from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
import os

class PantallaVersus(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout_principal = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        # Título
        self.lbl_titulo = Label(text="[b][size=40]PREPARANDO PARTIDA[/size][/b]", markup=True, size_hint_y=0.2)
        self.layout_principal.add_widget(self.lbl_titulo)
        
        # Contenedor de Perfiles (Jugador 1 VS Jugador 2)
        self.layout_perfiles = BoxLayout(orientation='horizontal', spacing=30, size_hint_y=0.6)
        
        # Perfil 1
        self.perfil_1 = BoxLayout(orientation='vertical', spacing=10)
        self.lbl_p1_nombre = Label(text="[b]Jugador 1[/b]", markup=True, font_size='24sp', size_hint_y=0.2)
        self.lbl_p1_tipo = Label(text="Tipo: Humano", font_size='18sp', size_hint_y=0.2)
        self.lbl_p1_mazo = Label(text="Mazo: ...", font_size='16sp', size_hint_y=0.6, text_size=(None, None), halign='center', valign='middle')
        self.lbl_p1_mazo.bind(size=self.lbl_p1_mazo.setter('text_size'))
        
        self.perfil_1.add_widget(self.lbl_p1_nombre)
        self.perfil_1.add_widget(self.lbl_p1_tipo)
        self.perfil_1.add_widget(self.lbl_p1_mazo)
        
        # Etiqueta VS
        self.lbl_vs = Label(text="[b][size=50][color=ff3333]VS[/color][/size][/b]", markup=True, size_hint_x=0.2)
        
        # Perfil 2
        self.perfil_2 = BoxLayout(orientation='vertical', spacing=10)
        self.lbl_p2_nombre = Label(text="[b]Jugador 2[/b]", markup=True, font_size='24sp', size_hint_y=0.2)
        self.lbl_p2_tipo = Label(text="Tipo: ...", font_size='18sp', size_hint_y=0.2)
        self.lbl_p2_mazo = Label(text="Mazo: ...", font_size='16sp', size_hint_y=0.6, text_size=(None, None), halign='center', valign='middle')
        self.lbl_p2_mazo.bind(size=self.lbl_p2_mazo.setter('text_size'))
        
        self.perfil_2.add_widget(self.lbl_p2_nombre)
        self.perfil_2.add_widget(self.lbl_p2_tipo)
        self.perfil_2.add_widget(self.lbl_p2_mazo)
        
        self.layout_perfiles.add_widget(self.perfil_1)
        self.layout_perfiles.add_widget(self.lbl_vs)
        self.layout_perfiles.add_widget(self.perfil_2)
        
        self.layout_principal.add_widget(self.layout_perfiles)
        
        # Indicador de Carga
        self.lbl_carga = Label(text="Iniciando...", font_size='20sp', size_hint_y=0.2)
        self.layout_principal.add_widget(self.lbl_carga)
        
        self.add_widget(self.layout_principal)

    def on_pre_enter(self, *args):
        # Cargar los datos desde app.game_settings
        app = self.manager.app
        settings = getattr(app, 'game_settings', None)
        
        if settings:
            # Configurar visualmente J1
            self.lbl_p1_tipo.text = f"Tipo: {settings['p1']['tipo']}"
            nombre_mazo_p1 = os.path.basename(settings['p1']['mazo']).replace('.json', '')
            self.lbl_p1_mazo.text = f"[color=aaffaa]Mazo:\n{nombre_mazo_p1}[/color]"
            self.lbl_p1_mazo.markup = True
            
            # Configurar visualmente J2
            self.lbl_p2_tipo.text = f"Tipo: {settings['p2']['tipo']}"
            nombre_mazo_p2 = os.path.basename(settings['p2']['mazo']).replace('.json', '')
            self.lbl_p2_mazo.text = f"[color=ffaaaa]Mazo:\n{nombre_mazo_p2}[/color]"
            self.lbl_p2_mazo.markup = True
            
            if 'Humano' not in settings['p2']['tipo']:
                self.lbl_p2_nombre.text = f"[b]IA ({settings['p2']['tipo']})[/b]"
            else:
                self.lbl_p2_nombre.text = "[b]Jugador 2[/b]"

        # Programar cambio a la pantalla del juego
        # Pasamos un tiempo corto para que el jugador pueda ver la pantalla (ej. 2.5 segundos)
        self.transicion_evento = Clock.schedule_once(self.ir_a_partida, 2.5)

    def on_leave(self, *args):
        # Por seguridad, si salimos de la pantalla manualmente, cancelar el evento
        if hasattr(self, 'transicion_evento') and self.transicion_evento:
            self.transicion_evento.cancel()

    def ir_a_partida(self, dt):
        self.manager.current = 'game_screen'
