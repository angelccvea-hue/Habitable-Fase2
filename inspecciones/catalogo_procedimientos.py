"""Catálogo de procedimientos de reparación (referencia técnica VIG / COL / MAM)."""

PROCEDIMIENTOS_INICIALES: list[dict[str, str]] = [
    {
        "codigo": "VIG-01",
        "categoria": "VIG",
        "titulo": "Inyección estructural de fisuras en vigas",
        "descripcion": "Inyección de resina o lechada en fisuras de flexión o corte en vigas con daño leve a moderado.",
    },
    {
        "codigo": "VIG-02",
        "categoria": "VIG",
        "titulo": "Reparación localizada de recubrimiento en vigas",
        "descripcion": "Restitución de recubrimiento y protección en zonas con pérdida localizada del hormigón.",
    },
    {
        "codigo": "VIG-03",
        "categoria": "VIG",
        "titulo": "Reconstrucción de rótula plástica",
        "descripcion": "Reparación de nudos con formación de rótula plástica bajo descarga diseñada.",
    },
    {
        "codigo": "VIG-04",
        "categoria": "VIG",
        "titulo": "Reconstrucción de núcleo en vigas",
        "descripcion": "Sustitución o reconstrucción del núcleo comprimido con confinamiento adecuado.",
    },
    {
        "codigo": "COL-01",
        "categoria": "COL",
        "titulo": "Sellado y protección superficial en columnas",
        "descripcion": "Tratamiento de fisuras superficiales y protección anticorrosiva.",
    },
    {
        "codigo": "COL-02",
        "categoria": "COL",
        "titulo": "Inyección estructural en columnas",
        "descripcion": "Inyección de resina o lechada en fisuras diagonales o longitudinales.",
    },
    {
        "codigo": "COL-03",
        "categoria": "COL",
        "titulo": "Reparación localizada de recubrimiento en columnas",
        "descripcion": "Reparación parcial del recubrimiento con mortero estructural o equivalente.",
    },
    {
        "codigo": "COL-04",
        "categoria": "COL",
        "titulo": "Reconstrucción equivalente bajo descarga diseñada",
        "descripcion": "Reconstrucción de sección de columna con apuntalamiento y descarga calculada.",
    },
    {
        "codigo": "COL-05",
        "categoria": "COL",
        "titulo": "Refuerzo o encamisado de columnas",
        "descripcion": "Encamisado, confinamiento o refuerzo externo para recuperar capacidad portante.",
    },
    {
        "codigo": "COL-CRIT",
        "categoria": "COL",
        "titulo": "Condición crítica — fuera de alcance de reparación",
        "descripcion": "Aplastamiento, pandeo de barras, núcleo triturado u otros mecanismos fuera de COL-01 a COL-04.",
    },
    {
        "codigo": "MAM-01",
        "categoria": "MAM",
        "titulo": "Reparación no estructural de fisuras leves",
        "descripcion": "Sellado de fisuras en mampostería o tabiques no estructurales.",
    },
    {
        "codigo": "MAM-02",
        "categoria": "MAM",
        "titulo": "Inyección estructural en mampostería",
        "descripcion": "Inyección de fisuras y grietas moderadas en muros de arriostre o mampostería.",
    },
    {
        "codigo": "MAM-03",
        "categoria": "MAM",
        "titulo": "Reconstrucción localizada (llaveado y costura)",
        "descripcion": "Reconstrucción parcial de paños con llaveado y costura estructural.",
    },
    {
        "codigo": "MAM-04",
        "categoria": "MAM",
        "titulo": "Sustitución por tabiquería liviana sismorresistente",
        "descripcion": "Reemplazo de mampostería dañada en rutas de evacuación por sistema liviano.",
    },
    {
        "codigo": "PLN-01",
        "categoria": "OTRO",
        "titulo": "Plano de inspección estructural en planta (sistema de ejes) — borrador",
        "descripcion": (
            "Protocolo propuesto: plano de inspección (no croquis libre) con matriz "
            "de ejes letra×número, inclusive plantas irregulares. Descargar ficha PDF PLN-01."
        ),
    },
]


def asegurar_procedimientos_catalogo() -> int:
    """Crea/actualiza procedimientos semilla. Devuelve cuántos se crearon."""
    from inspecciones.models import Procedimiento

    n = 0
    for item in PROCEDIMIENTOS_INICIALES:
        _, created = Procedimiento.objects.update_or_create(
            codigo=item["codigo"],
            defaults={
                "categoria": item["categoria"],
                "titulo": item["titulo"],
                "descripcion": item.get("descripcion", ""),
                "activo": True,
            },
        )
        if created:
            n += 1
    return n


def listar_procedimientos_ayuda(*, limite: int | None = None) -> list[dict[str, str]]:
    """Lista activa para wizards / Excel (fallback a semilla si BD vacía).

    Orden de categorías como en Excel: COL → MAM → VIG.
    """
    order_cat = {"COL": 0, "MAM": 1, "VIG": 2, "OTRO": 3}

    def _sort_key(row: dict) -> tuple:
        cat = (row.get("categoria") or "").upper()
        return (order_cat.get(cat, 9), row.get("codigo") or "")

    try:
        from django.apps import apps

        if apps.ready:
            from inspecciones.models import Procedimiento

            qs = Procedimiento.objects.filter(activo=True)
            rows = [
                {
                    "codigo": p.codigo,
                    "categoria": p.categoria,
                    "titulo": p.titulo,
                    "descripcion": p.descripcion or "",
                }
                for p in qs
            ]
            rows.sort(key=_sort_key)
            if limite:
                rows = rows[:limite]
            if rows:
                return rows
    except Exception:
        pass
    rows = sorted(PROCEDIMIENTOS_INICIALES, key=_sort_key)
    if limite:
        rows = rows[:limite]
    return rows
