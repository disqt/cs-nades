import re
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
