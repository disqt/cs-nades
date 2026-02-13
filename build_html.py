"""Generate a filterable static HTML page from scraped nade data."""

import argparse
import html
import json
from pathlib import Path

MAPS_ORDER = ["mirage", "dust2", "inferno", "overpass", "ancient", "anubis", "nuke"]

TECHNIQUE_LABELS = {
    "left": "Left Click",
    "right": "Right Click",
    "left_jump": "Jump Throw",
    "right_jump": "Right + Jump",
    "left_right": "Left + Right",
    "run_left": "Run + Left",
    "run_right": "Run + Right",
    "run_left_jump": "Run + Jump",
}


def _esc(s):
    """HTML-escape a string."""
    return html.escape(str(s)) if s else ""


def build_card_html(n):
    """Build a single nade card's HTML."""
    slug = _esc(n["slug"])
    map_name = _esc(n["map"])
    side = _esc(n["team"])
    title_to = _esc(n.get("titleTo", "?"))
    title_from = _esc(n.get("titleFrom", "?"))
    title = f"{title_to} from {title_from}"
    technique_raw = n.get("technique", "")
    technique = _esc(TECHNIQUE_LABELS.get(technique_raw, technique_raw))
    movement = n.get("movement", "")
    console_cmd = _esc(n.get("console", ""))
    captions = n.get("captions", [])
    source_url = _esc(n.get("source_url", "#"))

    # Frame paths relative to index.html
    frame_base = f"data/{n['map']}/{n['slug']}"

    side_label = "T" if n["team"] == "t" else "CT"
    movement_tag = ""
    if movement and movement != "stationary":
        movement_tag = f'<span class="tag">{_esc(movement)}</span>'

    caption_pos = _esc(captions[0]) if len(captions) > 0 else "Position"
    caption_aim = _esc(captions[1]) if len(captions) > 1 else "Aim"
    caption_throw = _esc(captions[2]) if len(captions) > 2 else "Throw"

    console_block = ""
    if console_cmd:
        console_block = f'<code class="console-cmd" title="Click to copy">{console_cmd}</code>'

    return f'''<div class="nade-card" data-map="{map_name}" data-side="{side}">
  <div class="card-header" onclick="toggleCard(this)">
    <img class="card-thumb" src="{frame_base}/lineup.webp" alt="{title}" loading="lazy"
         onerror="this.src='{frame_base}/aim.jpg'">
    <div class="card-info">
      <h3>{title}</h3>
      <span class="tag map-{map_name}">{map_name}</span>
      <span class="tag side-{side}">{side_label}</span>
      <span class="tag">{technique}</span>
      {movement_tag}
    </div>
    <span class="card-chevron">&#9660;</span>
  </div>
  <div class="card-detail" style="display:none">
    <div class="frames">
      <div class="frame">
        <img src="{frame_base}/position.jpg" alt="Position" loading="lazy">
        <p>{caption_pos}</p>
      </div>
      <div class="frame">
        <img src="{frame_base}/aim.jpg" alt="Aim" loading="lazy">
        <p>{caption_aim}</p>
      </div>
      <div class="frame">
        <img src="{frame_base}/result.jpg" alt="Result" loading="lazy">
        <p>Result</p>
      </div>
    </div>
    {console_block}
    <a class="source-link" href="{source_url}" target="_blank" rel="noopener">View on csnades.gg &#8599;</a>
  </div>
</div>'''


def build_html(data_dir, output_path):
    """Build the complete HTML page from nades.json."""
    data_dir = Path(data_dir)
    nades_file = data_dir / "nades.json"

    with open(nades_file, encoding="utf-8") as f:
        nades = json.load(f)

    # Sort by map order, then by destination, then by origin
    def sort_key(n):
        map_idx = MAPS_ORDER.index(n["map"]) if n["map"] in MAPS_ORDER else 99
        return (map_idx, n.get("titleTo", ""), n.get("titleFrom", ""))
    nades.sort(key=sort_key)

    # Collect unique values for filters
    maps_present = sorted(
        set(n["map"] for n in nades),
        key=lambda m: MAPS_ORDER.index(m) if m in MAPS_ORDER else 99,
    )
    sides = ["t", "ct"]

    # Build cards HTML
    cards_html = "\n".join(build_card_html(n) for n in nades)

    # Build filter buttons
    map_buttons = "\n".join(
        f'<button class="filter-btn" data-filter-map="{m}" '
        f"onclick=\"toggleFilter(this, 'map', '{m}')\">{m}</button>"
        for m in maps_present
    )
    side_buttons = "\n".join(
        f'<button class="filter-btn" data-filter-side="{s}" '
        f"onclick=\"toggleFilter(this, 'side', '{s}')\">"
        f'{"T" if s == "t" else "CT"}</button>'
        for s in sides
    )

    total = len(nades)

    page_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>CS2 Grenade Lineups</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; padding: 1.5rem; max-width: 1200px; margin: 0 auto; }}
h1 {{ font-size: 1.6rem; margin-bottom: 0.3rem; }}
.subtitle {{ color: #8b949e; margin-bottom: 1.5rem; font-size: 0.9rem; }}
.subtitle a {{ color: #58a6ff; text-decoration: none; }}
.subtitle a:hover {{ text-decoration: underline; }}
.filters {{ margin-bottom: 1rem; display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }}
.filter-label {{ color: #8b949e; font-size: 0.85rem; margin-right: 0.25rem; }}
.filter-btn {{ background: #21262d; border: 1px solid #30363d; color: #e6edf3; padding: 0.3rem 0.75rem; border-radius: 1rem; cursor: pointer; font-size: 0.8rem; transition: all 0.15s; }}
.filter-btn:hover {{ border-color: #58a6ff; }}
.filter-btn.active {{ background: #1f6feb; border-color: #1f6feb; }}
.filter-sep {{ width: 1px; height: 1.5rem; background: #30363d; margin: 0 0.25rem; }}
.count {{ color: #8b949e; font-size: 0.85rem; margin-bottom: 1rem; }}
.nade-card {{ background: #161b22; border: 1px solid #21262d; border-radius: 0.5rem; margin-bottom: 0.5rem; overflow: hidden; }}
.nade-card.hidden {{ display: none; }}
.card-header {{ display: flex; align-items: center; gap: 1rem; padding: 0.75rem; cursor: pointer; transition: background 0.15s; }}
.card-header:hover {{ background: #1c2128; }}
.card-thumb {{ width: 80px; height: 60px; object-fit: cover; border-radius: 0.25rem; flex-shrink: 0; }}
.card-info {{ flex: 1; }}
.card-info h3 {{ font-size: 0.95rem; margin-bottom: 0.3rem; }}
.tag {{ display: inline-block; font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 1rem; background: #21262d; color: #8b949e; margin-right: 0.25rem; text-transform: capitalize; }}
.side-t {{ background: #3d1f00; color: #f0883e; }}
.side-ct {{ background: #0c2d6b; color: #58a6ff; }}
.card-chevron {{ color: #484f58; font-size: 0.75rem; transition: transform 0.2s; flex-shrink: 0; }}
.card-header.expanded .card-chevron {{ transform: rotate(180deg); }}
.card-detail {{ padding: 1rem; border-top: 1px solid #21262d; }}
.frames {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin-bottom: 0.75rem; }}
.frame img {{ width: 100%; border-radius: 0.25rem; cursor: pointer; }}
.frame img:hover {{ opacity: 0.85; }}
.frame p {{ font-size: 0.8rem; color: #8b949e; margin-top: 0.25rem; text-align: center; }}
.console-cmd {{ display: block; background: #0d1117; border: 1px solid #21262d; padding: 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; color: #8b949e; word-break: break-all; margin-bottom: 0.5rem; cursor: pointer; }}
.console-cmd:hover {{ color: #e6edf3; }}
.source-link {{ font-size: 0.8rem; color: #58a6ff; text-decoration: none; }}
.source-link:hover {{ text-decoration: underline; }}
.back-link {{ display: inline-block; margin-bottom: 1rem; color: #58a6ff; text-decoration: none; font-size: 0.85rem; }}
.back-link:hover {{ text-decoration: underline; }}
@media (max-width: 600px) {{
  .frames {{ grid-template-columns: 1fr; }}
  .card-thumb {{ width: 60px; height: 45px; }}
}}
</style>
</head>
<body>

<a class="back-link" href="/cs/">&larr; Back to notes</a>
<h1>CS2 Grenade Lineups</h1>
<p class="subtitle">Recommended lineups scraped from <a href="https://csnades.gg">csnades.gg</a></p>

<div class="filters">
  <span class="filter-label">Map:</span>
  {map_buttons}
  <div class="filter-sep"></div>
  <span class="filter-label">Side:</span>
  {side_buttons}
</div>

<p class="count"><span id="visible-count">{total}</span> / {total} lineups</p>

<div id="cards">
{cards_html}
</div>

<script>
const activeFilters = {{ map: new Set(), side: new Set() }};

function toggleFilter(btn, type, value) {{
  btn.classList.toggle("active");
  if (activeFilters[type].has(value)) {{
    activeFilters[type].delete(value);
  }} else {{
    activeFilters[type].add(value);
  }}
  applyFilters();
}}

function applyFilters() {{
  let visible = 0;
  document.querySelectorAll(".nade-card").forEach(card => {{
    const mapMatch = activeFilters.map.size === 0 || activeFilters.map.has(card.dataset.map);
    const sideMatch = activeFilters.side.size === 0 || activeFilters.side.has(card.dataset.side);
    const show = mapMatch && sideMatch;
    card.classList.toggle("hidden", !show);
    if (show) visible++;
  }});
  document.getElementById("visible-count").textContent = visible;
}}

function toggleCard(header) {{
  const detail = header.nextElementSibling;
  const isHidden = detail.style.display === "none";
  detail.style.display = isHidden ? "block" : "none";
  header.classList.toggle("expanded", isHidden);
}}

document.querySelectorAll(".console-cmd").forEach(el => {{
  el.addEventListener("click", e => {{
    e.stopPropagation();
    navigator.clipboard.writeText(el.textContent).then(() => {{
      const orig = el.textContent;
      el.textContent = "Copied!";
      setTimeout(() => el.textContent = orig, 1500);
    }});
  }});
}});

document.querySelectorAll(".frame img").forEach(img => {{
  img.addEventListener("click", () => window.open(img.src, "_blank"));
}});
</script>
</body>
</html>'''

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"Generated {output_path} with {total} lineups")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build HTML page from scraped nades")
    parser.add_argument("--data", default="data", help="Data directory with nades.json")
    parser.add_argument("--out", default="index.html", help="Output HTML file path")
    args = parser.parse_args()
    build_html(args.data, args.out)
