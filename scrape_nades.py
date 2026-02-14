import argparse
import json
import os
import re
import subprocess
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote

import requests

ACTIVE_DUTY_MAPS = ["mirage", "dust2", "inferno", "overpass", "ancient", "anubis", "nuke"]
BASE_URL = "https://csnades.gg"
REQUEST_DELAY = 1.0  # seconds between requests


def parse_vtt(vtt_str):
    """Parse a WebVTT string (possibly escaped) into (start_s, end_s, text) tuples."""
    if not vtt_str:
        return []

    # Unescape if needed (RSC payload uses \\n for newlines)
    text = vtt_str.replace("\\n", "\n").replace("\\\\", "\\")

    cues = []
    # Match: timestamp line followed by text line
    pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\n(.+?)(?:\n\n|\n?$)'
    for m in re.finditer(pattern, text, re.DOTALL):
        start = _ts_to_seconds(m.group(1))
        end = _ts_to_seconds(m.group(2))
        caption = re.sub(r'<[^>]+>', '', m.group(3)).strip()
        cues.append((start, end, caption))
    return cues


def _ts_to_seconds(ts):
    """Convert HH:MM:SS.mmm to float seconds."""
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def _tooltip(html, tooltip_id):
    """Extract data-tooltip-content value for a given tooltip ID."""
    m = re.search(
        rf'data-tooltip-id="{re.escape(tooltip_id)}"[^>]*data-tooltip-content="([^"]*)"',
        html,
    )
    return m.group(1) if m else None


def extract_nade_from_html(html):
    """Extract nade data from a csnades.gg detail page."""
    # Slug + map + type from canonical URL
    canon = re.search(r'<link[^>]+rel="canonical"[^>]+href="https://csnades\.gg/([^/]+)/([^/]+)/([^"]+)"', html)
    if not canon:
        return None
    map_name = canon.group(1)
    nade_type = canon.group(2).rstrip("s")  # "smokes" -> "smoke"
    slug = canon.group(3)

    # Asset ID from video poster (first poster on page = primary nade)
    asset_match = re.search(r'poster="https://assets\.csnades\.gg/nades/([^/]+)/thumbnail', html)
    asset_id = asset_match.group(1) if asset_match else None

    # VTT from URL-encoded <track> element
    vtt_match = re.search(r'src="data:text/vtt;charset=utf-8,([^"]+)"', html)
    vtt_raw = unquote(vtt_match.group(1)) if vtt_match else ""
    vtt_cues = parse_vtt(vtt_raw)

    # Title parsing: "{Map} {TitleTo} from {TitleFrom} {Type} - CSNADES.gg..."
    title_match = re.search(r'<title>(\w+)\s+(.+?)\s+from\s+(.+?)\s+\w+\s*-\s*CSNADES', html)
    title_to = title_match.group(2) if title_match else None
    title_from = title_match.group(3) if title_match else None

    # HTML attribute tooltips
    team = _tooltip(html, "metadata-team")
    technique = _tooltip(html, "metadata-technique")
    movement = _tooltip(html, "metadata-movement")
    console_cmd = _tooltip(html, "copy-console")

    return {
        "slug": slug,
        "map": map_name,
        "team": team,
        "type": nade_type,
        "titleFrom": title_from,
        "titleTo": title_to,
        "technique": technique,
        "movement": movement,
        "console": console_cmd,
        "asset_id": asset_id,
        "vtt_cues": vtt_cues,
        "video_url": f"https://assets.csnades.gg/nades/{asset_id}/hq.mp4" if asset_id else None,
        "lineup_url": f"https://assets.csnades.gg/nades/{asset_id}/lineup.webp" if asset_id else None,
        "source_url": f"https://csnades.gg/{map_name}/{nade_type}s/{slug}",
    }


def download_file(url, dest_path):
    """Download a file from URL to dest_path."""
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


def extract_frame(video_path, timestamp_s, output_path):
    """Extract a single frame at timestamp_s from video."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{timestamp_s:.3f}",
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def generate_thumbnail(input_path, width=400):
    """Generate a thumbnail version of an image using ffmpeg.

    Creates a scaled-down copy with '_thumb' suffix (e.g. result_thumb.jpg).
    """
    p = Path(input_path)
    thumb_path = p.parent / (p.stem + "_thumb" + p.suffix)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", f"scale={width}:-1",
        "-q:v", "4",
        str(thumb_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return str(thumb_path)


def extract_result_clip(video_path, start_s, output_dir, duration=6.0):
    """Extract a short clip starting at start_s.

    Generates both full-res and thumbnail (400px) versions.
    """
    output_dir = Path(output_dir)
    start = max(0, start_s)

    # Full resolution clip
    full_clip = output_dir / "result.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}", "-i", str(video_path),
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an", "-movflags", "+faststart",
        str(full_clip),
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    # Thumbnail clip (400px wide)
    thumb_clip = output_dir / "result_thumb.mp4"
    cmd_thumb = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}", "-i", str(video_path),
        "-t", f"{duration:.3f}",
        "-vf", "scale=400:-2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-an", "-movflags", "+faststart",
        str(thumb_clip),
    ]
    subprocess.run(cmd_thumb, capture_output=True, check=True)


def extract_lineup_frames(video_url, vtt_cues, output_dir):
    """Download video, extract position/aim/result frames based on VTT cues.

    Frame selection:
    - position: 2/3 into first caption (usually "Stand at X")
    - aim: 2/3 into second caption (usually "Aim at Y")
    - result: 2 seconds after last caption ends (smoke has landed)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if len(vtt_cues) < 2:
        print(f"  WARNING: Only {len(vtt_cues)} VTT cues, need at least 2")
        return False

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_video = tmp.name

    try:
        print(f"  Downloading video...")
        download_file(video_url, tmp_video)

        # Position frame: 2/3 into first cue
        pos_ts = vtt_cues[0][0] + (vtt_cues[0][1] - vtt_cues[0][0]) * 2 / 3
        print(f"  Position frame at {pos_ts:.2f}s ({vtt_cues[0][2]})")
        extract_frame(tmp_video, pos_ts, output_dir / "position.jpg")
        generate_thumbnail(output_dir / "position.jpg")

        # Aim frame: 2/3 into second cue
        aim_ts = vtt_cues[1][0] + (vtt_cues[1][1] - vtt_cues[1][0]) * 2 / 3
        print(f"  Aim frame at {aim_ts:.2f}s ({vtt_cues[1][2]})")
        extract_frame(tmp_video, aim_ts, output_dir / "aim.jpg")
        generate_thumbnail(output_dir / "aim.jpg")

        # Result frame: 2s after last cue ends
        result_ts = vtt_cues[-1][1] + 2.0
        print(f"  Result frame at {result_ts:.2f}s (after last cue)")
        extract_frame(tmp_video, result_ts, output_dir / "result.jpg")
        generate_thumbnail(output_dir / "result.jpg")

        # Result video clip: 3s clip ending ~1s after result frame
        clip_start = max(0, result_ts - 2.0)
        clip_duration = 3.0
        print(f"  Result clip from {clip_start:.2f}s ({clip_duration:.1f}s)")
        extract_result_clip(tmp_video, clip_start, output_dir, duration=clip_duration)

        return True
    finally:
        os.unlink(tmp_video)


def extract_recommended_slugs(html, map_name):
    """Extract all nade slugs from a csnades.gg list page.

    The list page embeds nade data in Next.js RSC payload chunks as escaped JSON.
    Each nade object has an id like "nade_<hex>" followed by a "slug" field.
    We match this pattern to filter out non-nade slugs (map names, nav items).

    Args:
        html: Full HTML of the list page (e.g. https://csnades.gg/mirage?recommended=true)
        map_name: Map name (e.g. "mirage") -- reserved for future filtering.

    Returns:
        List of slug strings (e.g. ["ticket-booth-from-tetris", "top-mid-from-t-spawn", ...])
    """
    # RSC payload contains escaped JSON: \"id\":\"nade_xxx\",\"slug\":\"slug-name\"
    # In the HTML file, \" is a literal backslash + quote (two chars).
    # The regex matches this escaped pattern to extract only nade slugs.
    slugs = re.findall(
        r'\\"id\\":\\"nade_[a-f0-9]+\\",\\"slug\\":\\"([a-z0-9-]+)\\"',
        html,
    )
    # Deduplicate while preserving order (RSC data may repeat chunks)
    seen = set()
    unique = []
    for s in slugs:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


def extract_beginner_smoke_slugs(html):
    """Extract slugs of beginner-recommended smoke nades from list page.

    The RSC payload contains all nades for the map regardless of URL filters.
    Each nade object has slug, type, and beginner fields. We extract all three
    and filter to only beginner smokes.
    """
    # Match: \"slug\":\"xxx\"...\"beginner\":true/false within each nade chunk
    pairs = re.findall(
        r'\\"slug\\":\\"([a-z0-9-]+)\\".*?\\"beginner\\":(true|false)',
        html,
    )
    seen = set()
    slugs = []
    for slug, beginner in pairs:
        if beginner == "true" and slug not in seen and slug not in ACTIVE_DUTY_MAPS:
            seen.add(slug)
            slugs.append(slug)
    return slugs


MIN_NADES_PER_MAP = 8


def get_slugs_for_map_with_fallback(beginner_slugs, all_recommended_slugs, min_count=MIN_NADES_PER_MAP):
    """Use beginner slugs, but fill with non-beginner recommended if below threshold."""
    if len(beginner_slugs) >= min_count:
        return beginner_slugs

    result = list(beginner_slugs)
    seen = set(beginner_slugs)
    for slug in all_recommended_slugs:
        if slug not in seen:
            result.append(slug)
            seen.add(slug)
        if len(result) >= min_count:
            break
    return result


def scrape_map(map_name, output_dir, existing_slugs=None):
    """Scrape all beginner-recommended smokes for a map."""
    existing_slugs = existing_slugs or set()
    output_dir = Path(output_dir)

    print(f"\n{'='*60}")
    print(f"Scraping {map_name} (beginner-recommended smokes)")

    list_url = f"{BASE_URL}/{map_name}?recommended=true"
    print(f"  Fetching {list_url}")
    resp = requests.get(list_url, timeout=30)
    resp.raise_for_status()

    beginner_slugs = extract_beginner_smoke_slugs(resp.text)
    all_recommended = extract_recommended_slugs(resp.text, map_name)
    smoke_slugs = get_slugs_for_map_with_fallback(beginner_slugs, all_recommended)

    if len(beginner_slugs) < len(smoke_slugs):
        print(f"  Found {len(beginner_slugs)} beginner smokes, filled to {len(smoke_slugs)} with recommended")
    else:
        print(f"  Found {len(smoke_slugs)} beginner-recommended smokes")

    nades = []
    for i, slug in enumerate(smoke_slugs):
        if slug in existing_slugs:
            print(f"  [{i+1}/{len(smoke_slugs)}] {slug} -- already scraped, skipping")
            continue

        print(f"  [{i+1}/{len(smoke_slugs)}] {slug}")
        time.sleep(REQUEST_DELAY)

        detail_url = f"{BASE_URL}/{map_name}/smokes/{slug}"
        try:
            resp = requests.get(detail_url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"    ERROR fetching detail page: {e}")
            continue

        nade = extract_nade_from_html(resp.text)
        if not nade or not nade.get("vtt_cues"):
            print(f"    ERROR: could not extract nade data or VTT cues")
            continue

        # Extract frames
        nade_dir = output_dir / map_name / slug
        if nade.get("video_url"):
            try:
                ok = extract_lineup_frames(nade["video_url"], nade["vtt_cues"], nade_dir)
                if not ok:
                    print(f"    WARNING: frame extraction incomplete")
            except Exception as e:
                print(f"    ERROR extracting frames: {e}")
                continue

        # Download lineup diagram
        if nade.get("lineup_url"):
            nade_dir.mkdir(parents=True, exist_ok=True)
            try:
                download_file(nade["lineup_url"], nade_dir / "lineup.webp")
            except Exception as e:
                print(f"    WARNING: could not download lineup diagram: {e}")

        # Remove non-serializable fields, add frame paths
        nade_data = {k: v for k, v in nade.items() if k != "vtt_cues"}
        nade_data["captions"] = [text for _, _, text in nade["vtt_cues"]]
        nades.append(nade_data)

    return nades


def _scrape_map_worker(args):
    """Worker function for parallel map scraping."""
    map_name, output_dir, existing_slugs = args
    return scrape_map(map_name, output_dir, existing_slugs)


def scrape_all(output_dir, maps=None):
    """Scrape all maps in parallel. Incremental: skips already-scraped nades."""
    output_dir = Path(output_dir)
    maps = maps or ACTIVE_DUTY_MAPS

    nades_file = output_dir / "nades.json"
    existing = []
    if nades_file.exists():
        with open(nades_file) as f:
            existing = json.load(f)
    existing_slugs = {n["slug"] for n in existing}
    print(f"Existing nades: {len(existing_slugs)}")

    all_nades = list(existing)

    # Scrape maps in parallel (one worker per map)
    worker_args = [(map_name, output_dir, existing_slugs) for map_name in maps]
    with ProcessPoolExecutor(max_workers=len(maps)) as executor:
        futures = {
            executor.submit(_scrape_map_worker, args): args[0]
            for args in worker_args
        }
        for future in as_completed(futures):
            map_name = futures[future]
            try:
                new_nades = future.result()
                all_nades.extend(new_nades)
            except Exception as e:
                print(f"\nERROR scraping {map_name}: {e}")

    with open(nades_file, "w") as f:
        json.dump(all_nades, f, indent=2)
    print(f"\nTotal nades: {len(all_nades)} (saved to {nades_file})")
    return all_nades


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape recommended nades from csnades.gg")
    parser.add_argument("--maps", nargs="*", default=None,
                        help="Maps to scrape (default: all active duty)")
    parser.add_argument("--outdir", default="data",
                        help="Output directory (default: data)")
    args = parser.parse_args()
    scrape_all(args.outdir, args.maps)
