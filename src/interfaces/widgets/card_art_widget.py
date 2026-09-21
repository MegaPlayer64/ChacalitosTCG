"""
Componente Visual de Arte de Carta con Encuadre y Modo Detalle (CardArtWidget).

Permite dos modos de visualización:
1. is_detail=False (Miniatura / Thumbnail para Mano, Álbum y Grillas):
   - Mantiene una relación de aspecto fija (1:1 cuadrada) centrada en su contenedor padre.
   - Aplica máscara Stencil para recortar los márgenes sobrantes.
   - Escala dinámicamente los desplazamientos X e Y en proporción al tamaño del canvas
     (normalizados respecto a REF_SIZE=200.0) para que el encuadre sea 100% idéntico en cualquier pantalla.
   - Aplica el zoom y offset configurados en card_art_config.json.

2. is_detail=True (Vista de Detalles / Inspección de Carta):
   - Desactiva el Stencil y el recorte.
   - Renderiza la ilustración completa original ajustada con keep_ratio=True y allow_stretch=True,
     mostrando el arte entero sin zoom ni cortes en alta definición.
"""

from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.graphics import StencilPush, StencilUse, StencilUnUse, StencilPop, Rectangle
from src.infrastructure.loaders.card_art_loader import CardArtLoader


class CardArtWidget(Widget):
    zoom = NumericProperty(1.0)
    offset_x = NumericProperty(0.0)
    offset_y = NumericProperty(0.0)
    source = StringProperty("")
    card_id = StringProperty("")
    is_detail = BooleanProperty(False)

    REF_SIZE = 200.0  # Dimensión base de referencia para normalizar desplazamientos

    def __init__(self, card_id=None, is_detail=False, auto_load=True, **kwargs):
        super().__init__(**kwargs)
        self.is_detail = is_detail
        self.auto_load = auto_load

        # Instrucciones gráficas para recorte Stencil
        self._stencil_push = StencilPush()
        self._stencil_rect_before = Rectangle()
        self._stencil_use = StencilUse()

        self._stencil_unuse = StencilUnUse()
        self._stencil_rect_after = Rectangle()
        self._stencil_pop = StencilPop()

        # Imagen interna de la carta
        self._img = Image(
            allow_stretch=True,
            keep_ratio=self.is_detail,
            size_hint=(None, None)
        )
        self.add_widget(self._img)

        # Configuración inicial del canvas
        self._configurar_stencil()

        # Vincular eventos para recalcular geometría
        self.bind(
            pos=self._actualizar_geometria,
            size=self._actualizar_geometria,
            zoom=self._actualizar_geometria,
            offset_x=self._actualizar_geometria,
            offset_y=self._actualizar_geometria,
            source=self._on_source_changed,
            is_detail=self._on_is_detail_changed
        )
        self._img.bind(texture=self._actualizar_geometria)

        if card_id is not None:
            self.set_card_id(card_id)

    def _configurar_stencil(self):
        """Activa el Stencil si es miniatura o lo desactiva si es vista de detalle."""
        self.canvas.before.clear()
        self.canvas.after.clear()

        if not self.is_detail:
            self.canvas.before.add(self._stencil_push)
            self.canvas.before.add(self._stencil_rect_before)
            self.canvas.before.add(self._stencil_use)

            self.canvas.after.add(self._stencil_unuse)
            self.canvas.after.add(self._stencil_rect_after)
            self.canvas.after.add(self._stencil_pop)
            self._img.keep_ratio = False
        else:
            self._img.keep_ratio = True

    def _on_is_detail_changed(self, *args):
        self._configurar_stencil()
        self._actualizar_geometria()

    def set_card_id(self, card_id):
        """Asigna la carta, cargando su imagen y configuración de encuadre correspondiente."""
        self.card_id = str(card_id).strip()
        art_path = CardArtLoader.get_card_art_path(self.card_id)
        self.source = art_path

        if self.auto_load and not self.is_detail:
            cfg = CardArtLoader.get_art_config(self.card_id)
            self.zoom = cfg.get("zoom", 1.0)
            self.offset_x = cfg.get("offset_x", 0.0)
            self.offset_y = cfg.get("offset_y", 0.0)

    def reload_config(self):
        """Recarga la configuración de encuadre almacenada en JSON para esta carta."""
        if self.card_id and not self.is_detail:
            cfg = CardArtLoader.get_art_config(self.card_id)
            self.zoom = cfg.get("zoom", 1.0)
            self.offset_x = cfg.get("offset_x", 0.0)
            self.offset_y = cfg.get("offset_y", 0.0)

    def _on_source_changed(self, _instance, value):
        self._img.source = value

    def _actualizar_geometria(self, *args):
        """Recalcula dimensiones y posición de la imagen y máscara de recorte."""
        w, h = self.size
        x, y = self.pos

        if w <= 0 or h <= 0:
            return

        if self.is_detail:
            # ----------------------------------------------------
            # MODO VISTA DE DETALLE:
            # La imagen completa ocupa el widget con keep_ratio=True
            # ----------------------------------------------------
            self._img.allow_stretch = True
            self._img.keep_ratio = True
            self._img.pos = (x, y)
            self._img.size = (w, h)
            return

        # ----------------------------------------------------
        # MODO MINIATURA CON ENCUADRE:
        # 1. Ventana fija de relación de aspecto 1:1 cuadrada centrada en el widget
        # ----------------------------------------------------
        side = min(w, h)
        crop_x = x + (w - side) / 2.0
        crop_y = y + (h - side) / 2.0

        # Actualizar coordenadas de la máscara Stencil
        self._stencil_rect_before.pos = (crop_x, crop_y)
        self._stencil_rect_before.size = (side, side)
        self._stencil_rect_after.pos = (crop_x, crop_y)
        self._stencil_rect_after.size = (side, side)

        # 2. Escalar imagen para cubrir la ventana cuadrada (Cover)
        tex = self._img.texture
        if tex and tex.width > 0 and tex.height > 0:
            base_scale = max(side / tex.width, side / tex.height)
            base_w = tex.width * base_scale
            base_h = tex.height * base_scale
        else:
            base_w = side
            base_h = side

        # 3. Aplicar factor de zoom
        scale_factor = max(0.1, self.zoom)
        final_w = base_w * scale_factor
        final_h = base_h * scale_factor

        # 4. Escalar desplazamientos X e Y de forma proporcional a la ventana (relativo a REF_SIZE)
        rel_scale = side / self.REF_SIZE
        scaled_offset_x = self.offset_x * rel_scale
        scaled_offset_y = self.offset_y * rel_scale

        # 5. Centrar imagen en la ventana cuadrada y aplicar desplazamientos
        center_x = crop_x + (side / 2.0) + scaled_offset_x
        center_y = crop_y + (side / 2.0) + scaled_offset_y

        img_x = center_x - (final_w / 2.0)
        img_y = center_y - (final_h / 2.0)

        self._img.allow_stretch = True
        self._img.keep_ratio = False
        self._img.pos = (img_x, img_y)
        self._img.size = (final_w, final_h)
