"""Genera HTML autocontenido: visor multi-planta PLN-01 × MET-01 (revisión equipo)."""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from inspecciones.partidas_catalogo import PARTIDAS_SEMILLA  # noqa: E402

DOWNLOADS = Path.home() / "Downloads"
DOCS_OUT = ROOT / "entregables-revision"


def _partidas() -> list[dict]:
    rows = []
    for c, g, t, u, _a, _o, _d in PARTIDAS_SEMILLA:
        if str(c).startswith("EST_"):
            continue
        rows.append(
            {
                "codigo": c,
                "grupo": g.label if hasattr(g, "label") else str(g),
                "titulo": t,
                "unidad": u.label if hasattr(u, "label") else str(u),
            }
        )
    return rows


def main() -> None:
    partidas = _partidas()
    plantas = [
        {"codigo_piso": "PB", "titulo": "Planta baja", "orden": 0},
        {"codigo_piso": "P1", "titulo": "Piso 1", "orden": 1},
        {"codigo_piso": "P2", "titulo": "Piso 2", "orden": 2},
    ]
    # Semilla de revisión: varias plantas con reparaciones ya asignadas
    seed = {
        "PB-C-C4": {
            "partida": "REP_COL_LOCAL",
            "cantidad": "1",
            "apuntamiento": "preventivo",
            "nota": "Espiga / desprendimiento local",
            "elemento": "Columna",
            "piso": "PB",
            "titulo_partida": "Reparación local de columna",
        },
        "PB-V(C-D)·eje4": {
            "partida": "INY_FISURA",
            "cantidad": "2.4",
            "apuntamiento": "trabajo",
            "nota": "Fisura diagonal tramo C-D",
            "elemento": "Viga",
            "piso": "PB",
            "titulo_partida": "Inyección estructural de fisuras",
        },
        "PB-C-B3": {
            "partida": "APUNT_COL",
            "cantidad": "1",
            "apuntamiento": "ambos",
            "nota": "Apuntalar antes de intervenir",
            "elemento": "Columna",
            "piso": "PB",
            "titulo_partida": "Apuntalamiento de trabajo — columnas",
        },
        "P1-V(B-C)·eje3": {
            "partida": "REP_VIGA_LOCAL",
            "cantidad": "1",
            "apuntamiento": "trabajo",
            "nota": "Daño en zona de apoyo",
            "elemento": "Viga",
            "piso": "P1",
            "titulo_partida": "Reparación local de viga",
        },
        "P1-C-C4": {
            "partida": "REF_COL",
            "cantidad": "1",
            "apuntamiento": "preventivo",
            "nota": "Encamisado propuesto",
            "elemento": "Columna",
            "piso": "P1",
            "titulo_partida": "Refuerzo de columna (encamisado / perfiles)",
        },
        "P2-V(C-D)·eje4": {
            "partida": "FIS_CORTE",
            "cantidad": "1.8",
            "apuntamiento": "na",
            "nota": "Patrón de corte sísmico",
            "elemento": "Viga",
            "piso": "P2",
            "titulo_partida": "Tratamiento de grieta de corte (vigas / muros)",
        },
        "P2-C-B4": {
            "partida": "FIS_SELLADO",
            "cantidad": "0.6",
            "apuntamiento": "na",
            "nota": "Microfisura no estructural",
            "elemento": "Columna",
            "piso": "P2",
            "titulo_partida": "Sellado no estructural de fisuras / microfisuras",
        },
    }

    partidas_json = json.dumps(partidas, ensure_ascii=False)
    plantas_json = json.dumps(plantas, ensure_ascii=False)
    seed_json = json.dumps(seed, ensure_ascii=False)
    hoy = date.today().isoformat()

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Revisión equipo — Visor multi-planta PLN-01 × MET-01</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: "Segoe UI", Arial, Helvetica, sans-serif; background: #f1f5f9; color: #0f172a; }}
    .barra {{ display: flex; height: 4px; }}
    .barra span {{ flex: 1; }}
    .ve-a {{ background: #ffcc00; }} .ve-b {{ background: #00247d; }} .ve-c {{ background: #c8102e; }}
    .aviso {{
      background: #fff8e6; border-bottom: 1px solid #f0d78c; color: #5c4813;
      padding: 8px 16px; font-size: 0.8rem; line-height: 1.4;
    }}
    .aviso strong {{ color: #00247d; }}
    .top {{
      background: linear-gradient(120deg, #001a5c, #00247d 55%, #0a3a8a);
      color: #fff; padding: 12px 16px; border-bottom: 3px solid #ffcc00;
    }}
    .top h1 {{ margin: 0; font-size: 1.05rem; font-weight: 800; }}
    .top .sub {{ margin: 4px 0 0; font-size: 0.8rem; opacity: 0.92; }}
    .chip {{
      display: inline-block; background: rgba(255,255,255,0.12);
      border: 1px solid rgba(255,255,255,0.28); border-radius: 999px;
      padding: 2px 10px; font-size: 0.75rem; margin: 2px 4px 0 0;
    }}
    .layout {{ display: grid; grid-template-columns: 1fr minmax(300px, 360px); gap: 0; }}
    @media (max-width: 960px) {{ .layout {{ grid-template-columns: 1fr; }} }}
    .main {{ padding: 12px 14px 20px; }}
    .panel {{
      background: #fff; border-left: 1px solid #cbd5e1; padding: 14px;
      overflow: auto; max-height: calc(100vh - 120px); position: sticky; top: 0;
    }}
    h2 {{ margin: 0 0 6px; font-size: 0.9rem; color: #00247d; font-weight: 800; }}
    h3 {{ margin: 14px 0 6px; font-size: 0.82rem; color: #00247d; font-weight: 800;
      border-bottom: 2px solid #ffcc00; padding-bottom: 2px; }}
    .hint {{ font-size: 0.75rem; color: #64748b; margin: 0 0 10px; line-height: 1.35; }}
    .tabs {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 10px; }}
    .tab {{
      border: 1px solid #94a3b8; background: #fff; color: #00247d;
      border-radius: 999px; padding: 6px 12px; font-size: 0.8rem; font-weight: 700; cursor: pointer;
    }}
    .tab:hover {{ background: #eef2f8; }}
    .tab.on {{ background: #00247d; color: #fff; border-color: #00247d; }}
    .tab .n {{ display: inline-block; margin-left: 6px; background: #ffcc00; color: #001a5c;
      border-radius: 999px; padding: 0 6px; font-size: 0.7rem; }}
    .tab.on .n {{ background: #fff; }}
    .mosaic {{
      display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 10px; margin-bottom: 12px;
    }}
    .floor-card {{
      background: #fff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 8px;
      cursor: pointer;
    }}
    .floor-card:hover, .floor-card.on {{ border-color: #00247d; outline: 2px solid #ffcc00; }}
    .floor-card h4 {{ margin: 0 0 4px; font-size: 0.78rem; color: #00247d; }}
    .floor-card .meta {{ font-size: 0.7rem; color: #64748b; margin-bottom: 4px; }}
    .floor-card svg {{ width: 100%; height: auto; display: block; background: #f8fafc; border-radius: 6px; }}
    .work {{
      background: #fff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 10px;
    }}
    .work svg {{ width: 100%; max-height: 380px; display: block; }}
    label {{ display: block; font-size: 0.72rem; font-weight: 700; color: #334155; margin: 8px 0 3px; }}
    select, input, textarea {{
      width: 100%; font-size: 0.85rem; padding: 7px 8px;
      border: 1px solid #cbd5e1; border-radius: 6px; background: #fff;
    }}
    button {{
      margin-top: 10px; width: 100%; background: #00247d; color: #fff; border: 0;
      padding: 9px; border-radius: 6px; font-weight: 700; cursor: pointer;
    }}
    button:hover {{ background: #001a5c; }}
    button.sec {{ background: #fff; color: #00247d; border: 1px solid #00247d; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.72rem; margin-top: 6px; }}
    th, td {{ border: 1px solid #e2e8f0; padding: 4px 6px; text-align: left; vertical-align: top; }}
    th {{ background: #00247d; color: #fff; }}
    tr.hi td {{ background: #fff8e6; }}
    .el {{ cursor: pointer; }}
    .el:hover {{ filter: brightness(1.08); }}
    .el.sel {{ stroke: #ffcc00 !important; stroke-width: 3.5 !important; }}
    .badge {{
      display: inline-block; background: #eef2f8; border-radius: 999px;
      padding: 1px 8px; font-size: 0.7rem; font-weight: 700; color: #00247d;
    }}
    .toast {{
      display: none; margin-top: 8px; padding: 8px; background: #ecfdf5;
      border: 1px solid #6ee7b7; border-radius: 6px; font-size: 0.75rem; color: #065f46;
    }}
    .toast.err {{ background: #fef2f2; border-color: #fecaca; color: #991b1b; }}
    .kpi-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 10px; }}
    .kpi {{
      background: #fff; border: 1px solid #d7dee8; border-radius: 8px;
      padding: 6px 10px; border-top: 3px solid #00247d; min-width: 90px;
    }}
    .kpi .v {{ font-size: 1.1rem; font-weight: 800; color: #00247d; }}
    .kpi .l {{ font-size: 0.68rem; color: #64748b; font-weight: 700; }}
    .leyenda {{
      display: flex; flex-wrap: wrap; gap: 10px; font-size: 0.72rem; color: #475569; margin: 0 0 8px;
    }}
    .leyenda span::before {{
      content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 2px;
      margin-right: 5px; vertical-align: -1px;
    }}
    .l-ok::before {{ background: #0f766e; }}
    .l-a::before {{ background: #eab308; }}
    .l-bc::before {{ background: #dc2626; }}
  </style>
</head>
<body>
  <div class="barra"><span class="ve-a"></span><span class="ve-b"></span><span class="ve-c"></span></div>
  <div class="aviso">
    <strong>Prototipo para revisión de equipo</strong> · CPEH Fase II ROJO ·
    Visor multi-planta (PLN-01) con asignación de partidas (MET-01).
    Archivo autocontenido: ábralo en cualquier navegador, sin servidor.
    Los cambios se guardan solo en este equipo (navegador). Datos de ejemplo precargados · {hoy}.
  </div>
  <header class="top">
    <h1>Visor multi-planta × metrados — PLN-01 · MET-01</h1>
    <p class="sub">
      Caso demostración · HAB-DEMO-MULTI · varias plantas · catálogo MET-01 de intervención
    </p>
    <p class="sub" style="margin-top:8px">
      <span class="chip">Selector de plantas</span>
      <span class="chip">Vista conjunta</span>
      <span class="chip">Resumen de reparaciones</span>
    </p>
  </header>

  <div class="layout">
    <div class="main">
      <div class="kpi-row">
        <div class="kpi"><div class="v" id="kPlantas">0</div><div class="l">Plantas</div></div>
        <div class="kpi"><div class="v" id="kArr">0</div><div class="l">Arreglos totales</div></div>
        <div class="kpi"><div class="v" id="kActiva">—</div><div class="l">Planta activa</div></div>
      </div>

      <h3>1 · Vista conjunta de plantas</h3>
      <p class="hint">Pulse una tarjeta para editar esa planta. Borde verde = elemento con partida asignada.</p>
      <div class="leyenda">
        <span class="l-ok">Con reparación</span>
        <span class="l-a">Daño leve (estilo PLN-01)</span>
        <span class="l-bc">Daño moderado/severo (estilo PLN-01)</span>
      </div>
      <div class="mosaic" id="mosaic"></div>

      <h3>2 · Planta activa — asignar reparaciones</h3>
      <div class="tabs" id="tabs"></div>
      <div class="work">
        <svg id="plano" viewBox="0 0 640 400" aria-label="Plano de inspección"></svg>
      </div>

      <h3>3 · Resumen de reparaciones (todas las plantas)</h3>
      <p class="hint">Listado unificado. Filas de la planta activa resaltadas. Clic en una fila para saltar al elemento.</p>
      <table>
        <thead>
          <tr>
            <th>Planta</th><th>ID PLN-01</th><th>Partida</th><th>Elemento</th>
            <th>Cant.</th><th>Apunt.</th><th>Nota</th>
          </tr>
        </thead>
        <tbody id="resumen"></tbody>
      </table>
    </div>

    <aside class="panel">
      <h2>Elemento seleccionado</h2>
      <p class="hint" id="selHint">Elija una planta y haga clic en un círculo (columna) o tramo (viga).</p>
      <div id="form" style="display:none">
        <label>Planta</label>
        <input id="pisoAct" readonly>
        <label>id_pln01</label>
        <input id="idPln" readonly>
        <label>Elemento</label>
        <input id="tipoEl" readonly>
        <label>Partida (catálogo MET-01)</label>
        <select id="partida"></select>
        <label>Cantidad</label>
        <input id="cant" type="number" step="0.001" value="1">
        <label>Tipo apuntamiento</label>
        <select id="apunt">
          <option value="na">No aplica</option>
          <option value="preventivo">Preventivo (estabilización post-sísmica)</option>
          <option value="trabajo">De trabajo (durante la intervención)</option>
          <option value="ambos">Preventivo + trabajo</option>
        </select>
        <label>Nota</label>
        <textarea id="nota" rows="2"></textarea>
        <button type="button" id="btnSave">Guardar arreglo</button>
        <button type="button" class="sec" id="btnClear">Quitar arreglo</button>
        <button type="button" class="sec" id="btnReset" style="margin-top:6px">Restaurar ejemplo de revisión</button>
        <div class="toast" id="toast"></div>
      </div>

      <h2 style="margin-top:18px">En esta planta <span class="badge" id="nArrPiso">0</span></h2>
      <table>
        <thead><tr><th>ID</th><th>Partida</th><th>Cant.</th></tr></thead>
        <tbody id="tbodyPiso"></tbody>
      </table>
    </aside>
  </div>

  <script>
    const PARTIDAS = {partidas_json};
    const SEED = {seed_json};
    const KEY = "cpeh_met01_multi_revision_v1";

    let PLANTAS = {plantas_json};
    let store = {{}};
    let pisoActivo = (PLANTAS[0] && PLANTAS[0].codigo_piso) || "PB";
    let selectedLocal = null;

    function loadStore() {{
      try {{
        const raw = localStorage.getItem(KEY);
        if (raw) {{
          store = JSON.parse(raw) || {{}};
          return;
        }}
      }} catch (e) {{}}
      store = JSON.parse(JSON.stringify(SEED));
      localStorage.setItem(KEY, JSON.stringify(store));
    }}

    function fullId(localId) {{
      return pisoActivo + "-" + localId;
    }}

    function countByPiso(codigo) {{
      let n = 0;
      Object.keys(store).forEach(id => {{
        const p = (store[id].piso || id.split("-")[0] || "").toUpperCase();
        if (p === codigo.toUpperCase()) n++;
      }});
      return n;
    }}

    const sel = document.getElementById("partida");
    PARTIDAS.forEach(p => {{
      const o = document.createElement("option");
      o.value = p.codigo;
      o.textContent = p.codigo + " — " + p.titulo + " (" + p.unidad + ")";
      sel.appendChild(o);
    }});

    function toast(msg, err) {{
      const t = document.getElementById("toast");
      t.textContent = msg;
      t.className = "toast" + (err ? " err" : "");
      t.style.display = "block";
      setTimeout(() => {{ t.style.display = "none"; }}, 2600);
    }}

    const ELEMS = [
      {{ local: "V(A-B)·eje4", tipo: "Viga", kind: "rect", x: 90, y: 92, w: 100, h: 16, fill: "#fef9c3", stroke: "#ca8a04" }},
      {{ local: "V(B-C)·eje4", tipo: "Viga", kind: "rect", x: 210, y: 92, w: 100, h: 16, fill: "#fef9c3", stroke: "#ca8a04" }},
      {{ local: "V(C-D)·eje4", tipo: "Viga", kind: "rect", x: 330, y: 92, w: 100, h: 16, fill: "#fecaca", stroke: "#b91c1c" }},
      {{ local: "V(A-B)·eje3", tipo: "Viga", kind: "rect", x: 90, y: 192, w: 100, h: 16, fill: "#fef9c3", stroke: "#ca8a04" }},
      {{ local: "V(B-C)·eje3", tipo: "Viga", kind: "rect", x: 210, y: 192, w: 100, h: 16, fill: "#fecaca", stroke: "#b91c1c" }},
      {{ local: "C-A4", tipo: "Columna", kind: "circle", cx: 80, cy: 100, r: 10, fill: "#3b82f6" }},
      {{ local: "C-B4", tipo: "Columna", kind: "circle", cx: 200, cy: 100, r: 10, fill: "#fef08a", stroke: "#eab308" }},
      {{ local: "C-C4", tipo: "Columna", kind: "circle", cx: 320, cy: 100, r: 10, fill: "#fecaca", stroke: "#dc2626" }},
      {{ local: "C-D4", tipo: "Columna", kind: "circle", cx: 440, cy: 100, r: 10, fill: "#3b82f6" }},
      {{ local: "C-A3", tipo: "Columna", kind: "circle", cx: 80, cy: 200, r: 10, fill: "#3b82f6" }},
      {{ local: "C-B3", tipo: "Columna", kind: "circle", cx: 200, cy: 200, r: 10, fill: "#fecaca", stroke: "#dc2626" }},
      {{ local: "C-C3", tipo: "Columna", kind: "circle", cx: 320, cy: 200, r: 10, fill: "#3b82f6" }},
    ];

    function svgFrame(pisoLabel, interactive) {{
      let g = "";
      g += '<text x="12" y="22" fill="#00247d" font-size="13" font-weight="800">' + pisoLabel + ' — ejes A–D · 3–4</text>';
      g += '<g stroke="#94a3b8" stroke-dasharray="4 3" stroke-width="1">';
      g += '<line x1="80" y1="70" x2="80" y2="300"/><line x1="200" y1="70" x2="200" y2="300"/>';
      g += '<line x1="320" y1="70" x2="320" y2="300"/><line x1="440" y1="70" x2="440" y2="300"/>';
      g += '<line x1="60" y1="100" x2="520" y2="100"/><line x1="60" y1="200" x2="520" y2="200"/></g>';
      g += '<g fill="#9d174d" font-size="11" font-weight="800">';
      g += '<text x="74" y="62">A</text><text x="194" y="62">B</text><text x="314" y="62">C</text><text x="434" y="62">D</text>';
      g += '<text x="40" y="104">4</text><text x="40" y="204">3</text></g>';
      ELEMS.forEach(e => {{
        const fid = pisoLabel + "-" + e.local;
        const assigned = !!store[fid];
        const cls = interactive ? ' class="el"' : "";
        const data = interactive
          ? ' data-local="' + e.local + '" data-tipo="' + e.tipo + '"'
          : "";
        let stroke = e.stroke || "#334155";
        let sw = e.stroke ? "2" : "1";
        if (assigned) {{ stroke = "#0f766e"; sw = "3"; }}
        if (e.kind === "rect") {{
          g += '<rect' + cls + data + ' x="' + e.x + '" y="' + e.y + '" width="' + e.w +
            '" height="' + e.h + '" fill="' + e.fill + '" stroke="' + stroke +
            '" stroke-width="' + sw + '" rx="2"/>';
        }} else {{
          g += '<circle' + cls + data + ' cx="' + e.cx + '" cy="' + e.cy + '" r="' + e.r +
            '" fill="' + e.fill + '" stroke="' + stroke + '" stroke-width="' + sw + '"/>';
        }}
      }});
      g += '<text x="480" y="100" fill="#cf142b" font-size="11" font-weight="800">N</text>';
      return g;
    }}

    function renderMosaic() {{
      const box = document.getElementById("mosaic");
      box.innerHTML = "";
      PLANTAS.forEach(p => {{
        const n = countByPiso(p.codigo_piso);
        const card = document.createElement("div");
        card.className = "floor-card" + (p.codigo_piso === pisoActivo ? " on" : "");
        card.innerHTML =
          "<h4>" + (p.titulo || p.codigo_piso) + "</h4>" +
          '<div class="meta">' + n + " arreglo(s)</div>" +
          '<svg viewBox="0 0 640 320">' + svgFrame(p.codigo_piso, false) + "</svg>";
        card.onclick = () => setPiso(p.codigo_piso);
        box.appendChild(card);
      }});
    }}

    function renderTabs() {{
      const tabs = document.getElementById("tabs");
      tabs.innerHTML = "";
      PLANTAS.forEach(p => {{
        const b = document.createElement("button");
        b.type = "button";
        b.className = "tab" + (p.codigo_piso === pisoActivo ? " on" : "");
        b.innerHTML = (p.titulo || p.codigo_piso) +
          '<span class="n">' + countByPiso(p.codigo_piso) + "</span>";
        b.onclick = () => setPiso(p.codigo_piso);
        tabs.appendChild(b);
      }});
    }}

    function bindClicks(svg) {{
      svg.querySelectorAll(".el").forEach(el => {{
        el.addEventListener("click", () => {{
          svg.querySelectorAll(".el").forEach(x => x.classList.remove("sel"));
          el.classList.add("sel");
          selectedLocal = el.dataset.local;
          const fid = fullId(selectedLocal);
          document.getElementById("form").style.display = "block";
          document.getElementById("selHint").textContent =
            "Asigne una partida MET-01 a este elemento de " + pisoActivo + ".";
          document.getElementById("pisoAct").value = pisoActivo;
          document.getElementById("idPln").value = fid;
          document.getElementById("tipoEl").value = el.dataset.tipo;
          const prev = store[fid];
          if (prev) {{
            sel.value = prev.partida;
            document.getElementById("cant").value = prev.cantidad ?? 1;
            document.getElementById("apunt").value = prev.apuntamiento || "na";
            document.getElementById("nota").value = prev.nota || "";
          }} else {{
            document.getElementById("cant").value = "1";
            document.getElementById("apunt").value = "na";
            document.getElementById("nota").value = "";
          }}
        }});
      }});
    }}

    function renderPlano() {{
      const svg = document.getElementById("plano");
      const pl = PLANTAS.find(p => p.codigo_piso === pisoActivo);
      const label = (pl && pl.titulo) ? (pl.codigo_piso + " · " + pl.titulo) : pisoActivo;
      svg.innerHTML = svgFrame(pisoActivo, true);
      const t = svg.querySelector("text");
      if (t) t.textContent = label + " — seleccione elemento";
      bindClicks(svg);
    }}

    function renderResumen() {{
      const tb = document.getElementById("resumen");
      tb.innerHTML = "";
      const ids = Object.keys(store).sort();
      if (!ids.length) {{
        tb.innerHTML = '<tr><td colspan="7">Sin reparaciones asignadas aún.</td></tr>';
        return;
      }}
      ids.forEach(id => {{
        const r = store[id];
        const piso = (r.piso || id.split("-")[0] || "").toUpperCase();
        const tr = document.createElement("tr");
        if (piso === pisoActivo.toUpperCase()) tr.className = "hi";
        const partLabel = r.partida + (r.titulo_partida ? " — " + r.titulo_partida : "");
        tr.innerHTML =
          "<td>" + piso + "</td>" +
          "<td>" + id + "</td>" +
          "<td>" + partLabel + "</td>" +
          "<td>" + (r.elemento || "") + "</td>" +
          "<td>" + (r.cantidad ?? "") + "</td>" +
          "<td>" + (r.apuntamiento || "na") + "</td>" +
          "<td>" + (r.nota || "") + "</td>";
        tr.style.cursor = "pointer";
        tr.onclick = () => {{
          setPiso(piso);
          setTimeout(() => {{
            const local = id.indexOf("-") >= 0 ? id.slice(id.indexOf("-") + 1) : id;
            const el = document.querySelector('.el[data-local="' + CSS.escape(local) + '"]');
            if (el) el.dispatchEvent(new Event("click"));
          }}, 50);
        }};
        tb.appendChild(tr);
      }});
    }}

    function renderPisoList() {{
      const tb = document.getElementById("tbodyPiso");
      tb.innerHTML = "";
      let n = 0;
      Object.keys(store).sort().forEach(id => {{
        const r = store[id];
        const piso = (r.piso || id.split("-")[0] || "").toUpperCase();
        if (piso !== pisoActivo.toUpperCase()) return;
        n++;
        const tr = document.createElement("tr");
        tr.innerHTML = "<td>" + id + "</td><td>" + r.partida + "</td><td>" + (r.cantidad ?? "") + "</td>";
        tb.appendChild(tr);
      }});
      document.getElementById("nArrPiso").textContent = n;
    }}

    function refreshAll() {{
      document.getElementById("kPlantas").textContent = PLANTAS.length;
      document.getElementById("kArr").textContent = Object.keys(store).length;
      document.getElementById("kActiva").textContent = pisoActivo;
      renderTabs();
      renderMosaic();
      renderPlano();
      renderResumen();
      renderPisoList();
    }}

    function setPiso(codigo) {{
      pisoActivo = codigo;
      selectedLocal = null;
      document.getElementById("form").style.display = "none";
      document.getElementById("selHint").textContent =
        "Planta " + codigo + ": haga clic en un elemento del plano.";
      refreshAll();
    }}

    function persist() {{
      localStorage.setItem(KEY, JSON.stringify(store));
      toast("Guardado en este navegador");
      refreshAll();
    }}

    document.getElementById("btnSave").onclick = () => {{
      if (!selectedLocal) return;
      const fid = fullId(selectedLocal);
      const p = PARTIDAS.find(x => x.codigo === sel.value);
      store[fid] = {{
        partida: sel.value,
        cantidad: document.getElementById("cant").value,
        apuntamiento: document.getElementById("apunt").value,
        nota: document.getElementById("nota").value,
        elemento: document.getElementById("tipoEl").value,
        piso: pisoActivo,
        titulo_partida: p ? p.titulo : "",
      }};
      persist();
    }};

    document.getElementById("btnClear").onclick = () => {{
      if (!selectedLocal) return;
      delete store[fullId(selectedLocal)];
      persist();
    }};

    document.getElementById("btnReset").onclick = () => {{
      store = JSON.parse(JSON.stringify(SEED));
      localStorage.setItem(KEY, JSON.stringify(store));
      toast("Ejemplo de revisión restaurado");
      refreshAll();
    }};

    loadStore();
    refreshAll();
  </script>
</body>
</html>
"""

    DOCS_OUT.mkdir(parents=True, exist_ok=True)
    name = "PLN01-MET01-visor-multi-planta-revision-equipo.html"
    out_docs = DOCS_OUT / name
    out_dl = DOWNLOADS / name
    out_docs.write_text(html, encoding="utf-8")
    out_dl.write_text(html, encoding="utf-8")
    print("OK", out_docs)
    print("OK", out_dl)
    print("bytes", len(html.encode("utf-8")))


if __name__ == "__main__":
    main()
