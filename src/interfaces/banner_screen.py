import json
import os
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from src.domain.audio_manager import AudioManager
from src.domain.gacha_system import GachaSystem
from src.infrastructure.loaders.card_loader import CardLoader
from src.infrastructure.path_manager import PathManager


# Paleta visual unificada por rareza y tipo
COLORES_RAREZA = {
    "Excelencia": (0.85, 0.62, 0.12, 1),  # Dorado brillante
    "Épica": (0.58, 0.24, 0.72, 1),       # Púrpura épico
    "Especial": (0.16, 0.50, 0.76, 1),    # Azul especial
    "Común": (0.32, 0.36, 0.42, 1),       # Gris pizarra
}

HEX_RAREZA = {
    "Excelencia": "FFD54F",
    "Épica": "CE93D8",
    "Especial": "4FC3F7",
    "Común": "CFD8DC",
}


def extraer_datos_carta(carta) -> dict:
    """Normaliza los atributos de una carta sin importar si el loader usa inglés o español."""
    cid = str(getattr(carta, "id", "?"))
    nombre = getattr(carta, "name", None) or getattr(carta, "nombre", f"Carta #{cid}")
    rareza = getattr(carta, "rarity", None) or getattr(carta, "rareza", "Común")
    coste = getattr(carta, "cost", None)
    if coste is None:
        coste = getattr(carta, "coste", 0)

    tipo_raw = getattr(carta, "card_type", None) or getattr(carta, "tipo", None)
    if not tipo_raw:
        tipo_raw = "unit" if hasattr(carta, "attack") or hasattr(carta, "ataque") else "spell"

    vida = getattr(carta, "hp", None) or getattr(carta, "health", None) or getattr(carta, "vida", 0)
    ataque = getattr(carta, "attack", None) if hasattr(carta, "attack") else getattr(carta, "ataque", 0)
    velocidad = getattr(carta, "speed", None) if hasattr(carta, "speed") else getattr(carta, "velocidad", 0)
    rango = (
        getattr(carta, "range", None)
        or getattr(carta, "attack_range", None)
        or getattr(carta, "rango_ataque", 1)
    )
    descripcion = (
        getattr(carta, "description", None)
        or getattr(carta, "ability", None)
        or getattr(carta, "descripcion", None)
        or "Sin habilidad especial."
    )

    raw_grupos = (
        getattr(carta, "groups", None)
        or getattr(carta, "grupos", None)
        or getattr(carta, "Grupos", "")
    )
    if isinstance(raw_grupos, (list, tuple, set)):
        grupos_str = ", ".join(str(g) for g in raw_grupos if str(g).strip() and str(g).strip() != "-")
    else:
        grupos_str = str(raw_grupos).strip()
        if grupos_str in {"-", "None", "nan"}:
            grupos_str = ""

    return {
        "id": cid,
        "nombre": nombre,
        "rareza": rareza,
        "coste": coste,
        "tipo": tipo_raw,
        "vida": vida,
        "ataque": ataque,
        "velocidad": velocidad,
        "rango": rango,
        "descripcion": str(descripcion),
        "grupos": grupos_str if grupos_str else "Sin grupo (Universal)",
    }


class PopupDetalleCarta(ModalView):
    """Ventana modal para inspeccionar estadísticas, grupos, habilidad y tasas de una carta."""

    def __init__(self, carta, copias_actuales=0, tasa_info=None, **kwargs):
        super().__init__(size_hint=(0.78, 0.80), auto_dismiss=True, **kwargs)
        datos = extraer_datos_carta(carta)
        rareza = datos["rareza"]
        color_cabecera = COLORES_RAREZA.get(rareza, (0.2, 0.3, 0.4, 1))
        hex_r = HEX_RAREZA.get(rareza, "FFFFFF")

        contenedor = BoxLayout(orientation="vertical", padding=18, spacing=12)
        with contenedor.canvas.before:
            Color(0.11, 0.13, 0.18, 0.98)
            self._bg = RoundedRectangle(pos=contenedor.pos, size=contenedor.size, radius=[14])
        contenedor.bind(
            pos=lambda inst, val: setattr(self._bg, "pos", val),
            size=lambda inst, val: setattr(self._bg, "size", val),
        )

        # Cabecera con nombre y rareza
        cabecera = BoxLayout(orientation="vertical", size_hint_y=None, height=74, padding=10)
        with cabecera.canvas.before:
            Color(*color_cabecera)
            self._hdr_bg = RoundedRectangle(pos=cabecera.pos, size=cabecera.size, radius=[10])
        cabecera.bind(
            pos=lambda inst, val: setattr(self._hdr_bg, "pos", val),
            size=lambda inst, val: setattr(self._hdr_bg, "size", val),
        )

        tipo_legible = {"unit": "Unidad", "spell": "Truco", "building": "Entorno"}.get(
            datos["tipo"], datos["tipo"].capitalize()
        )
        lbl_titulo = Label(
            text=f"[b]#{datos['id']} · {datos['nombre']}[/b]\n[{rareza.upper()} · {tipo_legible}]",
            markup=True,
            font_size="18sp",
            halign="center",
            valign="middle",
        )
        lbl_titulo.bind(size=lbl_titulo.setter("text_size"))
        cabecera.add_widget(lbl_titulo)
        contenedor.add_widget(cabecera)

        # Barra de estadísticas según tipo de carta
        if datos["tipo"] == "unit":
            texto_stats = (
                f"⚡ Coste: [b]{datos['coste']}[/b]   |   "
                f"❤️ Vida: [b]{int(float(datos['vida']))}[/b]   |   "
                f"⚔️ Ataque: [b]{int(float(datos['ataque']))}[/b]   |   "
                f"👟 Vel: [b]{int(float(datos['velocidad']))}[/b]   |   "
                f"🎯 Rango: [b]{int(float(datos['rango']))}[/b]"
            )
        else:
            texto_stats = f"⚡ Coste de Energía: [b]{datos['coste']}[/b]   |   Categoría: [b]{tipo_legible}[/b]"

        lbl_stats = Label(text=texto_stats, markup=True, font_size="15sp", size_hint_y=None, height=34)
        contenedor.add_widget(lbl_stats)

        # Grupos / Etiquetas
        lbl_grupos = Label(
            text=f"[color=90CAF9][b]Grupos:[/b][/color] {datos['grupos']}",
            markup=True,
            font_size="14sp",
            size_hint_y=None,
            height=34,
            halign="center",
        )
        lbl_grupos.bind(size=lbl_grupos.setter("text_size"))
        contenedor.add_widget(lbl_grupos)

        # Descripción / Habilidad en ScrollView
        scroll_desc = ScrollView(size_hint=(1, 1))
        lbl_desc = Label(
            text=f"[b]Habilidad Especial:[/b]\n\n{datos['descripcion']}",
            markup=True,
            font_size="15sp",
            halign="left",
            valign="top",
            size_hint_y=None,
            padding=(12, 10),
        )
        lbl_desc.bind(
            width=lambda inst, w: setattr(inst, "text_size", (w - 24, None)),
            texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1] + 20, 90)),
        )
        scroll_desc.add_widget(lbl_desc)
        contenedor.add_widget(scroll_desc)

        # Pie informativo: copias en inventario y tasa en el banner activo
        info_extra = [f"📦 En tu inventario: [b]{copias_actuales}/4 copias[/b]"]
        if tasa_info:
            tag_dest = "  [color=FFD54F]★ DESTACADA (2x)[/color]" if tasa_info["destacada"] else ""
            info_extra.append(
                f"🎲 Probabilidad ({tasa_info['banner_nombre']}): "
                f"[color={hex_r}][b]{tasa_info['std_pct']:.2f}%[/b][/color] normal"
                + (
                    f"  |  [color={hex_r}][b]{tasa_info['s5_pct']:.2f}%[/b][/color] Slot 5"
                    if tasa_info["s5_pct"] > 0
                    else ""
                )
                + tag_dest
            )

        lbl_footer = Label(
            text="\n".join(info_extra),
            markup=True,
            font_size="13sp",
            size_hint_y=None,
            height=48,
            halign="center",
        )
        lbl_footer.bind(size=lbl_footer.setter("text_size"))
        contenedor.add_widget(lbl_footer)

        btn_cerrar = Button(
            text="Cerrar",
            size_hint=(0.45, None),
            height=44,
            pos_hint={"center_x": 0.5},
            background_color=(0.75, 0.25, 0.25, 1),
        )
        btn_cerrar.bind(on_release=lambda x: self.dismiss())
        contenedor.add_widget(btn_cerrar)

        self.add_widget(contenedor)


class PopupPoolBanner(ModalView):
    """Previsualización interactiva de todas las cartas y probabilidades del banner."""

    ORDEN_RAREZA = {"Excelencia": 0, "Épica": 1, "Especial": 2, "Común": 3}

    def __init__(self, banner_cfg, pool_banner, ids_destacadas, permitir_excelencias, inventario, **kwargs):
        super().__init__(size_hint=(0.88, 0.88), auto_dismiss=True, **kwargs)
        self.banner_cfg = banner_cfg
        self.pool_banner = pool_banner
        self.ids_destacadas = ids_destacadas
        self.permitir_excelencias = permitir_excelencias
        self.inventario = inventario
        self.filtro_actual = "TODAS"

        self.tasas = self._calcular_tasas()

        root = BoxLayout(orientation="vertical", padding=16, spacing=10)
        with root.canvas.before:
            Color(0.10, 0.12, 0.16, 0.98)
            self._bg = RoundedRectangle(pos=root.pos, size=root.size, radius=[14])
        root.bind(
            pos=lambda inst, val: setattr(self._bg, "pos", val),
            size=lambda inst, val: setattr(self._bg, "size", val),
        )

        # Título y resumen de tasas globales por rareza
        if permitir_excelencias:
            resumen_tasas = (
                f"[b]📋 Pool de {banner_cfg['nombre']} ({len(pool_banner)} cartas)[/b]\n"
                "[size=13sp]Tiros 1–4: [color=CFD8DC]Común 70%[/color] · [color=4FC3F7]Especial 20%[/color] · "
                "[color=CE93D8]Épica 8%[/color] · [color=FFD54F]Excelencia 2%[/color]   |   "
                "Slot 5: [color=4FC3F7]65%[/color] / [color=CE93D8]25%[/color] / [color=FFD54F]10%[/color][/size]"
            )
        else:
            resumen_tasas = (
                f"[b]🎟️ Pool de {banner_cfg['nombre']} ({len(pool_banner)} cartas)[/b]\n"
                "[size=13sp]Tiros 1–4: [color=CFD8DC]Común 72%[/color] · [color=4FC3F7]Especial 20%[/color] · "
                "[color=CE93D8]Épica 8%[/color] · [color=FF8A80]Excelencia 0%[/color]   |   "
                "Slot 5: [color=4FC3F7]Especial 75%[/color] / [color=CE93D8]Épica 25%[/color][/size]"
            )

        lbl_header = Label(text=resumen_tasas, markup=True, font_size="17sp", halign="center", size_hint_y=None, height=62)
        lbl_header.bind(size=lbl_header.setter("text_size"))
        root.add_widget(lbl_header)

        # Barra de filtros
        barra_filtros = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=None, height=38)
        filtros = [
            ("TODAS", "Todas"),
            ("DESTACADAS", "★ Destacadas"),
            ("Excelencia", "Excelencia"),
            ("Épica", "Épica"),
            ("Especial", "Especial"),
            ("Común", "Común"),
        ]
        self.botones_filtro = {}
        for clave_f, texto_f in filtros:
            if clave_f == "Excelencia" and not permitir_excelencias:
                continue
            btn_f = Button(text=texto_f, font_size="13sp", background_color=(0.25, 0.30, 0.38, 1))
            btn_f.bind(on_release=lambda inst, f=clave_f: self._aplicar_filtro(f))
            self.botones_filtro[clave_f] = btn_f
            barra_filtros.add_widget(btn_f)
        root.add_widget(barra_filtros)

        # Lista scrollable de cartas del banner
        self.scroll = ScrollView(size_hint=(1, 1))
        self.lista_layout = GridLayout(cols=1, spacing=6, size_hint_y=None, padding=(4, 4))
        self.lista_layout.bind(minimum_height=self.lista_layout.setter("height"))
        self.scroll.add_widget(self.lista_layout)
        root.add_widget(self.scroll)

        # Pie con instrucción y botón cerrar
        footer = BoxLayout(orientation="horizontal", size_hint_y=None, height=44, spacing=12)
        lbl_tip = Label(
            text="💡 Haz clic en cualquier carta para ver sus atributos y habilidad",
            font_size="13sp",
            color=(0.8, 0.85, 0.9, 1),
            halign="left",
        )
        lbl_tip.bind(size=lbl_tip.setter("text_size"))
        btn_cerrar = Button(
            text="Volver al Banner",
            size_hint_x=0.32,
            background_color=(0.75, 0.25, 0.25, 1),
        )
        btn_cerrar.bind(on_release=lambda x: self.dismiss())
        footer.add_widget(lbl_tip)
        footer.add_widget(btn_cerrar)
        root.add_widget(footer)

        self.add_widget(root)
        self._aplicar_filtro("TODAS")

    def _calcular_tasas(self) -> dict:
        if self.permitir_excelencias:
            probs_std = {"Común": 0.70, "Especial": 0.20, "Épica": 0.08, "Excelencia": 0.02}
            probs_s5 = {"Común": 0.0, "Especial": 0.65, "Épica": 0.25, "Excelencia": 0.10}
        else:
            probs_std = {"Común": 0.72, "Especial": 0.20, "Épica": 0.08, "Excelencia": 0.0}
            probs_s5 = {"Común": 0.0, "Especial": 0.75, "Épica": 0.25, "Excelencia": 0.0}

        por_rareza = {}
        for c in self.pool_banner:
            r = getattr(c, "rarity", "Común")
            por_rareza.setdefault(r, []).append(c)

        tasas = {}
        mult = 2.0
        for r, cartas in por_rareza.items():
            peso_total = sum(mult if str(c.id) in self.ids_destacadas else 1.0 for c in cartas)
            for c in cartas:
                cid = str(c.id)
                es_dest = cid in self.ids_destacadas
                frac = (mult if es_dest else 1.0) / peso_total
                tasas[cid] = {
                    "std_pct": probs_std.get(r, 0.0) * frac * 100.0,
                    "s5_pct": probs_s5.get(r, 0.0) * frac * 100.0,
                    "destacada": es_dest,
                    "banner_nombre": self.banner_cfg["nombre"],
                }
        return tasas

    def _aplicar_filtro(self, filtro):
        self.filtro_actual = filtro
        for clave, btn in self.botones_filtro.items():
            btn.background_color = (0.20, 0.55, 0.75, 1) if clave == filtro else (0.25, 0.30, 0.38, 1)

        self.lista_layout.clear_widgets()

        filtradas = []
        for c in self.pool_banner:
            cid = str(c.id)
            r = getattr(c, "rarity", "Común")
            if filtro == "TODAS":
                filtradas.append(c)
            elif filtro == "DESTACADAS" and cid in self.ids_destacadas:
                filtradas.append(c)
            elif r == filtro:
                filtradas.append(c)

        # Ordenar: Destacadas primero -> Rareza mayor a menor -> ID numérico
        filtradas.sort(
            key=lambda c: (
                0 if str(c.id) in self.ids_destacadas else 1,
                self.ORDEN_RAREZA.get(getattr(c, "rarity", "Común"), 9),
                int(c.id),
            )
        )

        if not filtradas:
            self.lista_layout.add_widget(
                Label(text="No hay cartas en esta categoría para este sobre.", size_hint_y=None, height=50)
            )
            return

        for carta in filtradas:
            datos = extraer_datos_carta(carta)
            cid = datos["id"]
            rareza = datos["rareza"]
            tasa = self.tasas.get(cid, {"std_pct": 0.0, "s5_pct": 0.0, "destacada": False})
            copias = self.inventario.get(cid, 0)

            estrella = "★ " if tasa["destacada"] else ""
            slot5_txt = f"  |  Slot 5: {tasa['s5_pct']:.2f}%" if tasa["s5_pct"] > 0 else ""
            texto_fila = (
                f"{estrella}#{cid}  {datos['nombre']}   [{rareza}]   "
                f"(Tiro normal: {tasa['std_pct']:.2f}%{slot5_txt})   ·   Inv: {copias}/4"
            )

            color_btn = COLORES_RAREZA.get(rareza, (0.3, 0.35, 0.4, 1))
            btn_fila = Button(
                text=texto_fila,
                size_hint_y=None,
                height=44,
                font_size="13sp",
                background_color=color_btn,
                halign="left",
                valign="middle",
                padding=(12, 0),
            )
            btn_fila.bind(size=btn_fila.setter("text_size"))
            btn_fila.bind(
                on_release=lambda inst, c_obj=carta, cp=copias, t_inf=tasa: PopupDetalleCarta(
                    c_obj, copias_actuales=cp, tasa_info=t_inf
                ).open()
            )
            self.lista_layout.add_widget(btn_fila)


class TarjetaRevelada(BoxLayout):
    """Componente visual clicable para representar cada carta obtenida."""

    def __init__(self, carta, es_nueva=False, on_ver_detalle=None, ancho=160, **kwargs):
        super().__init__(orientation="vertical", padding=4, spacing=4, size_hint_x=None, width=ancho, **kwargs)
        datos = extraer_datos_carta(carta)
        rareza = datos["rareza"]
        tipo = datos["tipo"]

        color_fondo = COLORES_RAREZA.get(rareza, (0.2, 0.4, 0.6, 1))
        tipo_badge = {"unit": "Unidad", "spell": "Truco", "building": "Entorno"}.get(tipo, tipo)
        etiqueta_nueva = "🆕 ¡NUEVA!\n" if es_nueva else ""

        if tipo == "unit":
            resumen_stats = f"⚡{datos['coste']}  ❤️{int(float(datos['vida']))}  ⚔️{int(float(datos['ataque']))}"
        else:
            resumen_stats = f"⚡ Coste: {datos['coste']}"

        btn_carta = Button(
            text=f"{etiqueta_nueva}{datos['nombre']}\n\n{resumen_stats}\n[{rareza} · {tipo_badge}]\n(Clic: detalle)",
            background_color=color_fondo,
            halign="center",
            valign="middle",
            font_size="13sp",
        )
        btn_carta.bind(size=btn_carta.setter("text_size"))
        if on_ver_detalle:
            btn_carta.bind(on_release=lambda inst: on_ver_detalle(carta))
        self.add_widget(btn_carta)


class PantallaBanner(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ruta_perfil = PathManager.get_user_profile_path()
        self.perfil_cache = {}
        self.cartas_colectables = []

        # --- CATÁLOGO COMPLETO DE BANNERS (Sincronizado con GachaSystem) ---
        self.lista_banners = [
            {
                "id": "SIMCE",
                "nombre": "Copa SIMCE & Patio",
                "desc": "¡La evaluación nacional comienza!\nChino (Quemadas), Dante (Olimpiadas) y Yotnier & Joel (Quemadores) lideran el patio.",
                "coste_1": 100,
                "coste_5": 500,
                "pago_con_ticket": False,
                "imagen": "src/art/facciones_png/logo-simce.png",
            },
            {
                "id": "ALIANZAS",
                "nombre": "Crónicas de Alianzas",
                "desc": "¡Alianzas III y IV se enfrentan!\nDragón Menor, Rin (Rey), Ami (Reina) y las fusiones de alianza entran al tablero.",
                "coste_1": 100,
                "coste_5": 500,
                "pago_con_ticket": False,
                "imagen": "src/art/facciones_png/logo-alainzas3ro.png",
            },
            {
                "id": "HALLOWEEN",
                "nombre": "Noche de Brujas",
                "desc": "¡Terror y misterio en el liceo!\nAriana & Camila (Club de Pelea), Margarita (Vampira), Ami (Pesadillas) e Isidora.",
                "coste_1": 100,
                "coste_5": 500,
                "pago_con_ticket": False,
                "imagen": "src/art/facciones_png/logo-halloween.png",
            },
            {
                "id": "FERIA_LIBRO",
                "nombre": "Feria del Libro",
                "desc": "¡Cultura, ciencia y literatura!\nJoel (Hombre Arácnido), Rafa (Chamán), Helen (Científica) y Margaret (Circe).",
                "coste_1": 100,
                "coste_5": 500,
                "pago_con_ticket": False,
                "imagen": "src/art/facciones_png/logo-ferialibro.png",
            },
            {
                "id": "GALAS",
                "nombre": "Gran Gala & Destacados",
                "desc": "¡Noche de gala y ceremonia!\nDante (Destacado Académico), Helen (Jazz Star), Licenciatura y Competencia Internacional.",
                "coste_1": 100,
                "coste_5": 500,
                "pago_con_ticket": False,
                "imagen": "src/art/facciones_png/logo-galas.png",
            },
            {
                "id": "RAICES",
                "nombre": "La Tirana & Raíces",
                "desc": "¡Tradición, Caporal y Clan Mish-A!\nEmi & Richi (Demonios), Martina & Rin (Ángeles) y Cristóbal & Josefa (Caporal).",
                "coste_1": 100,
                "coste_5": 500,
                "pago_con_ticket": False,
                "imagen": "src/art/facciones_png/logo-raices.png",
            },
            {
                "id": "JURASICO",
                "nombre": "Era Jurásica & Clandestinos",
                "desc": "¡Dinosaurios y mercado clandestino!\nCrisby (Dinosaurio), Dante (Dinosaurio), Yotnier y Recinto Militar.",
                "coste_1": 100,
                "coste_5": 500,
                "pago_con_ticket": False,
                "imagen": "src/art/facciones_png/logo-jurasico.png",
            },
            {
                "id": "GENERAL",
                "nombre": "Sobre General",
                "desc": "Colección estándar con las 153 cartas colectables disponibles sin Rate Up específico.",
                "coste_1": 100,
                "coste_5": 500,
                "pago_con_ticket": False,
                "imagen": "src/art/facciones_png/logo-general.png",
            },
            {
                "id": "MASTER_PACK",
                "nombre": "Master Pack (Tickets)",
                "desc": "¡Popurrí gratuito con 1 Ticket! Reúne 26 cartas Especiales y Épicas destacadas (sin Excelencias).",
                "coste_ticket": 1,
                "pago_con_ticket": True,
                "imagen": "src/art/facciones_png/ticket.png",
            },
        ]
        self.banner_actual = self.lista_banners[0]
        self.botones_banners = {}

        # Estado de revelación 1 a 1
        self._cola_revelacion = []
        self._indice_revelacion = 0
        self._nuevas_en_tirada = set()

        # --- LAYOUT PRINCIPAL ---
        layout_principal = BoxLayout(orientation="horizontal")

        # ==========================================
        # PANEL IZQUIERDO: SELECCIÓN DE BANNERS Y MENÚ
        # ==========================================
        panel_izquierdo = BoxLayout(orientation="vertical", size_hint_x=0.26, padding=10, spacing=10)

        lbl_titulo_banners = Label(text="BANNERS", font_size="18sp", bold=True, size_hint_y=None, height=40)
        panel_izquierdo.add_widget(lbl_titulo_banners)

        scroll_banners = ScrollView(size_hint=(1, 1))
        lista_botones_banners = BoxLayout(orientation="vertical", size_hint_y=None, spacing=8)
        lista_botones_banners.bind(minimum_height=lista_botones_banners.setter("height"))

        for banner in self.lista_banners:
            prefijo = "🎟️ " if banner.get("pago_con_ticket") else ""
            btn_banner = Button(
                text=f"{prefijo}{banner['nombre']}",
                size_hint_y=None,
                height=52,
                font_size="13sp",
                halign="center",
                valign="middle",
            )
            btn_banner.bind(size=btn_banner.setter("text_size"))
            btn_banner.bind(on_release=lambda instance, b=banner: self.cambiar_banner_activo(b))
            self.botones_banners[banner["id"]] = btn_banner
            lista_botones_banners.add_widget(btn_banner)

        scroll_banners.add_widget(lista_botones_banners)
        panel_izquierdo.add_widget(scroll_banners)

        btn_tienda = Button(
            text="Ir a Tienda 🛒",
            size_hint_y=None,
            height=46,
            background_color=(0.8, 0.5, 0.1, 1),
        )
        btn_tienda.bind(on_release=lambda x: self.cambiar_a_tienda())
        panel_izquierdo.add_widget(btn_tienda)

        btn_volver = Button(
            text="Volver al Menú",
            size_hint_y=None,
            height=46,
            background_color=(0.7, 0.2, 0.2, 1),
        )
        btn_volver.bind(on_release=lambda x: self.cambiar_a_menu())
        panel_izquierdo.add_widget(btn_volver)

        # ==========================================
        # PANEL DERECHO: VISUALIZACIÓN Y GACHA
        # ==========================================
        self.panel_derecho = BoxLayout(orientation="vertical", size_hint_x=0.74, padding=18, spacing=12)

        # Barra superior (Monedas + Tickets)
        self.lbl_recursos = Label(
            text="🪙 Monedas: --   |   🎟️ Tickets: --",
            font_size="18sp",
            bold=True,
            size_hint_y=0.08,
            halign="right",
        )
        self.lbl_recursos.bind(size=self.lbl_recursos.setter("text_size"))
        self.panel_derecho.add_widget(self.lbl_recursos)

        # Zona central para arte, previsualización o revelación
        self.zona_central = BoxLayout(orientation="vertical", size_hint_y=0.74, spacing=8)
        self.panel_derecho.add_widget(self.zona_central)

        # Botonera de Tiros
        self.layout_botones_tiro = BoxLayout(orientation="horizontal", spacing=20, size_hint_y=0.18)

        self.btn_tirar_1 = Button(text="Tirar x1\n(-- 🪙)", font_size="16sp", background_color=(0.3, 0.7, 0.8, 1))
        self.btn_tirar_1.bind(on_release=lambda x: self.realizar_tiro(cantidad=1))

        self.btn_tirar_5 = Button(
            text="Tirar x5\n(-- 🪙)", font_size="16sp", bold=True, background_color=(0.8, 0.6, 0.2, 1)
        )
        self.btn_tirar_5.bind(on_release=lambda x: self.realizar_tiro(cantidad=5))

        self.layout_botones_tiro.add_widget(self.btn_tirar_1)
        self.layout_botones_tiro.add_widget(self.btn_tirar_5)
        self.panel_derecho.add_widget(self.layout_botones_tiro)

        layout_principal.add_widget(panel_izquierdo)
        layout_principal.add_widget(self.panel_derecho)
        self.add_widget(layout_principal)

        self._cargar_catalogo_cartas()
        self.renderizar_vista_banner()

    def _cargar_catalogo_cartas(self):
        """Carga las cartas colectables desde cards.csv para la vista previa de banners."""
        try:
            ruta_csv = PathManager.get_data_file_path("cards.csv")
            todas = CardLoader.load_units(ruta_csv)
            excluidas = getattr(GachaSystem, "EXCLUIDAS_DE_SOBRES", {99})
            rarezas_excl = getattr(GachaSystem, "RAREZAS_EXCLUIDAS", {"Ficha", "Evento"})
            self.cartas_colectables = [
                c for c in todas
                if int(c.id) not in excluidas
                and getattr(c, "rarity", "") not in rarezas_excl
                and getattr(c, "card_type", "") != "Ficha"
            ]
        except Exception as exc:
            print(f"[⚠️ PantallaBanner] No se pudo precargar cards.csv: {exc}")
            self.cartas_colectables = []

    def on_enter(self):
        self._cargar_catalogo_cartas()
        self.actualizar_recursos()
        AudioManager().play_bgm("placeholderbossanova.ogg")

    def actualizar_recursos(self):
        """Actualiza el panel superior leyendo monedas, tickets e inventario desde el JSON."""
        if os.path.exists(self.ruta_perfil):
            with open(self.ruta_perfil, "r", encoding="utf-8") as f:
                self.perfil_cache = json.load(f)
            coins = self.perfil_cache.get("coins", 0)
            tickets = self.perfil_cache.get("tickets", 0)
            self.lbl_recursos.text = f"🪙 Monedas: {coins}   |   🎟️ Tickets: {tickets}"

    def _actualizar_estilo_botones_banner(self):
        for banner in self.lista_banners:
            bid = banner["id"]
            btn = self.botones_banners.get(bid)
            if not btn:
                continue
            activo = bid == self.banner_actual["id"]
            if banner.get("pago_con_ticket"):
                btn.background_color = (0.20, 0.78, 0.58, 1) if activo else (0.14, 0.45, 0.36, 1)
            else:
                btn.background_color = (0.24, 0.58, 0.88, 1) if activo else (0.16, 0.30, 0.46, 1)

    def cambiar_banner_activo(self, banner_seleccionado):
        self.banner_actual = banner_seleccionado
        self.renderizar_vista_banner()

    def renderizar_vista_banner(self):
        """Muestra el arte del banner, acceso a tasas/cartas y botones de tiro."""
        self.zona_central.clear_widgets()
        self._actualizar_estilo_botones_banner()

        ruta_img = self.banner_actual.get("imagen", "")
        if ruta_img and os.path.exists(ruta_img):
            widget_arte = Image(source=ruta_img, allow_stretch=True, keep_ratio=True, size_hint_y=0.58)
        else:
            # Recuadro estilizado si el PNG del banner aún no existe
            widget_arte = BoxLayout(size_hint_y=0.58, padding=16)
            with widget_arte.canvas.before:
                Color(0.15, 0.22, 0.34, 1)
                bg_rect = RoundedRectangle(pos=widget_arte.pos, size=widget_arte.size, radius=[14])
            widget_arte.bind(
                pos=lambda inst, val: setattr(bg_rect, "pos", val),
                size=lambda inst, val: setattr(bg_rect, "size", val),
            )
            lbl_emblema = Label(
                text=f"[b]🎴 {self.banner_actual['nombre'].upper()}[/b]",
                markup=True,
                font_size="24sp",
                halign="center",
            )
            widget_arte.add_widget(lbl_emblema)

        lbl_info = Label(
            text=f"[b]{self.banner_actual['nombre']}[/b]\n{self.banner_actual['desc']}",
            markup=True,
            halign="center",
            valign="middle",
            size_hint_y=0.28,
        )
        lbl_info.bind(size=lbl_info.setter("text_size"))

        btn_ver_pool = Button(
            text="📋 Ver Cartas y Tasas (%)",
            size_hint=(0.52, None),
            height=42,
            pos_hint={"center_x": 0.5},
            background_color=(0.24, 0.42, 0.64, 1),
            font_size="14sp",
            bold=True,
        )
        btn_ver_pool.bind(on_release=lambda x: self.abrir_preview_banner())

        self.zona_central.add_widget(widget_arte)
        self.zona_central.add_widget(lbl_info)
        self.zona_central.add_widget(btn_ver_pool)

        # Configuración dinámica de botones según el tipo de pago
        es_ticket = self.banner_actual.get("pago_con_ticket", False)
        if es_ticket:
            self.btn_tirar_1.opacity = 0
            self.btn_tirar_1.disabled = True

            costo = self.banner_actual.get("coste_ticket", 1)
            self.btn_tirar_5.text = f"Abrir Sobre x5\n({costo} 🎟️ Ticket)"
            self.btn_tirar_5.background_color = (0.2, 0.7, 0.5, 1)
        else:
            self.btn_tirar_1.opacity = 1
            self.btn_tirar_1.disabled = False
            self.btn_tirar_1.text = f"Tirar x1\n({self.banner_actual['coste_1']} 🪙)"
            self.btn_tirar_1.background_color = (0.3, 0.7, 0.8, 1)

            self.btn_tirar_5.text = f"Tirar x5\n({self.banner_actual['coste_5']} 🪙)"
            self.btn_tirar_5.background_color = (0.8, 0.6, 0.2, 1)

        self.layout_botones_tiro.opacity = 1
        self.layout_botones_tiro.disabled = False

    def abrir_preview_banner(self):
        """Abre el modal con las cartas del banner, rarezas y porcentajes reales."""
        if not self.cartas_colectables:
            self._cargar_catalogo_cartas()
        self.actualizar_recursos()

        pool_banner, ids_destacadas, permitir_excelencias = GachaSystem._filtrar_pool_banner(
            self.banner_actual["id"].upper(), self.cartas_colectables
        )
        inventario = self.perfil_cache.get("inventory", {})
        PopupPoolBanner(
            banner_cfg=self.banner_actual,
            pool_banner=pool_banner,
            ids_destacadas=ids_destacadas,
            permitir_excelencias=permitir_excelencias,
            inventario=inventario,
        ).open()

    def _abrir_detalle_carta_simple(self, carta):
        inventario = self.perfil_cache.get("inventory", {})
        copias = inventario.get(str(carta.id), 0)
        PopupDetalleCarta(carta, copias_actuales=copias).open()

    def realizar_tiro(self, cantidad):
        es_ticket = self.banner_actual.get("pago_con_ticket", False)
        costo_total = (
            self.banner_actual.get("coste_ticket", 1)
            if es_ticket
            else (self.banner_actual["coste_1"] if cantidad == 1 else self.banner_actual["coste_5"])
        )
        tipo_banner = self.banner_actual["id"]

        # Guardamos el inventario previo para detectar cuáles son cartas ¡NUEVAS!
        self.actualizar_recursos()
        inventario_previo = dict(self.perfil_cache.get("inventory", {}))

        resultado = GachaSystem.abrir_sobre_avanzado(
            tipo_banner=tipo_banner,
            cantidad_cartas=cantidad,
            costo=costo_total,
            pago_con_ticket=es_ticket,
            ruta_perfil=self.ruta_perfil,
        )

        if not resultado["exito"]:
            self.zona_central.clear_widgets()
            self.zona_central.add_widget(Label(text=f"❌ {resultado['mensaje']}", font_size="20sp", color=(1, 0, 0, 1)))
            return

        self.actualizar_recursos()
        self.iniciar_revelacion_uno_a_uno(resultado["cartas"], inventario_previo)

    def iniciar_revelacion_uno_a_uno(self, cartas_obtenidas, inventario_previo):
        """Prepara la revelación secuencial carta por carta."""
        self._cola_revelacion = cartas_obtenidas
        self._indice_revelacion = 0
        self._nuevas_en_tirada = set()

        # Detectar qué cartas no estaban en el inventario antes de abrir el sobre
        conteo_simulado = dict(inventario_previo)
        for idx, carta in enumerate(cartas_obtenidas):
            cid = str(carta.id)
            if conteo_simulado.get(cid, 0) == 0:
                self._nuevas_en_tirada.add(idx)
            conteo_simulado[cid] = conteo_simulado.get(cid, 0) + 1

        self.layout_botones_tiro.opacity = 0
        self.layout_botones_tiro.disabled = True
        self._mostrar_paso_revelacion()

    def _mostrar_paso_revelacion(self):
        self.zona_central.clear_widgets()
        total = len(self._cola_revelacion)
        idx = self._indice_revelacion
        carta = self._cola_revelacion[idx]
        datos = extraer_datos_carta(carta)
        rareza = datos["rareza"]
        hex_r = HEX_RAREZA.get(rareza, "FFFFFF")
        es_nueva = idx in self._nuevas_en_tirada

        anuncios_rareza = {
            "Excelencia": f"[color={hex_r}][b]★ ¡¡EXCELENCIA!! ★[/b][/color]",
            "Épica": f"[color={hex_r}][b]✦ ¡CARTA ÉPICA! ✦[/b][/color]",
            "Especial": f"[color={hex_r}][b]◆ Carta Especial ◆[/b][/color]",
            "Común": f"[color={hex_r}]• Carta Común •[/color]",
        }

        lbl_progreso = Label(
            text=f"[b]Carta {idx + 1} de {total}[/b]\n{anuncios_rareza.get(rareza, rareza)}",
            markup=True,
            font_size="20sp",
            halign="center",
            size_hint_y=0.22,
        )
        self.zona_central.add_widget(lbl_progreso)

        # Contenedor centrado para la carta protagonista con animación de aparición
        contenedor_centro = BoxLayout(orientation="horizontal", size_hint_y=0.58)
        contenedor_centro.add_widget(BoxLayout())  # Espaciador izquierdo

        tarjeta = TarjetaRevelada(
            carta=carta,
            es_nueva=es_nueva,
            on_ver_detalle=self._abrir_detalle_carta_simple,
            ancho=220,
        )
        tarjeta.opacity = 0
        contenedor_centro.add_widget(tarjeta)

        contenedor_centro.add_widget(BoxLayout())  # Espaciador derecho
        self.zona_central.add_widget(contenedor_centro)

        Animation(opacity=1, duration=0.24).start(tarjeta)

        # Controles inferiores: Siguiente / Resumen + Saltar todo
        barra_avance = BoxLayout(orientation="horizontal", spacing=14, size_hint_y=0.20, padding=(30, 6))
        es_ultima = idx >= total - 1

        btn_siguiente = Button(
            text="Ver Resumen Final ✨" if es_ultima else "Siguiente Carta ➔",
            font_size="16sp",
            bold=True,
            background_color=(0.20, 0.68, 0.35, 1) if es_ultima else (0.22, 0.55, 0.82, 1),
        )
        btn_siguiente.bind(on_release=lambda x: self._avanzar_revelacion())
        barra_avance.add_widget(btn_siguiente)

        if not es_ultima:
            btn_saltar = Button(
                text="Saltar Todo ⏭️",
                size_hint_x=0.38,
                font_size="14sp",
                background_color=(0.45, 0.45, 0.52, 1),
            )
            btn_saltar.bind(on_release=lambda x: self.renderizar_resumen_sobre())
            barra_avance.add_widget(btn_saltar)

        self.zona_central.add_widget(barra_avance)

    def _avanzar_revelacion(self):
        self._indice_revelacion += 1
        if self._indice_revelacion < len(self._cola_revelacion):
            self._mostrar_paso_revelacion()
        else:
            self.renderizar_resumen_sobre()

    def renderizar_resumen_sobre(self):
        """Muestra el resumen con todas las cartas obtenidas clicables."""
        self.zona_central.clear_widgets()

        lbl_felicidades = Label(
            text="✨ ¡RESUMEN DEL SOBRE! ✨\n[size=13sp](Haz clic en cualquier carta para ver su detalle)[/size]",
            markup=True,
            font_size="22sp",
            bold=True,
            halign="center",
            size_hint_y=0.22,
        )
        self.zona_central.add_widget(lbl_felicidades)

        contenedor_grilla = BoxLayout(orientation="horizontal", padding=12, size_hint_y=0.58)
        scroll_cartas = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False)

        grilla_cartas = GridLayout(rows=1, spacing=14, size_hint_x=None)
        grilla_cartas.bind(minimum_width=grilla_cartas.setter("width"))

        for idx, carta in enumerate(self._cola_revelacion):
            recuadro_carta = TarjetaRevelada(
                carta=carta,
                es_nueva=(idx in self._nuevas_en_tirada),
                on_ver_detalle=self._abrir_detalle_carta_simple,
                ancho=155,
            )
            grilla_cartas.add_widget(recuadro_carta)

        scroll_cartas.add_widget(grilla_cartas)
        contenedor_grilla.add_widget(scroll_cartas)
        self.zona_central.add_widget(contenedor_grilla)

        btn_aceptar = Button(
            text="Aceptar",
            size_hint_y=0.18,
            size_hint_x=0.45,
            pos_hint={"center_x": 0.5},
            background_color=(0.2, 0.7, 0.3, 1),
            font_size="16sp",
            bold=True,
        )
        btn_aceptar.bind(on_release=lambda x: self.renderizar_vista_banner())
        self.zona_central.add_widget(btn_aceptar)

    def cambiar_a_tienda(self):
        self.manager.current = "shop_screen"

    def cambiar_a_menu(self):
        self.manager.current = "menu_screen"