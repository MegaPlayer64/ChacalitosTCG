"""
Herramienta de Desarrollo para Ajuste y Encuadre de Artes de Cartas (DevArtTool).

Provee un ModalView interactivo con vista previa en tiempo real, selector de cartas
y controles de deslizamiento para calibrar Zoom, Offset X y Offset Y guardando
los resultados directamente en 'src/data/card_art_config.json'.
"""

from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle, Line

from src.infrastructure.loaders.card_loader import CardLoader
from src.infrastructure.loaders.card_art_loader import CardArtLoader
from src.interfaces.widgets.card_art_widget import CardArtWidget
from src.domain.card_styles import apply_card_theme, get_rarity_markup
from src.domain.audio_manager import AudioManager


class DevArtAdjusterModal(ModalView):
    def __init__(self, card_id=1, on_save_callback=None, **kwargs):
        super().__init__(size_hint=(0.88, 0.92), auto_dismiss=False, **kwargs)
        self.on_save_callback = on_save_callback
        self.actualizando_ui = False

        # Obtener todas las cartas disponibles para el selector
        todas_las_cartas = CardLoader.load_units()
        self.cartas_map = {str(c.id): c for c in todas_las_cartas}
        self.lista_ids = sorted(list(self.cartas_map.keys()), key=lambda x: int(x) if x.isdigit() else 999)
        if not self.lista_ids:
            self.lista_ids = [str(i) for i in range(1, 89)]

        self.current_id = str(card_id) if str(card_id) in self.cartas_map else self.lista_ids[0]

        # Contenedor raíz con fondo oscuro estilizado
        layout_principal = BoxLayout(orientation='vertical', padding=18, spacing=12)

        with layout_principal.canvas.before:
            Color(0.10, 0.12, 0.16, 0.98)
            self.rect_fondo = RoundedRectangle(pos=self.pos, size=self.size, radius=[14, 14, 14, 14])
            Color(0.28, 0.35, 0.48, 1.0)
            self.borde_fondo = Line(rounded_rectangle=[self.pos[0], self.pos[1], self.size[0], self.size[1], 14], width=1.5)

        layout_principal.bind(
            pos=self._actualizar_canvas_fondo,
            size=self._actualizar_canvas_fondo
        )

        # --- 1. ENCABEZADO SUPERIOR ---
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=42, spacing=10)
        lbl_titulo = Label(
            text="[b]🎨 AJUSTADOR DE ARTE Y ENCUADRES (MODO DESARROLLADOR)[/b]",
            markup=True,
            font_size='17sp',
            halign='left',
            valign='middle'
        )
        lbl_titulo.bind(size=lbl_titulo.setter('text_size'))

        btn_cerrar = Button(
            text="✕ CERRAR",
            font_size='14sp',
            size_hint=(None, None),
            size=(110, 38),
            background_color=(0.8, 0.25, 0.25, 1),
            bold=True
        )
        btn_cerrar.bind(on_release=self.dismiss)

        header.add_widget(lbl_titulo)
        header.add_widget(btn_cerrar)
        layout_principal.add_widget(header)

        # --- 2. BARRA SELECTORA DE CARTA ---
        barra_selector = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=8)

        btn_prev = Button(text="◀ Anterior", size_hint_x=None, width=110, background_color=(0.25, 0.35, 0.5, 1))
        btn_prev.bind(on_release=self.anterior_carta)

        # Construir opciones del spinner con ID y Nombre
        opciones_spinner = []
        for cid in self.lista_ids:
            c_obj = self.cartas_map.get(cid)
            nombre = c_obj.name if c_obj else f"Carta #{cid}"
            opciones_spinner.append(f"#{cid} - {nombre}")

        self.spinner_cartas = Spinner(
            text=self._obtener_texto_spinner(self.current_id),
            values=opciones_spinner,
            size_hint_x=1.0,
            font_size='15sp',
            background_color=(0.18, 0.24, 0.35, 1)
        )
        self.spinner_cartas.bind(text=self.al_seleccionar_carta_spinner)

        btn_next = Button(text="Siguiente ▶", size_hint_x=None, width=110, background_color=(0.25, 0.35, 0.5, 1))
        btn_next.bind(on_release=self.siguiente_carta)

        barra_selector.add_widget(btn_prev)
        barra_selector.add_widget(self.spinner_cartas)
        barra_selector.add_widget(btn_next)
        layout_principal.add_widget(barra_selector)

        # --- 3. ÁREA CENTRAL (VISTA PREVIA + CONTROLES) ---
        area_central = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=1.0)

        # A. VISTA PREVIA DE LA CARTA
        col_preview = BoxLayout(orientation='vertical', size_hint_x=0.45, spacing=8)
        col_preview.add_widget(Label(text="[b]Vista Previa de la Carta[/b]", markup=True, size_hint_y=None, height=26))

        # Marco contenedor de la carta simulada
        self.card_frame = BoxLayout(
            orientation='vertical',
            padding=8,
            spacing=6,
            size_hint=(None, None),
            size=(220, 295),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # Widget visual de arte de carta (Ventana de calibración 200x200)
        self.lbl_card_header = Label(
            text="", 
            markup=True, 
            font_size='14sp', 
            size_hint_y=None,
            height=32,
            halign='center',
            valign='middle'
        )
        self.lbl_card_header.bind(size=self.lbl_card_header.setter('text_size'))

        self.art_widget = CardArtWidget(
            card_id=self.current_id, 
            is_detail=False, 
            auto_load=False, 
            size_hint=(None, None), 
            size=(200, 200),
            pos_hint={'center_x': 0.5}
        )

        self.lbl_card_info = Label(
            text="", 
            markup=True, 
            font_size='12sp', 
            size_hint_y=None,
            height=28,
            halign='center',
            valign='middle'
        )
        self.lbl_card_info.bind(size=self.lbl_card_info.setter('text_size'))

        self.card_frame.add_widget(self.lbl_card_header)
        self.card_frame.add_widget(self.art_widget)
        self.card_frame.add_widget(self.lbl_card_info)

        col_preview.add_widget(self.card_frame)
        area_central.add_widget(col_preview)

        # B. PANEL DE CONTROLES Y SLIDERS
        col_controls = BoxLayout(orientation='vertical', size_hint_x=0.55, spacing=14, padding=[10, 5, 10, 5])

        # Control 1: ZOOM
        box_zoom = BoxLayout(orientation='vertical', spacing=3, size_hint_y=None, height=65)
        self.lbl_zoom = Label(text="🔍 Escala / Zoom: 1.00x", markup=True, halign='left', size_hint_y=None, height=22)
        self.lbl_zoom.bind(size=self.lbl_zoom.setter('text_size'))
        self.slider_zoom = Slider(min=0.5, max=3.0, step=0.05, value=1.0)
        self.slider_zoom.bind(value=self.on_slider_change)
        box_zoom.add_widget(self.lbl_zoom)
        box_zoom.add_widget(self.slider_zoom)
        col_controls.add_widget(box_zoom)

        # Control 2: OFFSET X
        box_x = BoxLayout(orientation='vertical', spacing=3, size_hint_y=None, height=65)
        self.lbl_x = Label(text="↔️ Desplazamiento X: 0 px", markup=True, halign='left', size_hint_y=None, height=22)
        self.lbl_x.bind(size=self.lbl_x.setter('text_size'))
        self.slider_x = Slider(min=-100.0, max=100.0, step=1.0, value=0.0)
        self.slider_x.bind(value=self.on_slider_change)
        box_x.add_widget(self.lbl_x)
        box_x.add_widget(self.slider_x)
        col_controls.add_widget(box_x)

        # Control 3: OFFSET Y
        box_y = BoxLayout(orientation='vertical', spacing=3, size_hint_y=None, height=65)
        self.lbl_y = Label(text="↕️ Desplazamiento Y: 0 px", markup=True, halign='left', size_hint_y=None, height=22)
        self.lbl_y.bind(size=self.lbl_y.setter('text_size'))
        self.slider_y = Slider(min=-100.0, max=100.0, step=1.0, value=0.0)
        self.slider_y.bind(value=self.on_slider_change)
        box_y.add_widget(self.lbl_y)
        box_y.add_widget(self.slider_y)
        col_controls.add_widget(box_y)

        # Botón de Reset
        btn_reset = Button(
            text="↺ Restablecer a Valores por Defecto (1.0x, 0, 0)",
            size_hint_y=None,
            height=38,
            font_size='13sp',
            background_color=(0.35, 0.40, 0.45, 1)
        )
        btn_reset.bind(on_release=self.reset_valores)
        col_controls.add_widget(btn_reset)

        # Label de Estado / Guardado
        self.lbl_status = Label(
            text="[color=aaaaaa]Mueve los controles para encuadrar la ilustración en vivo.[/color]",
            markup=True,
            font_size='13sp',
            halign='center',
            size_hint_y=None,
            height=32
        )
        self.lbl_status.bind(size=self.lbl_status.setter('text_size'))
        col_controls.add_widget(self.lbl_status)

        # Botón de Guardar
        btn_save = Button(
            text="💾 GUARDAR CONFIGURACIÓN",
            font_size='16sp',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.75, 0.45, 1),
            bold=True
        )
        btn_save.bind(on_release=self.guardar_configuracion)
        col_controls.add_widget(btn_save)

        area_central.add_widget(col_controls)
        layout_principal.add_widget(area_central)

        self.add_widget(layout_principal)
        self.cargar_datos_carta(self.current_id)

    def _actualizar_canvas_fondo(self, instance, *args):
        self.rect_fondo.pos = instance.pos
        self.rect_fondo.size = instance.size
        self.borde_fondo.rounded_rectangle = [instance.pos[0], instance.pos[1], instance.size[0], instance.size[1], 14]

    def _obtener_texto_spinner(self, cid):
        c_obj = self.cartas_map.get(str(cid))
        nombre = c_obj.name if c_obj else f"Carta #{cid}"
        return f"#{cid} - {nombre}"

    def cargar_datos_carta(self, cid):
        """Carga la carta especificada, sincronizando la vista previa y los sliders."""
        self.actualizando_ui = True
        self.current_id = str(cid)
        c_obj = self.cartas_map.get(self.current_id)

        # 1. Configuración visual del marco según rareza y tipo
        rareza = getattr(c_obj, 'rarity', 'Común') if c_obj else 'Común'
        tipo = getattr(c_obj, 'card_type', 'unit') if c_obj else 'unit'
        apply_card_theme(self.card_frame, rarity=rareza, card_type=tipo)

        color_tag = get_rarity_markup(rareza)
        nombre = c_obj.name if c_obj else f"Carta #{self.current_id}"
        coste = getattr(c_obj, 'cost', 0) if c_obj else 0
        self.lbl_card_header.text = f"{color_tag}[b]{nombre.upper()}[/b][/color]"
        self.lbl_card_info.text = f"⚡ Coste: {coste}E | [{rareza}]"

        # 2. Cargar configuración de encuadre
        cfg = CardArtLoader.get_art_config(self.current_id)
        zoom = cfg.get("zoom", 1.0)
        offset_x = cfg.get("offset_x", 0.0)
        offset_y = cfg.get("offset_y", 0.0)

        # 3. Asignar a sliders
        self.slider_zoom.value = zoom
        self.slider_x.value = offset_x
        self.slider_y.value = offset_y

        self.lbl_zoom.text = f"🔍 Escala / Zoom: [b]{zoom:.2f}x[/b]"
        self.lbl_x.text = f"↔️ Desplazamiento X: [b]{offset_x:+.0f} px[/b]"
        self.lbl_y.text = f"↕️ Desplazamiento Y: [b]{offset_y:+.0f} px[/b]"

        # 4. Actualizar widget visual
        self.art_widget.set_card_id(self.current_id)
        self.art_widget.zoom = zoom
        self.art_widget.offset_x = offset_x
        self.art_widget.offset_y = offset_y

        self.lbl_status.text = f"[color=aaaaaa]Editando encuadre de #{self.current_id} ({nombre}).[/color]"
        self.actualizando_ui = False

    def on_slider_change(self, *args):
        """Reacciona a los cambios en los sliders para actualizar la vista previa en tiempo real."""
        if self.actualizando_ui:
            return

        zoom = round(float(self.slider_zoom.value), 2)
        ox = round(float(self.slider_x.value), 1)
        oy = round(float(self.slider_y.value), 1)

        self.lbl_zoom.text = f"🔍 Escala / Zoom: [b]{zoom:.2f}x[/b]"
        self.lbl_x.text = f"↔️ Desplazamiento X: [b]{ox:+.0f} px[/b]"
        self.lbl_y.text = f"↕️ Desplazamiento Y: [b]{oy:+.0f} px[/b]"

        # Actualizar vista previa en tiempo real
        self.art_widget.zoom = zoom
        self.art_widget.offset_x = ox
        self.art_widget.offset_y = oy

    def reset_valores(self, *args):
        """Restablece los sliders a escala 1.0 y offsets en 0."""
        self.slider_zoom.value = 1.0
        self.slider_x.value = 0.0
        self.slider_y.value = 0.0
        self.on_slider_change()
        self.lbl_status.text = "[color=ffbb33]↺ Valores restablecidos a los valores por defecto.[/color]"

    def guardar_configuracion(self, *args):
        """Escribe la configuración de la carta actual en el archivo JSON."""
        zoom = round(float(self.slider_zoom.value), 2)
        ox = round(float(self.slider_x.value), 1)
        oy = round(float(self.slider_y.value), 1)

        exito = CardArtLoader.set_art_config(self.current_id, zoom=zoom, offset_x=ox, offset_y=oy, auto_save=True)
        if exito:
            self.lbl_status.text = f"[color=00ff88]✓ ¡Configuración guardada para #{self.current_id} ({zoom}x, {ox}px, {oy}px)![/color]"
            AudioManager().play_sfx("draw")
            if self.on_save_callback:
                self.on_save_callback(self.current_id, {"zoom": zoom, "offset_x": ox, "offset_y": oy})
        else:
            self.lbl_status.text = "[color=ff4444]❌ Error al guardar la configuración en disco.[/color]"
            AudioManager().play_sfx("error1")

    def al_seleccionar_carta_spinner(self, spinner, text):
        if not text or self.actualizando_ui:
            return
        # Extraer ID a partir del formato '#{id} - {nombre}'
        try:
            cid = text.split("-")[0].replace("#", "").strip()
            if cid in self.lista_ids:
                self.cargar_datos_carta(cid)
        except Exception:
            pass

    def anterior_carta(self, *args):
        idx = self.lista_ids.index(self.current_id) if self.current_id in self.lista_ids else 0
        nuevo_idx = (idx - 1) % len(self.lista_ids)
        nuevo_id = self.lista_ids[nuevo_idx]
        self.spinner_cartas.text = self._obtener_texto_spinner(nuevo_id)

    def siguiente_carta(self, *args):
        idx = self.lista_ids.index(self.current_id) if self.current_id in self.lista_ids else 0
        nuevo_idx = (idx + 1) % len(self.lista_ids)
        nuevo_id = self.lista_ids[nuevo_idx]
        self.spinner_cartas.text = self._obtener_texto_spinner(nuevo_id)
