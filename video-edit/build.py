"""Inline the proxy footage and stills into template.html -> preview.html (one self-contained file)."""
import base64
import pathlib

HERE = pathlib.Path(__file__).parent
ASSETS = {
    "A": ("assets/A.mp4", "video/mp4"),
    "B": ("assets/B.mp4", "video/mp4"),
    "C": ("assets/C.mp4", "video/mp4"),
    "D": ("assets/D.mp4", "video/mp4"),
    "E": ("assets/E.mp4", "video/mp4"),
    "F": ("assets/F.mp4", "video/mp4"),
    "G": ("assets/G.mp4", "video/mp4"),
    "BASIC": ("assets/basic.webp", "image/webp"),
    "ADV": ("assets/adv.webp", "image/webp"),
    "LOGO": ("assets/logo_alpha.png", "image/png"),
}

html = (HERE / "template.html").read_text()
for key, (path, mime) in ASSETS.items():
    data = base64.b64encode((HERE / path).read_bytes()).decode()
    html = html.replace("{{%s}}" % key, f"data:{mime};base64,{data}")
(HERE / "preview.html").write_text(html)
print(f"preview.html {len(html) / 1e6:.2f} MB")
