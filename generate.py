#!/usr/bin/env python3
"""Zet de standen-export van Voetbal Vlaanderen om naar een klassementspagina voor Jong Cercle.

Gebruik:
  python3 generate.py                 # downloadt de zip zelf
  python3 generate.py pad/naar.zip    # gebruikt een lokaal bestand
Schrijft: docs/index.html (en docs/stand.json)
"""
import csv, io, json, sys, urllib.request, zipfile, html, datetime, pathlib

# ---- Instellingen -----------------------------------------------------------
BRON_URL = "https://static.rbfa.be/project/publiek/download/vvlcltdownP.zip"
REEKS = "1"                      # Eerste Afdeling VV
EIGEN_PLOEG = "Cercle Brugge K.S.V. B"
TITEL = "Jong Cercle · 1ste afdeling VV"
UIT = pathlib.Path(__file__).parent / "docs"
# -----------------------------------------------------------------------------


def lees_zip(bron):
    if bron.startswith("http"):
        req = urllib.request.Request(bron, headers={"User-Agent": "Mozilla/5.0 (Cercle Brugge klassement)"})
        data = urllib.request.urlopen(req, timeout=60).read()
    else:
        data = pathlib.Path(bron).read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        naam = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        return z.read(naam).decode("latin-1")


def stand(csv_tekst):
    rijen = []
    for r in csv.DictReader(io.StringIO(csv_tekst), delimiter=";"):
        if r["DIV"].strip() != REEKS or r["PER"].strip() != "0":
            continue
        gp, gt = int(r["G+"]), int(r["G-"])
        rijen.append({
            "pos": int(r["POS"]), "ploeg": r["TEAM"].strip(),
            "m": int(r["M"]), "w": int(r["W"]), "v": int(r["L"]), "g": int(r["D"]),  # let op: L vóór D
            "dv": gp, "dt": gt, "ds": gp - gt, "ptn": int(r["PTS"]),
        })
    if not rijen:
        raise SystemExit(f"Reeks {REEKS} niet gevonden in de export — niets overschreven.")
    return sorted(rijen, key=lambda x: (x["pos"], -x["ds"]))


def render(rijen):
    def ds(x): return f"+{x}" if x > 0 else str(x)
    tr = []
    for r in rijen:
        eigen = r["ploeg"] == EIGEN_PLOEG
        naam = "Jong Cercle" if eigen else r["ploeg"]
        tr.append(f"""<tr{' class="eigen"' if eigen else ''}>
  <td class="pos">{r['pos']}</td><td class="ploeg">{html.escape(naam)}</td>
  <td>{r['m']}</td><td class="opt">{r['w']}</td><td class="opt">{r['v']}</td><td class="opt">{r['g']}</td>
  <td class="opt">{r['dv']}</td><td class="opt">{r['dt']}</td><td>{ds(r['ds'])}</td><td class="ptn">{r['ptn']}</td></tr>""")
    nu = datetime.datetime.now().strftime("%d/%m/%Y")
    return f"""<!doctype html>
<html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Klassement Jong Cercle</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Kanit:ital,wght@1,800&display=swap" rel="stylesheet">
<style>
:root{{--bg:#000;--alt:#1e1e1e;--tekst:#fff;--grijs:#b5b5b5;--lijn:#2a2a2a;--groen:#60B22C}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--tekst);font-family:Inter,system-ui,sans-serif;padding:16px}}
.wrap{{max-width:1450px;margin:0 auto;overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th{{font-weight:600;font-size:13px;color:var(--grijs);padding:18px 8px;border-bottom:1px solid var(--lijn);text-align:center}}
th.l,td.ploeg{{text-align:left}} th.ptn,td.ptn{{color:var(--tekst);font-weight:700}}
td{{padding:20px 8px;text-align:center;color:var(--grijs);font-variant-numeric:tabular-nums}}
tbody tr:nth-child(even){{background:var(--alt)}}
td.pos,td.ploeg{{font-family:Kanit,sans-serif;font-style:italic;font-weight:800;color:var(--tekst);text-transform:uppercase}}
td.pos{{font-size:22px;width:56px;text-align:right;padding-right:24px}}
td.ploeg{{font-size:18px;white-space:nowrap}}
tr.eigen td.pos,tr.eigen td.ploeg,tr.eigen td.ptn{{color:var(--groen)}}
tr.eigen{{box-shadow:inset 4px 0 0 var(--groen)}}
.voet{{color:var(--grijs);font-size:12px;margin-top:12px;text-align:right}}
@media (max-width:640px){{td.opt,th.opt{{display:none}} td{{padding:14px 5px}} td.ploeg{{font-size:15px;white-space:normal}} td.pos{{font-size:18px;padding-right:12px;width:36px}}}}
</style></head><body><div class="wrap">
<table><thead><tr><th>#</th><th class="l">Ploeg</th><th>M</th><th class="opt">M+</th><th class="opt">M-</th><th class="opt">M=</th><th class="opt">D+</th><th class="opt">D-</th><th>D±</th><th class="ptn">Ptn</th></tr></thead>
<tbody>
{chr(10).join(tr)}
</tbody></table>
<p class="voet">Bron: Voetbal Vlaanderen · bijgewerkt {nu}</p>
</div>
<script>
function meld(){{parent.postMessage({{jcHoogte:document.documentElement.scrollHeight}},"*")}}
addEventListener("load",meld);addEventListener("resize",meld);
</script></body></html>"""


if __name__ == "__main__":
    bron = sys.argv[1] if len(sys.argv) > 1 else BRON_URL
    rijen = stand(lees_zip(bron))
    UIT.mkdir(exist_ok=True)
    (UIT / "index.html").write_text(render(rijen), encoding="utf-8")
    (UIT / "stand.json").write_text(json.dumps(rijen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rijen)} ploegen weggeschreven naar {UIT}")
