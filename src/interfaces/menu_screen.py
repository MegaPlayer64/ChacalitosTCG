from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from src.domain.audio_manager import AudioManager

class MenuPrincipal(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Layout principal de toda la pantalla (Vertical)
        layout_global = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        # Encabezado / Título del Juego
        lbl_titulo = Label(
            text="[b]Chacalitos TCG[/b]\n[size=16sp]Engine v0.1.5[/size]", 
            font_size='32sp', 
            markup=True,
            size_hint_y=0.25,
            halign='center'
        )
        layout_global.add_widget(lbl_titulo)
        
        # Sub-contenedor para centrar los botones y que no ocupen todo el ancho
        layout_botones = BoxLayout(orientation='vertical', spacing=12, size_hint_x=0.6, pos_hint={'center_x': 0.5})
        
        btn_jugar = Button(text="BUSCAR PARTIDA", font_size='18sp', size_hint_y=None, height=50)
        btn_mazos = Button(text="COLECCIÓN Y MAZOS", font_size='18sp', size_hint_y=None, height=50)
        btn_gacha = Button(text="TIENDA / BANNERS", font_size='18sp', size_hint_y=None, height=50)
        btn_salir = Button(text="SALIR", font_size='18sp', size_hint_y=None, height=50)
        
        # Enlaces temporales para la navegación
        btn_jugar.bind(on_release=lambda x: self.cambiar_pantalla('selection_screen'))
        btn_mazos.bind(on_release=lambda x: self.cambiar_pantalla('inventory_screen'))
        btn_gacha.bind(on_release=lambda x: self.cambiar_pantalla('banner_screen'))
        btn_salir.bind(on_release=lambda x: self.manager.app.stop() if hasattr(self.manager, 'app') else exit())
        
        layout_botones.add_widget(btn_jugar)
        layout_botones.add_widget(btn_mazos)
        layout_botones.add_widget(btn_gacha)
        layout_botones.add_widget(btn_salir)
        
        layout_global.add_widget(layout_botones)
        
        # Footer con versión o créditos
        lbl_footer = Label(text="xXmegaplayer64Xx - 2026", font_size='12sp', size_hint_y=0.1)
        layout_global.add_widget(lbl_footer)
        
        self.add_widget(layout_global)

    def cambiar_pantalla(self, nombre_pantalla):
        self.manager.current = nombre_pantalla

    def on_enter(self):
        AudioManager().play_bgm('titanicmonarch.ogg')