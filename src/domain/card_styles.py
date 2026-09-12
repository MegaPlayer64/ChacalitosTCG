"""
Módulo de Estilos y Paleta de Colores Elegante (Dark Mode) para Cartas de LBSB Engine.

Provee colores RGBA nativos de Kivy (0.0 a 1.0) para:
- Rarezas: Común, Especial, Épica, Excelencia, Ficha, Evento.
- Tipos de carta: Unit, Spell, Building (y Entorno).
- Funciones auxiliares para aplicar fondos y bordes redondeados al canvas de BoxLayout y otros Widgets.
"""

from kivy.graphics import Color, RoundedRectangle, Line

# =============================================================================
# 1. PALETAS COMPLETAS POR RAREZA (DARK MODE PREMIUM)
# =============================================================================
RARITY_PALETTES = {
    "Común": {
        # Carbón pizarra oscuro refinado con borde plata satinado
        "bg": (0.16, 0.18, 0.22, 0.95),
        "border": (0.45, 0.50, 0.58, 1.0),
        "header": (0.22, 0.25, 0.30, 0.95),
        "markup": "#9AA0A6",
        "name": "Común",
    },
    "Especial": {
        # Zafiro medianoche con resplandor cobalto luminoso
        "bg": (0.10, 0.19, 0.32, 0.95),
        "border": (0.28, 0.60, 0.95, 1.0),
        "header": (0.15, 0.28, 0.45, 0.95),
        "markup": "#4299E1",
        "name": "Especial",
    },
    "Épica": {
        # Amatista imperial oscuro con resplandor lavanda místico
        "bg": (0.22, 0.12, 0.32, 0.95),
        "border": (0.72, 0.38, 0.95, 1.0),
        "header": (0.32, 0.18, 0.46, 0.95),
        "markup": "#B870E8",
        "name": "Épica",
    },
    "Excelencia": {
        # Obsidiana ámbar con marco de oro dorado brillante
        "bg": (0.28, 0.22, 0.08, 0.95),
        "border": (0.96, 0.78, 0.22, 1.0),
        "header": (0.40, 0.30, 0.12, 0.95),
        "markup": "#F5C842",
        "name": "Excelencia",
    },
    "Ficha": {
        # Grafito táctico / cian ahumado industrial
        "bg": (0.13, 0.17, 0.20, 0.95),
        "border": (0.35, 0.65, 0.72, 1.0),
        "header": (0.18, 0.24, 0.28, 0.95),
        "markup": "#59A6B2",
        "name": "Ficha",
    },
    "Evento": {
        # Carmesí oscuro / rubí profundo con resplandor escarlata
        "bg": (0.30, 0.10, 0.14, 0.95),
        "border": (0.94, 0.28, 0.35, 1.0),
        "header": (0.42, 0.14, 0.20, 0.95),
        "markup": "#E84658",
        "name": "Evento",
    },
}

# =============================================================================
# 2. PALETAS POR TIPO DE CARTA (DARK MODE COMPLEMENTARIO)
# =============================================================================
CARD_TYPE_PALETTES = {
    "unit": {
        # Azul acero táctico
        "bg": (0.12, 0.20, 0.30, 0.95),
        "border": (0.32, 0.65, 0.95, 1.0),
        "header": (0.18, 0.28, 0.42, 0.95),
        "markup": "#4DA6F4",
        "name": "Unidad",
    },
    "spell": {
        # Violeta arcano / misterio
        "bg": (0.24, 0.12, 0.28, 0.95),
        "border": (0.78, 0.40, 0.90, 1.0),
        "header": (0.34, 0.18, 0.40, 0.95),
        "markup": "#C864E0",
        "name": "Hechizo",
    },
    "building": {
        # Esmeralda jade oscuro / naturaleza y baluartes
        "bg": (0.10, 0.24, 0.18, 0.95),
        "border": (0.30, 0.82, 0.55, 1.0),
        "header": (0.15, 0.35, 0.26, 0.95),
        "markup": "#4DD48C",
        "name": "Edificio / Entorno",
    },
    "fusion": {
        # Titanio oscuro con aura iridiscente
        "bg": (0.25, 0.25, 0.25, 0.95),
        "border": (0.85, 0.85, 0.85, 1.0),
        "header": (0.35, 0.35, 0.35, 0.95),
        "markup": "#A9A9FF",
        "name": "Fusión",
    },
}

# =============================================================================
# 3. DICCIONARIOS DIRECTOS RGBA (ACCESO RÁPIDO)
# =============================================================================
# Fondos directos por Rareza
RARITY_COLORS = {k: v["bg"] for k, v in RARITY_PALETTES.items()}

# Bordes / Acentos directos por Rareza
RARITY_BORDER_COLORS = {k: v["border"] for k, v in RARITY_PALETTES.items()}

# Fondos directos por Tipo de Carta
CARD_TYPE_COLORS = {k: v["bg"] for k, v in CARD_TYPE_PALETTES.items()}

# Bordes / Acentos directos por Tipo de Carta
CARD_TYPE_BORDER_COLORS = {k: v["border"] for k, v in CARD_TYPE_PALETTES.items()}

# Color por defecto para elementos no identificados (Dark Neutral)
DEFAULT_CARD_BG = (0.14, 0.16, 0.20, 0.95)
DEFAULT_CARD_BORDER = (0.38, 0.42, 0.48, 1.0)


# =============================================================================
# 4. FUNCIONES HELPER DE BÚSQUEDA Y NORMALIZACIÓN
# =============================================================================
def normalize_rarity_key(rarity: str) -> str:
    """Normaliza variantes textuales ('epica', 'Épica', 'comun', etc.)."""
    if not rarity:
        return "Común"
    raw = str(rarity).strip().lower()
    raw = raw.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    
    mapping = {
        "comun": "Común",
        "especial": "Especial",
        "epica": "Épica",
        "excelencia": "Excelencia",
        "ficha": "Ficha",
        "token": "Ficha",
        "evento": "Evento",
    }
    return mapping.get(raw, "Común")


def normalize_card_type_key(card_type: str) -> str:
    """Normaliza tipos de carta ('unit', 'unidad', 'spell', 'hechizo', 'building', 'entorno', etc.)."""
    if not card_type:
        return "unit"
    raw = str(card_type).strip().lower()
    
    if raw in ("unit", "unidad", "unidades", "personaje"):
        return "unit"
    if raw in ("spell", "hechizo", "truco", "magia"):
        return "spell"
    if raw in ("building", "edificio", "entorno", "environment", "estructura"):
        return "building"
    return "unit"


def get_rarity_color(rarity: str, mode: str = "bg") -> tuple:
    """
    Retorna el color RGBA correspondiente a la rareza.
    :param rarity: 'Común', 'Especial', 'Épica', 'Excelencia', 'Ficha', 'Evento'.
    :param mode: 'bg', 'border', 'header', 'markup'.
    """
    key = normalize_rarity_key(rarity)
    palette = RARITY_PALETTES.get(key, RARITY_PALETTES["Común"])
    return palette.get(mode, palette["bg"])


def get_card_type_color(card_type: str, mode: str = "bg") -> tuple:
    """
    Retorna el color RGBA correspondiente al tipo de carta.
    :param card_type: 'unit', 'spell', 'building'.
    :param mode: 'bg', 'border', 'header', 'markup'.
    """
    key = normalize_card_type_key(card_type)
    palette = CARD_TYPE_PALETTES.get(key, CARD_TYPE_PALETTES["unit"])
    return palette.get(mode, palette["bg"])


def get_rarity_markup(rarity: str) -> str:
    """Retorna etiqueta de marcado Kivy para texto, e.g. '[color=#F5C842]'."""
    hex_code = get_rarity_color(rarity, mode="markup")
    return f"[color={hex_code}]"


def get_card_type_markup(card_type: str) -> str:
    """Retorna etiqueta de marcado Kivy para texto por tipo, e.g. '[color=#C864E0]'."""
    hex_code = get_card_type_color(card_type, mode="markup")
    return f"[color={hex_code}]"


# =============================================================================
# 5. APLICADOR DE CANVAS PARA BOX LAYOUT Y WIDGETS DE KIVY
# =============================================================================
def apply_card_background(
    widget,
    bg_color=None,
    border_color=None,
    radius=(10, 10, 10, 10),
    border_width=1.5,
    with_border=True,
    rarity=None,
    card_type=None,
):
    """
    Aplica de forma elegante un fondo de color y borde redondeado al canvas.before
    de cualquier BoxLayout o Widget de Kivy, vinculando automáticamente los cambios
    de tamaño (`size`) y posición (`pos`) del widget.

    Permite pasar directamente tuplas RGBA o bien indicar `rarity` o `card_type`.

    :param widget: Instancia de BoxLayout, Widget, etc.
    :param bg_color: Tupla RGBA (r, g, b, a) con valores de 0.0 a 1.0.
    :param border_color: Tupla RGBA para el borde exterior redondeado.
    :param radius: Radio de redondeo de las esquinas, e.g. [10, 10, 10, 10].
    :param border_width: Grosor del trazo del borde en píxeles.
    :param with_border: Booleano para activar o desactivar el trazado del borde.
    :param rarity: Nombre de la rareza si se desea derivar el color automáticamente.
    :param card_type: Nombre del tipo de carta si se desea derivar el color.
    """
    # 1. Determinar color de fondo si no se pasó explícito
    if bg_color is None:
        if rarity is not None:
            bg_color = get_rarity_color(rarity, mode="bg")
        elif card_type is not None:
            bg_color = get_card_type_color(card_type, mode="bg")
        else:
            bg_color = DEFAULT_CARD_BG

    # 2. Determinar color de borde si no se pasó explícito
    if border_color is None and with_border:
        if rarity is not None:
            border_color = get_rarity_color(rarity, mode="border")
        elif card_type is not None:
            border_color = get_card_type_color(card_type, mode="border")
        else:
            border_color = DEFAULT_CARD_BORDER

    # Normalizar radio
    if isinstance(radius, (int, float)):
        radius = [radius, radius, radius, radius]
    elif not isinstance(radius, (list, tuple)):
        radius = [10, 10, 10, 10]
    else:
        radius = list(radius)

    # 3. Si el widget ya tenía canvas configurado por esta función, sólo actualizamos
    if getattr(widget, "_card_canvas_initialized", False):
        if hasattr(widget, "_card_bg_color_instruction"):
            widget._card_bg_color_instruction.rgba = bg_color
        if hasattr(widget, "_card_border_color_instruction") and border_color:
            widget._card_border_color_instruction.rgba = border_color
        widget._card_radius = radius
        widget._card_border_width = border_width
        
        # Sincronizar geometría actual
        if hasattr(widget, "_card_bg_rect"):
            widget._card_bg_rect.pos = widget.pos
            widget._card_bg_rect.size = widget.size
            widget._card_bg_rect.radius = radius
        if hasattr(widget, "_card_border_line"):
            r_val = radius[0] if radius else 10
            widget._card_border_line.rounded_rectangle = [
                widget.pos[0], widget.pos[1], widget.size[0], widget.size[1], r_val
            ]
        return widget

    # 4. Inicialización en canvas.before
    with widget.canvas.before:
        widget._card_bg_color_instruction = Color(*bg_color)
        widget._card_bg_rect = RoundedRectangle(
            pos=widget.pos,
            size=widget.size,
            radius=radius
        )
        if with_border and border_color:
            widget._card_border_color_instruction = Color(*border_color)
            r_val = radius[0] if radius else 10
            widget._card_border_line = Line(
                rounded_rectangle=[
                    widget.pos[0], widget.pos[1], widget.size[0], widget.size[1], r_val
                ],
                width=border_width
            )
        else:
            widget._card_border_color_instruction = None
            widget._card_border_line = None

    widget._card_radius = radius
    widget._card_border_width = border_width
    widget._card_canvas_initialized = True

    # 5. Vinculación a eventos de redimensionamiento y movimiento
    def _actualizar_geometria(inst, _val):
        if hasattr(inst, "_card_bg_rect") and inst._card_bg_rect:
            inst._card_bg_rect.pos = inst.pos
            inst._card_bg_rect.size = inst.size
        if hasattr(inst, "_card_border_line") and inst._card_border_line:
            r = inst._card_radius[0] if inst._card_radius else 10
            inst._card_border_line.rounded_rectangle = [
                inst.pos[0], inst.pos[1], inst.size[0], inst.size[1], r
            ]

    widget.bind(pos=_actualizar_geometria, size=_actualizar_geometria)
    return widget


def apply_card_theme(widget, rarity=None, card_type=None, radius=(10, 10, 10, 10), border_width=1.5, **kwargs):
    """Soporta tanto rareza/tipo como colores RGBA directos pasados por kwargs."""
    return apply_card_background(
        widget=widget,
        rarity=rarity,
        card_type=card_type,
        radius=radius,
        border_width=border_width,
        with_border=True,
        **kwargs
    )