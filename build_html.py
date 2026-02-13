"""Generate a filterable static HTML page from scraped nade data."""

import argparse
import html
import json
import random
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


def build_card_html(n, idx):
    """Build a single nade grid card."""
    slug = _esc(n["slug"])
    map_name = _esc(n["map"])
    side = _esc(n["team"])
    title_to = _esc(n.get("titleTo", "?"))
    title_from = _esc(n.get("titleFrom", "?"))
    title = f"{title_to} from {title_from}"
    technique_raw = n.get("technique", "")
    technique = _esc(TECHNIQUE_LABELS.get(technique_raw, technique_raw))
    side_label = "T" if n["team"] == "t" else "CT"

    frame_base = f"data/{n['map']}/{n['slug']}"

    return f'''<div class="nade-card" data-map="{map_name}" data-side="{side}" data-idx="{idx}" onclick="openModal({idx})">
  <img class="card-img" src="{frame_base}/result.jpg" alt="{title}" loading="lazy">
  <div class="card-overlay">
    <span class="tag map-{map_name}">{map_name}</span>
    <span class="tag side-{side}">{side_label}</span>
  </div>
  <div class="card-label">
    <span class="card-title">{title}</span>
    <span class="card-tech">{technique}</span>
  </div>
</div>'''


def build_modal_data(nades):
    """Build JSON data for the modal, to be embedded in a <script> tag."""
    items = []
    for n in nades:
        frame_base = f"data/{n['map']}/{n['slug']}"
        captions = n.get("captions", [])
        items.append({
            "title": f"{n.get('titleTo', '?')} from {n.get('titleFrom', '?')}",
            "map": n["map"],
            "side": "T" if n["team"] == "t" else "CT",
            "technique": TECHNIQUE_LABELS.get(n.get("technique", ""), n.get("technique", "")),
            "movement": n.get("movement", ""),
            "console": n.get("console", ""),
            "source": n.get("source_url", "#"),
            "position": f"{frame_base}/position.jpg",
            "aim": f"{frame_base}/aim.jpg",
            "result": f"{frame_base}/result.jpg",
            "lineup": f"{frame_base}/lineup.webp",
            "capPos": captions[0] if len(captions) > 0 else "Position",
            "capAim": captions[1] if len(captions) > 1 else "Aim",
            "capThrow": captions[2] if len(captions) > 2 else "Throw",
        })
    return json.dumps(items)


def build_html(data_dir, output_path):
    """Build the complete HTML page from nades.json."""
    data_dir = Path(data_dir)
    nades_file = data_dir / "nades.json"

    with open(nades_file, encoding="utf-8") as f:
        nades = json.load(f)

    # Shuffle once deterministically (seeded by count so it's stable until new nades added)
    random.seed(len(nades))
    random.shuffle(nades)

    maps_present = sorted(
        set(n["map"] for n in nades),
        key=lambda m: MAPS_ORDER.index(m) if m in MAPS_ORDER else 99,
    )

    cards_html = "\n".join(build_card_html(n, i) for i, n in enumerate(nades))
    modal_data = build_modal_data(nades)

    map_buttons = "\n".join(
        f'<button class="filter-btn" data-filter-map="{m}" '
        f"onclick=\"toggleFilter(this, 'map', '{m}')\">{m}</button>"
        for m in maps_present
    )
    side_buttons = "\n".join(
        f'<button class="filter-btn" data-filter-side="{s}" '
        f"onclick=\"toggleFilter(this, 'side', '{s}')\">"
        f'{"T" if s == "t" else "CT"}</button>'
        for s in ["t", "ct"]
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
body {{ background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; padding: 1rem 1.25rem 3rem; max-width: 1400px; margin: 0 auto; }}
h1 {{ font-size: 1.5rem; margin-bottom: 0.2rem; }}
.subtitle {{ color: #8b949e; margin-bottom: 1.25rem; font-size: 0.85rem; }}
.subtitle a {{ color: #58a6ff; text-decoration: none; }}
.filters {{ margin-bottom: 1rem; display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; }}
.filter-label {{ color: #8b949e; font-size: 0.8rem; margin-right: 0.2rem; }}
.filter-btn {{ background: #21262d; border: 1px solid #30363d; color: #e6edf3; padding: 0.25rem 0.65rem; border-radius: 1rem; cursor: pointer; font-size: 0.75rem; transition: all 0.15s; text-transform: capitalize; }}
.filter-btn:hover {{ border-color: #58a6ff; }}
.filter-btn.active {{ background: #1f6feb; border-color: #1f6feb; }}
.filter-sep {{ width: 1px; height: 1.4rem; background: #30363d; margin: 0 0.2rem; }}
.count {{ color: #8b949e; font-size: 0.8rem; margin-bottom: 1rem; }}
.back-link {{ display: inline-block; margin-bottom: 0.75rem; color: #58a6ff; text-decoration: none; font-size: 0.8rem; }}

/* Grid */
.grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; }}
@media (max-width: 1100px) {{ .grid {{ grid-template-columns: repeat(3, 1fr); }} }}
@media (max-width: 750px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} }}
@media (max-width: 440px) {{ .grid {{ grid-template-columns: 1fr; }} }}

/* Card */
.nade-card {{ background: #161b22; border: 1px solid #21262d; border-radius: 0.5rem; overflow: hidden; cursor: pointer; transition: border-color 0.15s, transform 0.15s; position: relative; }}
.nade-card:hover {{ border-color: #30363d; transform: translateY(-2px); }}
.nade-card.hidden {{ display: none; }}
.card-img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }}
.card-overlay {{ position: absolute; top: 0.4rem; left: 0.4rem; display: flex; gap: 0.25rem; }}
.card-label {{ padding: 0.5rem 0.6rem; }}
.card-title {{ display: block; font-size: 0.8rem; font-weight: 600; line-height: 1.3; color: #f0f6fc; }}
.card-tech {{ font-size: 0.7rem; color: #8b949e; }}
.tag {{ display: inline-block; font-size: 0.65rem; padding: 0.1rem 0.4rem; border-radius: 0.75rem; background: rgba(33,38,45,0.85); color: #8b949e; backdrop-filter: blur(4px); text-transform: capitalize; }}
.side-t {{ background: rgba(61,31,0,0.85); color: #f0883e; }}
.side-ct {{ background: rgba(12,45,107,0.85); color: #58a6ff; }}

/* Modal */
.modal-bg {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 100; align-items: center; justify-content: center; padding: 1rem; }}
.modal-bg.open {{ display: flex; }}
.modal {{ background: #161b22; border: 1px solid #30363d; border-radius: 0.75rem; max-width: 1300px; width: 100%; max-height: 95vh; overflow-y: auto; position: relative; }}
.modal-close {{ position: absolute; top: 0.75rem; right: 0.75rem; background: none; border: none; color: #8b949e; font-size: 1.5rem; cursor: pointer; z-index: 2; line-height: 1; padding: 0.25rem; }}
.modal-close:hover {{ color: #e6edf3; }}
.modal-head {{ padding: 1.25rem 1.25rem 0.75rem; }}
.modal-head h2 {{ font-size: 1.15rem; margin-bottom: 0.4rem; }}
.modal-tags {{ display: flex; gap: 0.3rem; flex-wrap: wrap; }}
.modal-tags .tag {{ font-size: 0.7rem; padding: 0.15rem 0.5rem; }}
.modal-frames {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; padding: 0 1.25rem; }}
.modal-frame img {{ width: 100%; border-radius: 0.35rem; cursor: pointer; }}
.modal-frame img:hover {{ opacity: 0.85; }}
.modal-frame p {{ font-size: 0.75rem; color: #8b949e; margin-top: 0.3rem; text-align: center; line-height: 1.3; }}
.modal-foot {{ padding: 0.75rem 1.25rem 1.25rem; display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; justify-content: space-between; }}
.console-cmd {{ display: block; flex: 1; min-width: 0; background: #0d1117; border: 1px solid #21262d; padding: 0.4rem 0.6rem; border-radius: 0.25rem; font-size: 0.7rem; color: #8b949e; word-break: break-all; cursor: pointer; font-family: monospace; }}
.console-cmd:hover {{ color: #e6edf3; border-color: #58a6ff; }}
.source-link {{ font-size: 0.75rem; color: #58a6ff; text-decoration: none; white-space: nowrap; }}
@media (max-width: 600px) {{
  .modal-frames {{ grid-template-columns: 1fr; }}
  .modal {{ border-radius: 0; max-height: 100vh; }}
}}
</style>
</head>
<body>

<a class="back-link" href="/cs/">&larr; Back to notes</a>
<h1>CS2 Grenade Lineups</h1>
<p class="subtitle">Recommended lineups from <a href="https://csnades.gg">csnades.gg</a></p>

<div class="filters">
  <span class="filter-label">Map:</span>
  {map_buttons}
  <div class="filter-sep"></div>
  <span class="filter-label">Side:</span>
  {side_buttons}
</div>

<p class="count"><span id="visible-count">{total}</span> / {total} lineups</p>

<div class="grid" id="cards">
{cards_html}
</div>

<div class="modal-bg" id="modal-bg" onclick="closeModal(event)">
  <div class="modal" id="modal">
    <button class="modal-close" onclick="closeModal()">&times;</button>
    <div class="modal-head">
      <h2 id="m-title"></h2>
      <div class="modal-tags" id="m-tags"></div>
    </div>
    <div class="modal-frames">
      <div class="modal-frame"><img id="m-pos" alt="Position" onclick="window.open(this.src,'_blank')"><p id="m-cap-pos"></p></div>
      <div class="modal-frame"><img id="m-aim" alt="Aim" onclick="window.open(this.src,'_blank')"><p id="m-cap-aim"></p></div>
      <div class="modal-frame"><img id="m-res" alt="Result" onclick="window.open(this.src,'_blank')"><p id="m-cap-res"></p></div>
    </div>
    <div class="modal-foot">
      <code class="console-cmd" id="m-console" title="Click to copy" onclick="copyCmd(event)"></code>
      <a class="source-link" id="m-source" target="_blank" rel="noopener">csnades.gg &#8599;</a>
    </div>
  </div>
</div>

<script>
const nades = {modal_data};
const activeFilters = {{ map: new Set(), side: new Set() }};

function toggleFilter(btn, type, value) {{
  btn.classList.toggle("active");
  activeFilters[type].has(value) ? activeFilters[type].delete(value) : activeFilters[type].add(value);
  applyFilters();
}}

function applyFilters() {{
  let v = 0;
  document.querySelectorAll(".nade-card").forEach(c => {{
    const show = (activeFilters.map.size === 0 || activeFilters.map.has(c.dataset.map))
              && (activeFilters.side.size === 0 || activeFilters.side.has(c.dataset.side));
    c.classList.toggle("hidden", !show);
    if (show) v++;
  }});
  document.getElementById("visible-count").textContent = v;
}}

function openModal(idx) {{
  const n = nades[idx];
  document.getElementById("m-title").textContent = n.title;
  const tags = document.getElementById("m-tags");
  const mv = n.movement && n.movement !== "stationary" ? `<span class="tag">${{n.movement}}</span>` : "";
  tags.innerHTML = `<span class="tag map-${{n.map}}">${{n.map}}</span><span class="tag side-${{n.side === "T" ? "t" : "ct"}}">${{n.side}}</span><span class="tag">${{n.technique}}</span>${{mv}}`;
  document.getElementById("m-pos").src = n.position;
  document.getElementById("m-aim").src = n.aim;
  document.getElementById("m-res").src = n.result;
  document.getElementById("m-cap-pos").textContent = n.capPos;
  document.getElementById("m-cap-aim").textContent = n.capAim;
  document.getElementById("m-cap-res").textContent = "Result";
  const cmd = document.getElementById("m-console");
  cmd.textContent = n.console || "";
  cmd.style.display = n.console ? "" : "none";
  const src = document.getElementById("m-source");
  src.href = n.source;
  document.getElementById("modal-bg").classList.add("open");
  document.body.style.overflow = "hidden";
}}

function closeModal(e) {{
  if (e && e.target !== document.getElementById("modal-bg")) return;
  document.getElementById("modal-bg").classList.remove("open");
  document.body.style.overflow = "";
}}

function copyCmd(e) {{
  e.stopPropagation();
  const el = e.currentTarget;
  navigator.clipboard.writeText(el.textContent).then(() => {{
    const orig = el.textContent;
    el.textContent = "Copied!";
    setTimeout(() => el.textContent = orig, 1500);
  }});
}}

document.addEventListener("keydown", e => {{ if (e.key === "Escape") closeModal(); }});
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
