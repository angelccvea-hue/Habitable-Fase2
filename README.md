# Habitable Fase II (CPEH)

Aplicación **Django** para la **Comisión Presidencial para la Evaluación de Habitabilidad (CPEH)**: **verificación detallada Fase II** de edificaciones priorizadas en Habitable (etiquetas **rojo**, **amarillo** u otras) tras el sismo del 24-jun-2026.

Incluye ficha de caso, workflow por roles, metrados **MET-01**, planos de inspección **PLN-01** (visor multi-planta), mapa, tablero de operación, Excel/PDF y panel **Jazzmin**. El alcance de este sistema es **hasta Fase II** (no despliega Fase III).

**Repositorio:** https://github.com/angelccvea-hue/Habitable-Fase2

---

## Tabla de contenidos

1. [Qué resuelve](#qué-resuelve)
2. [Stack tecnológico](#stack-tecnológico)
3. [Arquitectura](#arquitectura)
4. [Modelo de dominio](#modelo-de-dominio)
5. [Roles y permisos](#roles-y-permisos)
6. [Rutas principales](#rutas-principales)
7. [Estructura del repositorio](#estructura-del-repositorio)
8. [Despliegue local (desarrollo)](#despliegue-local-desarrollo)
9. [Despliegue en servidor (producción)](#despliegue-en-servidor-producción)
10. [Datos semilla y comandos útiles](#datos-semilla-y-comandos-útiles)
11. [Variables de entorno](#variables-de-entorno)
12. [Notas operativas](#notas-operativas)

---

## Qué resuelve

| Necesidad | Cómo lo cubre la app |
|-----------|----------------------|
| Inventario Fase II (rojo / amarillo) | Modelo `CasoRojo` + precarga Habitable / ranking + visita de verificación |
| Dictamen estructurado | Decisiones **D1–D4**, magnitud **M**, prioridad, medidas, justificación |
| Cuantificación para anteproyecto | Catálogo de partidas + `LineaMetrado` (MET-01) anclado a IDs PLN-01 |
| Lectura espacial por planta | `PlantaInspeccion` + visor SVG multi-planta + resumen de reparaciones |
| Operación de brigadas | Asignación, bandejas por rol, tablero de operación, mapa GeoJSON |
| Evidencia | Fotos, croquis, PDF de informes adjuntos, export Excel/PDF |
| Gobierno de usuarios | Grupos Django + pantalla de gestión / credenciales emitidas |

---

## Stack tecnológico

| Capa | Tecnología |
|------|------------|
| Lenguaje | Python 3.11+ (probado en 3.13) |
| Framework | Django 5.x |
| Admin / UI | django-jazzmin + plantillas propias CPEH |
| API ligera | djangorestframework (geojson / health) |
| Estáticos | WhiteNoise (comprimidos; sin Manifest estricto por Jazzmin) |
| BD | SQLite (dev) o PostgreSQL (prod: `DATABASE_ENGINE=postgres`) |
| Excel | openpyxl |
| PDF | WeasyPrint (+ fallbacks documentados en código para Windows) |
| Imágenes | Pillow |
| Servidor WSGI | Gunicorn (`gunicorn.conf.py`) |
| i18n / TZ | `es-ve` · `America/Caracas` |

Dependencias: `requirements.txt`.

---

## Arquitectura

### Vista lógica

```text
                    ┌─────────────────────────────────────┐
                    │         Navegador (equipo CPEH)      │
                    │  Jazzmin Admin · Tableros · Visor    │
                    └──────────────┬──────────────────────┘
                                   │ HTTP
                    ┌──────────────▼──────────────────────┐
                    │     Django (config + inspecciones)   │
                    │  Auth · Workflow · Admin · Vistas    │
                    │  Excel import/export · PDF · Mapa    │
                    └──────┬───────────────────┬──────────┘
                           │                   │
              ┌────────────▼──────┐   ┌────────▼─────────┐
              │  SQLite / Postgres │   │ media/ (fotos,   │
              │  casos, metrados   │   │ PDF, croquis)    │
              └───────────────────┘   └──────────────────┘
```

### Capas de código

1. **`config/`** — proyecto Django: `settings`, `urls`, `wsgi`, tema Jazzmin.
2. **`inspecciones/`** — dominio de negocio (única app de producto):
   - `models.py` — entidades persistentes
   - `choices.py` — catálogos D/M, severidades, partidas, apuntamiento, etc.
   - `admin.py` + `admin_dashboard.py` — ficha CasoRojo, inlines, panel de control
   - `workflow.py` — transiciones de estado y reglas por rol
   - `*_views.py` — tableros, mapa, operación, visor PLN×MET, usuarios, PDF
   - `excel_plantilla.py` / `excel_import.py` — plantillas e importación
   - `partidas_catalogo.py` — semilla MET-01
   - `management/commands/` — carga ranking, Franco Mar, roles demo, informes PDF
   - `migrations/` — esquema versionado **0001 → 0016**
3. **`templates/`** — HTML admin, tableros, PDF, visor multi-planta.
4. **`static/`** — logos CPEH y assets públicos.
5. **`entregables-revision/`** — HTML autocontenido para revisión de equipo (sin servidor).

### Flujos principales

**A. Caso Fase II (ciclo de vida)**

```text
Precarga Habitable/Ranking
        → Asignación (coordinador / brigada / inspector)
        → Visita 2.ª ronda + validaciones / correcciones
        → Metrados + croquis / PLN-01
        → Dictamen D1–D4 (+ M si aplica)
        → Revisión / aprobación
        → Export Excel · PDF · tablero operación
```

**B. PLN-01 × MET-01**

```text
PlantaInspeccion (PB, P1, P2…)
        → Elementos del plano (id_pln01: PB-C-C4, PB-V(A-B)·eje4…)
        → LineaMetrado (partida catálogo, cantidad, apuntamiento, nota)
        → Visor: mosaico multi-planta + planta activa + resumen unificado
```

**C. Operación**

```text
Casos en BD → operacion_stats / tablero_operacion
           → KPIs por estado, decisión D, prioridad
           → Export Excel / PDF de operación
```

### Decisiones de diseño relevantes

- **Una app de producto** (`inspecciones`) para mantener el dominio unificado (casos + metrados + evidencia).
- **Admin como superficie principal** (Jazzmin): los ingenieros trabajan la ficha; los tableros complementan operación y asignación.
- **IDs PLN-01** como puente plano ↔ metrado (trazabilidad elemento a elemento).
- **Media servida por Django** también en prod (`/media/...`) porque el proxy suele enviar todo a Gunicorn.
- **DATA_UPLOAD / campos POST amplios** — la ficha con muchos inlines supera defaults de Django.

---

## Modelo de dominio

Entidades centrales (nombres de modelo):

| Modelo | Rol |
|--------|-----|
| `CasoRojo` | Expediente Fase II: precarga Habitable, visita, dictamen, GPS, score |
| `LineaMetrado` | Línea de cuantificación; `id_pln01`, `piso_pln`, partida, apuntamiento |
| `PartidaCatalogo` | Catálogo MET-01 (APUNT_*, REP_*, FIS_*, DEM_*, ESC_*, …) |
| `PlantaInspeccion` | Nivel/planta del caso para el visor multi-capa |
| `CroquisAdjunto` / `InformePdfAdjunto` / fotos | Evidencia por caso |
| `HistorialEstado` / `HistorialDetallado` | Auditoría de cambios |
| Credencial emitida | Claves generadas desde gestión de usuarios (operativo) |

Migraciones incluidas hasta **`0016_planta_inspeccion_multi`** (plantas + vínculo croquis).

---

## Roles y permisos

Grupos típicos (comando `crear_roles_ejemplo`):

| Usuario demo | Grupo | Uso |
|--------------|-------|-----|
| `inspector.demo` | inspector | Carga de visita / borrador |
| `revisor.demo` | revisor | Bandeja de revisión |
| `coordinador.demo` | coordinador | Asignación y seguimiento de brigada |

El **superusuario** ve todo el admin y las pantallas de gestión. Las reglas finas están en `workflow.py` (quién puede cambiar estado, editar metrados, etc.).

> Las claves demo se documentan en la guía de desarrolladores del panel; **no** se versionan secretos de producción en este repo.

---

## Rutas principales

| Ruta | Función |
|------|---------|
| `/` | Redirige al admin |
| `/admin/` | Panel Jazzmin (ficha CasoRojo, catálogos) |
| `/api/health/` | Health check JSON (versión, conteos) |
| `/api/casos/geojson/` | Casos para el mapa |
| `/mapa/` | Mapa de casos |
| `/asignacion/` | Tablero de asignación |
| `/asignacion/lote/` | Carga Excel de asignación por lote |
| `/operacion/` | Tablero de operación (+ export `.xlsx` / `.pdf`) |
| `/plano-metrado/` | Visor demo multi-planta |
| `/plano-metrado/<id>/` | Visor ligado a un caso |
| `/guia/usuario.pdf` | Guía de usuario (PDF) |
| `/catalogo/procedimientos/<codigo>.pdf` | Ficha de procedimiento |
| `/export/excel/...` · `/import/excel/` | Intercambio Excel |
| `/media/<path>` | Archivos subidos |

---

## Estructura del repositorio

```text
Habitable-Fase2/
├── README.md                 ← este documento
├── .env.example              ← plantilla de entorno (sin secretos)
├── .gitignore
├── manage.py
├── requirements.txt
├── gunicorn.conf.py          ← bind 127.0.0.1:8000, timeout 300s
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── jazzmin_settings.py
├── inspecciones/             ← app de dominio
│   ├── models.py
│   ├── admin.py
│   ├── workflow.py
│   ├── partidas_catalogo.py
│   ├── management/commands/
│   ├── migrations/
│   └── ...
├── templates/
├── static/
└── entregables-revision/     ← HTML autocontenido para revisión
```

**No se versiona:** `.env`, `db.sqlite3`, `media/`, `staticfiles/`, `logs/`, llaves `.ppk`/`.pem`, archivos de credenciales de servidor.

---

## Despliegue local (desarrollo)

### 1. Clonar e instalar

```powershell
git clone https://github.com/angelccvea-hue/Habitable-Fase2.git
cd Habitable-Fase2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Editar `.env` (mínimo: `SECRET_KEY` propio, `DEBUG=1`).

### 2. Base de datos y datos base

```powershell
python manage.py migrate
python manage.py crear_roles_ejemplo
python manage.py cargar_franco_mar
```

Opcional — catálogo de partidas se siembra en migraciones / `asegurar_partidas_catalogo`.

### 3. Arrancar

```powershell
python manage.py runserver 0.0.0.0:8000
```

| URL | Uso |
|-----|-----|
| http://127.0.0.1:8000/admin/ | Entrar con superusuario local |
| http://127.0.0.1:8000/operacion/ | Tablero |
| http://127.0.0.1:8000/plano-metrado/ | Visor multi-planta (demo) |
| http://127.0.0.1:8000/api/health/ | Verificar proceso |

Crear superusuario si aún no existe:

```powershell
python manage.py createsuperuser
```

### 4. WeasyPrint en Windows

La generación de PDF puede fallar si faltan bibliotecas GTK/Pango. En ese caso:

- Preferir **WSL/Linux** para PDF, o
- Usar las rutas de fallback ya implementadas en las vistas de PDF.

El resto del sistema (admin, Excel, visor) funciona sin WeasyPrint.

---

## Despliegue en servidor (producción)

Arquitectura típica ya usada en el entorno CPEH Fase II:

```text
Internet → Apache/Nginx (TLS, proxy)
                → Gunicorn 127.0.0.1:8000  (gunicorn.conf.py)
                → Django + PostgreSQL
                → disco local media/ + staticfiles/
```

### 1. Código en el servidor

```bash
cd /ruta/apps
git clone https://github.com/angelccvea-hue/Habitable-Fase2.git fase2-rojo
cd fase2-rojo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Entorno producción

Crear `.env` (nunca en git):

```bash
SECRET_KEY=<clave-larga-aleatoria>
DEBUG=0
ALLOWED_HOSTS=<ip-o-dominio>,localhost,127.0.0.1
DATABASE_ENGINE=postgres
DB_NAME=fase2_rojo
DB_USER=fase2_app
DB_PASSWORD=<secreto>
DB_HOST=127.0.0.1
DB_PORT=5432
```

### 3. PostgreSQL

```bash
sudo -u postgres createuser fase2_app
sudo -u postgres createdb -O fase2_app fase2_rojo
# asignar password al rol
```

### 4. Migrar y estáticos

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser   # solo la primera vez
```

### 5. Gunicorn

```bash
source .venv/bin/activate
gunicorn -c gunicorn.conf.py config.wsgi:application
```

`gunicorn.conf.py` por defecto:

- `bind = 127.0.0.1:8000`
- `timeout = 300` (fichas pesadas / subidas)
- workers según CPU

### 6. Proxy inverso (ejemplo Apache)

- ProxyPass `/` → `http://127.0.0.1:8000/`
- TLS en el virtual host
- No hace falta servir `/static` aparte si WhiteNoise está activo tras `collectstatic`
- `/media/` lo atiende Django (ruta definida en `config/urls.py`)

### 7. systemd (esqueleto)

```ini
[Unit]
Description=CPEH Fase II
After=network.target postgresql.service

[Service]
User=cph
Group=cph
WorkingDirectory=/home/cph/apps/fase2-rojo
EnvironmentFile=/home/cph/apps/fase2-rojo/.env
ExecStart=/home/cph/apps/fase2-rojo/.venv/bin/gunicorn -c gunicorn.conf.py config.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now fase2-rojo
sudo systemctl status fase2-rojo
```

### 8. Actualizar versión

```bash
cd /ruta/fase2-rojo
git pull
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart fase2-rojo
curl -s http://127.0.0.1:8000/api/health/
```

---

## Datos semilla y comandos útiles

| Comando | Efecto |
|---------|--------|
| `python manage.py migrate` | Aplica esquema |
| `python manage.py crear_roles_ejemplo` | Usuarios/grupos demo |
| `python manage.py cargar_franco_mar` | Caso ejemplo **171818** Franco Mar (D3) |
| `python manage.py importar_ranking ...` | Precarga masiva desde Excel ranking (si se dispone del archivo) |
| `python manage.py cargar_informes_demolicion ...` | Adjunta/enriquece con PDF de informes |
| `python manage.py cargar_catalogo_procedimientos` | Catálogo de procedimientos |

HTML de revisión offline (multi-planta):  
`entregables-revision/PLN01-MET01-visor-multi-planta-revision-equipo.html`

---

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SECRET_KEY` | inseguro en código | Obligatorio cambiar en prod |
| `DEBUG` | `1` | `0` en producción |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts separados por coma |
| `DATABASE_ENGINE` | `sqlite` | `postgres` para producción |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | — | Solo si Postgres |

Plantilla: `.env.example`.

---

## Notas operativas

1. **Secretos:** no subir `.env`, dumps de BD con datos personales, ni documentos de credenciales de servidor.
2. **Respaldos:** en prod respaldar PostgreSQL + carpeta `media/`.
3. **Visor multi-planta:** requiere plantas en el caso (`PlantaInspeccion`) o usa demo PB/P1/P2 sin caso.
4. **Compatibilidad PDF:** WeasyPrint es más fiable en Linux; planificar el host de PDF en consecuencia.
5. **Licencia / uso:** uso interno del programa CPEH / Habitable. No publicar datos de casos reales sin autorización.

---

## Contacto del repositorio

- Organización/cuenta de publicación: `angelccvea-hue`
- Proyecto: **Habitable-Fase2**
