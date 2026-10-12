"""Build preview.html: inline the stills and VO timeline; footage and VO audio stay in media/ next to the page."""
import base64
import json
import pathlib

HERE = pathlib.Path(__file__).parent
STILLS = {
    "BASIC": ("assets/basic.webp", "image/webp"),
    "ADV": ("assets/adv.webp", "image/webp"),
    "LOGO": ("assets/logo_alpha.png", "image/png"),
}

html = (HERE / "template.html").read_text()
for key, (path, mime) in STILLS.items():
    data = base64.b64encode((HERE / path).read_bytes()).decode()
    html = html.replace("{{%s}}" % key, f"data:{mime};base64,{data}")
html = html.replace("{{VO_TL}}", json.dumps(json.loads((HERE / "vo/timeline.json").read_text())))
(HERE / "preview.html").write_text(html)
print(f"preview.html {len(html) / 1e6:.2f} MB")
