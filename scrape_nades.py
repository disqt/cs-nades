import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import unquote


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
    import requests
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


def extract_lineup_frames(video_url, vtt_cues, output_dir):
    """Download video, extract position/aim/result frames based on VTT cues.

    Frame selection:
    - position: midpoint of first caption (usually "Stand at X")
    - aim: midpoint of second caption (usually "Aim at Y")
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

        # Position frame: midpoint of first cue
        pos_ts = (vtt_cues[0][0] + vtt_cues[0][1]) / 2
        print(f"  Position frame at {pos_ts:.2f}s ({vtt_cues[0][2]})")
        extract_frame(tmp_video, pos_ts, output_dir / "position.jpg")

        # Aim frame: midpoint of second cue
        aim_ts = (vtt_cues[1][0] + vtt_cues[1][1]) / 2
        print(f"  Aim frame at {aim_ts:.2f}s ({vtt_cues[1][2]})")
        extract_frame(tmp_video, aim_ts, output_dir / "aim.jpg")

        # Result frame: 2s after last cue ends
        result_ts = vtt_cues[-1][1] + 2.0
        print(f"  Result frame at {result_ts:.2f}s (after last cue)")
        extract_frame(tmp_video, result_ts, output_dir / "result.jpg")

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
