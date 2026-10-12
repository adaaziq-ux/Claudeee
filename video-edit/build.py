"""Build preview.html and the VO tracks.

Timing lives in edl.json (shot order + durations, VO line anchors). This script:
  1. mixes the per-line VO stems in vo/lines/ into one body track and one track per hook, per voice,
     placed at the times edl.json gives, then processes them for broadcast (EQ, compression, -16 LUFS);
  2. inlines the stills and the timing into template.html -> preview.html.
Footage and VO audio stay in media/ next to the page.
"""
import base64
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).parent
STILLS = {
    "BASIC": ("assets/basic.webp", "image/webp"),
    "ADV": ("assets/adv.webp", "image/webp"),
    "LOGO": ("assets/logo_alpha.png", "image/png"),
    "LOGIN": ("assets/login.webp", "image/webp"),
}
VO_CHAIN = ("highpass=f=70,equalizer=f=160:t=q:w=1:g=2.5,equalizer=f=3200:t=q:w=1.2:g=3,"
            "equalizer=f=9000:t=h:w=1:g=2,acompressor=threshold=-20dB:ratio=3.5:attack=4:release=90:makeup=2,"
            "aecho=0.8:0.5:28:0.08,loudnorm=I=-16:TP=-1.5:LRA=7")


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(path)]).decode())


def mix(stems, length, out):
    """stems: [(path, start_seconds)] -> processed mono mp3 of `length` seconds."""
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for path, _ in stems:
        cmd += ["-i", str(path)]
    parts = [f"[{i}]adelay={int(start * 1000)}:all=1[d{i}]" for i, (_, start) in enumerate(stems)]
    ins = "".join(f"[d{i}]" for i in range(len(stems)))
    graph = ";".join(parts) + f";{ins}amix=inputs={len(stems)}:normalize=0,apad,atrim=0:{length},{VO_CHAIN}"
    cmd += ["-filter_complex", graph, "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", str(out)]
    subprocess.run(cmd, check=True)


edl = json.loads((HERE / "edl.json").read_text())
t0, acc = {}, 0.0
for shot, dur in edl["shots"]:
    t0[shot] = round(acc, 3)
    acc += dur
total = acc
texts = {l["id"]: l["text"] for l in json.loads((HERE / "vo/lines.json").read_text())}

timeline = []
for lid, (shot, off) in edl["vo"].items():
    timeline.append({"id": lid, "start": round(t0[shot] + off, 3), "text": texts[lid],
                     "dur": round(duration(HERE / f"vo/lines/male_{lid}.flac"), 2),
                     "durF": round(duration(HERE / f"vo/lines/female_{lid}.flac"), 2)})

for voice in ("male", "female"):
    body = [(HERE / f"vo/lines/{voice}_{l['id']}.flac", l["start"]) for l in timeline if l["id"][0] == "b"]
    mix(body, total + 0.2, HERE / f"media/vo_{voice}_body.mp3")
    for k in "ABC":
        hook = [(HERE / f"vo/lines/{voice}_{l['id']}.flac", l["start"]) for l in timeline if l["id"][:2] == "h" + k]
        mix(hook, 4.5, HERE / f"media/vo_{voice}_hook{k}.mp3")

html = (HERE / "template.html").read_text()
for key, (path, mime) in STILLS.items():
    data = base64.b64encode((HERE / path).read_bytes()).decode()
    html = html.replace("{{%s}}" % key, f"data:{mime};base64,{data}")
html = html.replace("{{SEG_DUR}}", json.dumps(dict(edl["shots"])))
html = html.replace("{{VO_TL}}", json.dumps(timeline))
(HERE / "preview.html").write_text(html)
print(f"preview.html {len(html) / 1e6:.2f} MB, edit length {total:.1f}s")
