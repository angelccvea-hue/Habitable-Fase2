"""Genera prototipo HTML: plano PLN-01 + asignación de partidas MET-01 (visor dinámico)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from inspecciones.partidas_catalogo import PARTIDAS_SEMILLA  # noqa: E402

DOWNLOADS = Path.home() / "Downloads"


def main() -> None:
    partidas = [
        {
            "codigo": c,
            "grupo": g.label if hasattr(g, "label") else str(g),
            "titulo": t,
            "unidad": u.label if hasattr(u, "label") else str(u),
        }
        for c, g, t, u, _a, _o, _d in PARTIDAS_SEMILLA
        if not str(c).startswith("EST_")  # catálogo de intervención en el panel
    ]
    data = json.dumps(partidas, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<title>Visor PLN-01 × MET-01 — prototipo</title>
<style>
  body {{ margin:0; font-family:Arial,Helvetica,sans-serif; background:#f1f5f9; color:#0f172a; }}
  .top {{ background:linear-gradient(120deg,#001a5c,#00247d); color:#fff; padding:12px 16px; border-bottom:3px solid #ffcc00; }}
  .top h1 {{ margin:0; font-size:16px; }}
  .top p {{ margin:4px 0 0; font-size:12px; opacity:.9; }}
  .barra {{ display:flex; height:4px; }}
  .barra span {{ flex:1; }}
  .ve-a {{ background:#ffcc00; }} .ve-b {{ background:#00247d; }} .ve-c {{ background:#c8102e; }}
  .wrap {{ display:grid; grid-template-columns:1fr 320px; gap:0; min-height:calc(100vh - 70px); }}
  .canvas {{ padding:12px; }}
  .panel {{ background:#fff; border-left:1px solid #cbd5e1; padding:12px; overflow:auto; }}
  .panel h2 {{ margin:0 0 8px; font-size:13px; color:#00247d; }}
  .hint {{ font-size:11px; color:#64748b; margin:0 0 10px; }}
  label {{ display:block; font-size:11px; font-weight:700; color:#334155; margin:8px 0 3px; }}
  select, input, textarea {{ width:100%; box-sizing:border-box; font-size:12px; padding:6px; border:1px solid #cbd5e1; border-radius:4px; }}
  button {{ margin-top:10px; width:100%; background:#00247d; color:#fff; border:0; padding:8px; border-radius:4px; font-weight:700; cursor:pointer; }}
  button.sec {{ background:#fff; color:#00247d; border:1px solid #00247d; }}
  table {{ width:100%; border-collapse:collapse; font-size:11px; margin-top:12px; }}
  th, td {{ border:1px solid #e2e8f0; padding:4px 6px; text-align:left; }}
  th {{ background:#00247d; color:#fff; }}
  .el {{ cursor:pointer; }}
  .el:hover {{ opacity:.85; }}
  .el.sel {{ stroke:#ffcc00 !important; stroke-width:3 !important; }}
  .badge {{ display:inline-block; background:#eef2f8; border-radius:999px; padding:1px 7px; font-size:10px; }}
</style>
</head>
<body>
<div class="barra"><span class="ve-a"></span><span class="ve-b"></span><span class="ve-c"></span></div>
<div class="top">
  <h1>Prototipo — Plano PLN-01 × catálogo MET-01</h1>
  <p>Seleccione un elemento del plano → asigne partida. Los datos quedan en este navegador (localStorage). Misma idea que irá al sistema (LineaMetrado.id_pln01).</p>
</div>
<div class="wrap">
  <div class="canvas">
    <svg id="plano" viewBox="0 0 640 420" width="100%" style="background:#fff;border:1px solid #cbd5e1;border-radius:8px">
      <text x="16" y="28" fill="#00247d" font-size="14" font-weight="800">PB — ejemplo didáctico (ejes A–D · 1–4)</text>
      <text x="16" y="48" fill="#64748b" font-size="11">Clic en columna (círculo) o tramo de viga (rectángulo)</text>
      <!-- ejes -->
      <g stroke="#94a3b8" stroke-dasharray="4 3" stroke-width="1">
        <line x1="80" y1="80" x2="80" y2="360"/><line x1="200" y1="80" x2="200" y2="360"/>
        <line x1="320" y1="80" x2="320" y2="360"/><line x1="440" y1="80" x2="440" y2="360"/>
        <line x1="60" y1="100" x2="560" y2="100"/><line x1="60" y1="200" x2="560" y2="200"/>
        <line x1="60" y1="300" x2="560" y2="300"/>
      </g>
      <g fill="#9d174d" font-size="12" font-weight="800">
        <text x="74" y="72">A</text><text x="194" y="72">B</text><text x="314" y="72">C</text><text x="434" y="72">D</text>
        <text x="40" y="104">4</text><text x="40" y="204">3</text><text x="40" y="304">2</text>
      </g>
      <!-- vigas (tramos) -->
      <rect class="el" data-id="PB-V(A-B)·eje4" data-tipo="Viga" x="90" y="92" width="100" height="16" fill="#fef9c3" stroke="#ca8a04" rx="2"/>
      <rect class="el" data-id="PB-V(B-C)·eje4" data-tipo="Viga" x="210" y="92" width="100" height="16" fill="#fef9c3" stroke="#ca8a04" rx="2"/>
      <rect class="el" data-id="PB-V(C-D)·eje4" data-tipo="Viga" x="330" y="92" width="100" height="16" fill="#fecaca" stroke="#b91c1c" rx="2"/>
      <rect class="el" data-id="PB-V(A-B)·eje3" data-tipo="Viga" x="90" y="192" width="100" height="16" fill="#fef9c3" stroke="#ca8a04" rx="2"/>
      <rect class="el" data-id="PB-V(B-C)·eje3" data-tipo="Viga" x="210" y="192" width="100" height="16" fill="#fecaca" stroke="#b91c1c" rx="2"/>
      <!-- columnas -->
      <circle class="el" data-id="PB-C-A4" data-tipo="Columna" cx="80" cy="100" r="10" fill="#3b82f6"/>
      <circle class="el" data-id="PB-C-B4" data-tipo="Columna" cx="200" cy="100" r="10" fill="#fef08a" stroke="#eab308" stroke-width="2"/>
      <circle class="el" data-id="PB-C-C4" data-tipo="Columna" cx="320" cy="100" r="10" fill="#fecaca" stroke="#dc2626" stroke-width="2"/>
      <circle class="el" data-id="PB-C-D4" data-tipo="Columna" cx="440" cy="100" r="10" fill="#3b82f6"/>
      <circle class="el" data-id="PB-C-A3" data-tipo="Columna" cx="80" cy="200" r="10" fill="#3b82f6"/>
      <circle class="el" data-id="PB-C-B3" data-tipo="Columna" cx="200" cy="200" r="10" fill="#fecaca" stroke="#dc2626" stroke-width="2"/>
      <circle class="el" data-id="PB-C-C3" data-tipo="Columna" cx="320" cy="200" r="10" fill="#3b82f6"/>
      <text x="500" y="100" fill="#cf142b" font-size="12" font-weight="800">NORTE</text>
      <text x="16" y="400" fill="#64748b" font-size="10">Amarillo = daño A · Rojo = B/C (estilo PLN-01). Tras asignar partida, el borde del elemento se marca.</text>
    </svg>
  </div>
  <div class="panel">
    <h2>Elemento seleccionado</h2>
    <p class="hint" id="selHint">Haga clic en un círculo o tramo del plano.</p>
    <div id="form" style="display:none">
      <label>id_pln01</label>
      <input id="idPln" readonly/>
      <label>Elemento</label>
      <input id="tipoEl" readonly/>
      <label>Partida (catálogo MET-01)</label>
      <select id="partida"></select>
      <label>Cantidad</label>
      <input id="cant" type="number" step="0.001" value="1"/>
      <label>Tipo apuntamiento</label>
      <select id="apunt">
        <option value="na">na</option>
        <option value="preventivo">preventivo</option>
        <option value="trabajo">trabajo</option>
        <option value="ambos">ambos</option>
      </select>
      <label>Nota</label>
      <textarea id="nota" rows="2"></textarea>
      <button type="button" id="btnSave">Guardar arreglo en este elemento</button>
      <button type="button" class="sec" id="btnClear">Quitar arreglo</button>
    </div>
    <h2 style="margin-top:16px">Arreglos en el plano <span class="badge" id="nArr">0</span></h2>
    <table>
      <thead><tr><th>ID</th><th>Partida</th><th>Cant.</th></tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</div>
<script>
const PARTIDAS = {data};
const KEY = "cpeh_met01_proto_v1";
let selected = null;
let store = {{}};
try {{ store = JSON.parse(localStorage.getItem(KEY) || "{{}}") || {{}}; }} catch(e) {{ store = {{}}; }}

const sel = document.getElementById("partida");
PARTIDAS.forEach(p => {{
  const o = document.createElement("option");
  o.value = p.codigo;
  o.textContent = p.codigo + " — " + p.titulo + " (" + p.unidad + ")";
  sel.appendChild(o);
}});

function paintAssigned() {{
  document.querySelectorAll(".el").forEach(el => {{
    const id = el.dataset.id;
    if (store[id]) el.setAttribute("stroke", "#0f766e");
  }});
  const tb = document.getElementById("tbody");
  tb.innerHTML = "";
  Object.keys(store).sort().forEach(id => {{
    const r = store[id];
    const tr = document.createElement("tr");
    tr.innerHTML = "<td>"+id+"</td><td>"+r.partida+"</td><td>"+r.cantidad+"</td>";
    tb.appendChild(tr);
  }});
  document.getElementById("nArr").textContent = Object.keys(store).length;
}}

function selectEl(el) {{
  document.querySelectorAll(".el").forEach(e => e.classList.remove("sel"));
  el.classList.add("sel");
  selected = el.dataset.id;
  document.getElementById("form").style.display = "block";
  document.getElementById("selHint").textContent = "Asigne una partida del catálogo MET-01 a este elemento.";
  document.getElementById("idPln").value = selected;
  document.getElementById("tipoEl").value = el.dataset.tipo;
  const prev = store[selected];
  if (prev) {{
    sel.value = prev.partida;
    document.getElementById("cant").value = prev.cantidad;
    document.getElementById("apunt").value = prev.apuntamiento || "na";
    document.getElementById("nota").value = prev.nota || "";
  }} else {{
    document.getElementById("cant").value = "1";
    document.getElementById("apunt").value = "na";
    document.getElementById("nota").value = "";
  }}
}}

document.querySelectorAll(".el").forEach(el => {{
  el.addEventListener("click", () => selectEl(el));
}});

document.getElementById("btnSave").onclick = () => {{
  if (!selected) return;
  store[selected] = {{
    partida: sel.value,
    cantidad: document.getElementById("cant").value,
    apuntamiento: document.getElementById("apunt").value,
    nota: document.getElementById("nota").value,
    elemento: document.getElementById("tipoEl").value,
  }};
  localStorage.setItem(KEY, JSON.stringify(store));
  paintAssigned();
}};

document.getElementById("btnClear").onclick = () => {{
  if (!selected) return;
  delete store[selected];
  localStorage.setItem(KEY, JSON.stringify(store));
  paintAssigned();
}};

paintAssigned();
</script>
</body>
</html>
"""
    out = DOWNLOADS / "PLN01-MET01-visor-prototipo.html"
    out.write_text(html, encoding="utf-8")
    print("OK", out)


if __name__ == "__main__":
    main()
