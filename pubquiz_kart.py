#!/usr/bin/env python3
"""
pubquiz_kart.py – Generer pubquiz-kart fra YAML-konfig

Bruk:
    python pubquiz_kart.py quizzes/peppes_oslo.yaml
    python pubquiz_kart.py quizzes/peppes_oslo.yaml --output output/mitt_kart.html
    python pubquiz_kart.py quizzes/peppes_oslo.yaml --fasit        # kun fasit
    python pubquiz_kart.py quizzes/peppes_oslo.yaml --begge        # quiz + fasit
"""

import sys
import json
import argparse
import base64
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Installerer PyYAML...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml", "-q"])
    import yaml


# ── HTML-MAL ──────────────────────────────────────────────────────────────────

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="no">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} – {mode_label}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Georgia', serif; background: #f5f0e8; }}
  .page {{
    width: 297mm; min-height: 210mm; margin: 0 auto;
    background: #faf8f3; display: flex; flex-direction: column;
  }}
  header {{
    padding: 14px 28px 10px; border-bottom: 2px solid #1a1a1a;
    display: flex; align-items: baseline; gap: 16px;
  }}
  header h1 {{
    font-size: 22px; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #1a1a1a;
  }}
  header p {{ font-size: 12px; color: #666; letter-spacing: 0.04em; }}
  .fasit-badge {{
    margin-left: auto; font-size: 11px; font-weight: bold;
    color: #fff; background: #c0392b; padding: 3px 10px;
    border-radius: 3px; letter-spacing: 0.08em; text-transform: uppercase;
  }}
  #map {{ flex: 1; min-height: 168mm; width: 100%; background: #e8e4db; }}
  footer {{
    padding: 8px 28px; border-top: 1px solid #ccc;
    display: flex; justify-content: space-between; align-items: center;
  }}
  footer .answer-line {{
    font-size: 11px; color: #555; letter-spacing: 0.06em; text-transform: uppercase;
  }}
  footer .answer-box {{
    border-bottom: 1px solid #1a1a1a; width: 260px; height: 18px; display: inline-block;
  }}
  @media print {{
    body {{ background: white; }}
    .page {{ width: 297mm; margin: 0; box-shadow: none; }}
    @page {{ size: A4 landscape; margin: 0; }}
  }}

  /* Landmark SVG icons */
  .lm-svg-wrap {{
    display: flex; flex-direction: column; align-items: center;
    white-space: nowrap; background: none; border: none;
  }}
  .lm-svg-wrap img {{
    width: {landmark_size}px; height: {landmark_size}px;
    filter: drop-shadow(0 1px 3px rgba(0,0,0,0.35));
  }}

  /* Landmark emoji icons */
  .lm-emoji-wrap {{
    display: flex; flex-direction: column; align-items: center;
    white-space: nowrap; background: none; border: none;
  }}
  .lm-emoji {{ font-size: 20px; line-height: 1; }}

  /* Plain dot landmark */
  .lm-dot-wrap {{
    display: flex; flex-direction: column; align-items: center;
    white-space: nowrap; background: none; border: none;
  }}
  .lm-dot {{
    width: 8px; height: 8px; background: #555; border-radius: 50%;
    border: 1.5px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.3); margin-bottom: 2px;
  }}

  /* Shared label style */
  .lm-label {{
    font-family: 'Georgia', serif; font-size: 10px; color: #333;
    letter-spacing: 0.03em; text-align: center; font-style: italic;
    text-shadow: 0 1px 3px #faf8f3, 0 -1px 3px #faf8f3,
                 1px 0 3px #faf8f3, -1px 0 3px #faf8f3;
  }}

  /* Fasit answer label on quiz markers */
  .answer-label-wrap {{
    display: flex; flex-direction: column; align-items: center;
    white-space: nowrap;
  }}
  .answer-dot {{
    width: {marker_diameter}px; height: {marker_diameter}px;
    background: {marker_color}; border-radius: 50%;
    border: 3px solid #fff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    margin-bottom: 3px;
  }}
  .answer-text {{
    font-family: 'Georgia', serif; font-size: 10px; font-weight: bold;
    color: #1a1a1a; letter-spacing: 0.03em; text-align: center;
    text-shadow: 0 1px 3px #faf8f3, 0 -1px 3px #faf8f3,
                 1px 0 3px #faf8f3, -1px 0 3px #faf8f3;
    max-width: 90px; line-height: 1.2;
  }}
</style>
</head>
<body>
<div class="page">
  <header>
    <h1>{title}</h1>
    <p>{header_text}</p>
    {fasit_badge}
  </header>
  <div id="map"></div>
  <footer>
    {footer_content}
    <span style="font-size:10px; color:#aaa; letter-spacing:0.04em;">PUBQUIZ</span>
  </footer>
</div>
<script>
  var map = L.map('map', {{ zoomControl: false, attributionControl: false }});
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/{tile_style}/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    maxZoom: 19
  }}).addTo(map);

  var locations = {locations_json};
  var bounds = L.latLngBounds();
  var isFasit = {is_fasit};

  locations.forEach(function(loc) {{
    if (isFasit && loc.answer) {{
      // Fasit: show dot + answer label
      var dotSize = {marker_diameter};
      var html = '<div class="answer-label-wrap">'
               + '<div class="answer-dot"></div>'
               + '<div class="answer-text">' + loc.answer + '</div>'
               + '</div>';
      var icon = L.divIcon({{
        className: '',
        html: html,
        iconSize: [96, 40],
        iconAnchor: [48, dotSize / 2 + 3]
      }});
      L.marker([loc.lat, loc.lng], {{ icon: icon }}).addTo(map);
    }} else {{
      var d = {marker_diameter};
      var dotHtml = '<div style="width:'+d+'px;height:'+d+'px;background:{marker_color};'
                  + 'border-radius:50%;border:3px solid {marker_border};'
                  + 'box-shadow:0 2px 8px rgba(0,0,0,0.5);"></div>';
      var dotIcon = L.divIcon({{
        className: '',
        html: dotHtml,
        iconSize: [d, d],
        iconAnchor: [d/2, d/2]
      }});
      L.marker([loc.lat, loc.lng], {{ icon: dotIcon, zIndexOffset: 1000 }}).addTo(map);
    }}
    bounds.extend([loc.lat, loc.lng]);
  }});

  map.fitBounds(bounds, {{ padding: [{fit_padding}, {fit_padding}] }});

  var landmarks = {landmarks_json};
  landmarks.forEach(function(lm) {{
    var html, anchorY;
    if (lm.svg_b64) {{
      var sz = {landmark_size};
      html = '<div class="lm-svg-wrap">'
           + '<img src="data:image/svg+xml;base64,' + lm.svg_b64 + '" />'
           + '<div class="lm-label">' + lm.label + '</div></div>';
      anchorY = sz;
    }} else if (lm.icon) {{
      html = '<div class="lm-emoji-wrap">'
           + '<span class="lm-emoji">' + lm.icon + '</span>'
           + '<div class="lm-label">' + lm.label + '</div></div>';
      anchorY = 24;
    }} else {{
      html = '<div class="lm-dot-wrap">'
           + '<div class="lm-dot"></div>'
           + '<div class="lm-label">' + lm.label + '</div></div>';
      anchorY = 10;
    }}
    var lIcon = L.divIcon({{
      className: '',
      html: html,
      iconSize: [100, 50],
      iconAnchor: [50, anchorY]
    }});
    L.marker([lm.lat, lm.lng], {{ icon: lIcon, interactive: false, zIndexOffset: -100 }})
      .addTo(map);
  }});
</script>
</body>
</html>
"""


# ── HJELPEFUNKSJONER ──────────────────────────────────────────────────────────

def load_svg_b64(svg_path: Path) -> str | None:
    """Les en SVG-fil og returner base64-kodet streng."""
    if svg_path and svg_path.exists():
        raw = svg_path.read_bytes()
        return base64.b64encode(raw).decode("ascii")
    return None


def build_map(config_path: Path, output_path: Path, fasit: bool = False,
              svg_dir: Path = None):
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    title         = cfg.get("title", "Oslo")
    question      = cfg.get("question", "Hva representerer markørene på kartet?")
    answer_label  = cfg.get("answer_label", "Svar")
    tile_style    = cfg.get("tile_style", "light_all")
    fit_padding   = cfg.get("fit_padding", 60)
    marker_color  = cfg.get("marker_color", "#c0392b")
    marker_border = cfg.get("marker_border", "#ffffff")
    marker_radius = int(cfg.get("marker_radius", 12))
    landmark_size = int(cfg.get("landmark_svg_size", 36))
    markers       = cfg.get("markers", [])
    landmarks     = cfg.get("landmarks", [])

    marker_diameter = marker_radius * 2

    # Resolve SVG dir: flag > config key > sibling 'svgs' folder > script dir
    if svg_dir is None:
        cfg_svg = cfg.get("svg_dir")
        if cfg_svg:
            svg_dir = config_path.parent / cfg_svg
        else:
            svg_dir = config_path.parent.parent / "svgs"

    # Build locations JSON
    locs = []
    for m in markers:
        entry = {"lat": m["lat"], "lng": m["lng"]}
        if fasit and "answer" in m:
            entry["answer"] = m["answer"]
        locs.append(entry)
    locations_json = json.dumps(locs, ensure_ascii=False, indent=4)

    # Build landmarks JSON (embed SVGs as base64)
    lm_list = []
    for lm in landmarks:
        entry = {
            "lat":   lm["lat"],
            "lng":   lm["lng"],
            "label": lm.get("label", ""),
            "icon":  lm.get("icon", ""),
            "svg_b64": "",
        }
        svg_file = lm.get("svg")
        if svg_file:
            svg_path = svg_dir / svg_file
            b64 = load_svg_b64(svg_path)
            if b64:
                entry["svg_b64"] = b64
            else:
                print(f"  ⚠️  SVG ikke funnet: {svg_path}")
        lm_list.append(entry)
    landmarks_json = json.dumps(lm_list, ensure_ascii=False, indent=4)

    # Mode-specific strings
    mode_label    = "Fasit" if fasit else "Pubquiz"
    header_text   = f"FASIT – {question}" if fasit else question
    fasit_badge   = '<span class="fasit-badge">Fasit</span>' if fasit else ""
    is_fasit      = "true" if fasit else "false"
    if fasit:
        footer_content = '<span style="font-size:11px;color:#c0392b;font-weight:bold;letter-spacing:0.06em;text-transform:uppercase;">FASIT – IKKE DEL MED DELTAKERE</span>'
    else:
        footer_content = f'<span class="answer-line">{answer_label}: <span class="answer-box"></span></span>'

    html = HTML_TEMPLATE.format(
        title           = title,
        mode_label      = mode_label,
        header_text     = header_text,
        fasit_badge     = fasit_badge,
        is_fasit        = is_fasit,
        question        = question,
        answer_label    = answer_label,
        tile_style      = tile_style,
        fit_padding     = fit_padding,
        marker_color    = marker_color,
        marker_border   = marker_border,
        marker_radius   = marker_radius,
        marker_diameter = marker_diameter,
        landmark_size   = landmark_size,
        locations_json  = locations_json,
        landmarks_json  = landmarks_json,
        footer_content  = footer_content,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    tag = "FASIT" if fasit else "QUIZ"
    print(f"  [{tag}] ✅  {output_path}  ({len(markers)} markører, {len(landmarks)} landemerker)")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generer pubquiz-kart (og fasit) fra YAML-konfig"
    )
    parser.add_argument("config", help="Sti til YAML-konfig")
    parser.add_argument("--output", "-o", help="Output HTML-fil (standard: output/<navn>.html)")
    parser.add_argument("--fasit",  action="store_true", help="Generer kun fasitversjon")
    parser.add_argument("--begge",  action="store_true", help="Generer både quiz og fasit")
    parser.add_argument("--svg-dir", help="Mappe med SVG-filer (overstyrer konfig og standard)")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌  Finner ikke konfig-filen: {config_path}")
        sys.exit(1)

    svg_dir = Path(args.svg_dir) if args.svg_dir else None
    stem    = config_path.stem
    out_dir = config_path.parent.parent / "output"

    if args.output:
        base_out = Path(args.output)
    else:
        base_out = out_dir / f"{stem}.html"

    print(f"\n📍  Bygger kart fra: {config_path.name}")

    if args.begge:
        quiz_out  = base_out.parent / f"{base_out.stem}.html"
        fasit_out = base_out.parent / f"{base_out.stem}_fasit.html"
        build_map(config_path, quiz_out,  fasit=False, svg_dir=svg_dir)
        build_map(config_path, fasit_out, fasit=True,  svg_dir=svg_dir)
    elif args.fasit:
        fasit_out = base_out.parent / f"{base_out.stem}_fasit.html"
        build_map(config_path, fasit_out, fasit=True, svg_dir=svg_dir)
    else:
        build_map(config_path, base_out, fasit=False, svg_dir=svg_dir)

    print("\nÅpne HTML-filen i nettleser → Ctrl+P for utskrift (A4 liggende)\n")


if __name__ == "__main__":
    main()
