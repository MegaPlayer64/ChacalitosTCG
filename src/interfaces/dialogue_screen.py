from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Line
import os

class PantallaHistoria(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.dialogue_list = []
        self.current_index = 0
        self.on_finish_callback = None

        # Root Layout
        self.layout_root = FloatLayout()

        # 1. Fondo de Escena
        self.bg_image = Image(
            source='assets/backgrounds/bg_story_default.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.layout_root.add_widget(self.bg_image)

        # 2. Retrato del Personaje (Izquierda / Derecha)
        self.avatar_left = Image(
            size_hint=(0.35, 0.55),
            pos_hint={'x': 0.05, 'y': 0.25},
            opacity=0
        )
        self.avatar_right = Image(
            size_hint=(0.35, 0.55),
            pos_hint={'right': 0.95, 'y': 0.25},
            opacity=0
        )
        self.layout_root.add_widget(self.avatar_left)
        self.layout_root.add_widget(self.avatar_right)

        # 3. Contenedor del Cuadro de Diálogo (Bottom Panel)
        self.box_dialogue = BoxLayout(
            orientation='vertical',
            padding=[20, 15, 20, 15],
            spacing=5,
            size_hint=(0.92, 0.28),
            pos_hint={'center_x': 0.5, 'y': 0.03}
        )
        
        # Estilo de caja de diálogo alto contraste (E-ink Friendly)
        with self.box_dialogue.canvas.before:
            Color(0.08, 0.08, 0.1, 0.95)  # Fondo oscuro sólido
            self.rect_bg = Rectangle(pos=self.box_dialogue.pos, size=self.box_dialogue.size)
            Color(1, 1, 1, 1)  # Borde blanco
            self.line_border = Line(rect=(self.box_dialogue.x, self.box_dialogue.y, self.box_dialogue.width, self.box_dialogue.height), width=1.5)

        self.box_dialogue.bind(pos=self._update_canvas, size=self._update_canvas)

        # Etiqueta con el nombre del Personaje
        self.lbl_speaker = Label(
            text="Personaje",
            font_size='18sp',
            bold=True,
            color=(1, 0.85, 0.3, 1), # Tono dorado/destacado
            size_hint_y=0.25,
            halign='left',
            valign='middle'
        )
        self.lbl_speaker.bind(size=self.lbl_speaker.setter('text_size'))

        # Texto del Diálogo
        self.lbl_text = Label(
            text="Aquí aparecerá el diálogo de la historia...",
            font_size='17sp',
            color=(1, 1, 1, 1),
            size_hint_y=0.75,
            halign='left',
            valign='top'
        )
        self.lbl_text.bind(size=self.lbl_text.setter('text_size'))

        self.box_dialogue.add_widget(self.lbl_speaker)
        self.box_dialogue.add_widget(self.lbl_text)
        self.layout_root.add_widget(self.box_dialogue)

        # 4. Botón invisible transparente que cubre toda la pantalla para avanzar con un Tap
        btn_touch_advance = Button(
            background_color=(0, 0, 0, 0),
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        btn_touch_advance.bind(on_release=lambda x: self.avanzar_dialogo())
        self.layout_root.add_widget(btn_touch_advance)

        # Botón para Omitir Historia (SKIP)
        btn_skip = Button(
            text="OMITIR ⏭",
            font_size='12sp',
            size_hint=(0.18, 0.06),
            pos_hint={'right': 0.96, 'top': 0.97},
            background_color=(0.3, 0.3, 0.3, 1)
        )
        btn_skip.bind(on_release=lambda x: self.finalizar_escena())
        self.layout_root.add_widget(btn_skip)

        self.add_widget(self.layout_root)

    def _update_canvas(self, instance, value):
        self.rect_bg.pos = instance.pos
        self.rect_bg.size = instance.size
        self.line_border.rect = (instance.x, instance.y, instance.width, instance.height)

    def cargar_escena(self, data_escena, callback_al_terminar=None):
        """Inicializa la secuencia de diálogos a partir de un diccionario/JSON."""
        self.dialogue_list = data_escena.get("dialogues", [])
        self.current_index = 0
        self.on_finish_callback = callback_al_terminar

        if "background" in data_escena and os.path.exists(data_escena["background"]):
            self.bg_image.source = data_escena["background"]

        if self.dialogue_list:
            self.mostrar_nodo(self.dialogue_list[0])

    def mostrar_nodo(self, nodo):
        """Muestra la línea actual, el nombre y posiciona el retrato."""
        self.lbl_speaker.text = f"[b]{nodo.get('speaker', '???')}[/b]"
        self.lbl_text.text = nodo.get('text', '')

        avatar_path = nodo.get("avatar", "")
        side = nodo.get("side", "left")

        # Configurar visibilidad de retratos
        if side == "left":
            self.avatar_right.opacity = 0
            if avatar_path and os.path.exists(avatar_path):
                self.avatar_left.source = avatar_path
                self.avatar_left.opacity = 1
            else:
                self.avatar_left.opacity = 0
        else:
            self.avatar_left.opacity = 0
            if avatar_path and os.path.exists(avatar_path):
                self.avatar_right.source = avatar_path
                self.avatar_right.opacity = 1
            else:
                self.avatar_right.opacity = 0

    def avanzar_dialogo(self):
        """Pasa al siguiente texto de la lista o termina la escena."""
        self.current_index += 1
        if self.current_index < len(self.dialogue_list):
            self.mostrar_nodo(self.dialogue_list[self.current_index])
        else:
            self.finalizar_escena()

    def finalizar_escena(self):
        """Llama al callback o redirige al tutorial/pantalla correspondiente."""
        if self.on_finish_callback:
            self.on_finish_callback()
        else:
            # Transición por defecto a la pantalla de Tutorial o Selección
            self.manager.current = 'tutorial_game_screen'