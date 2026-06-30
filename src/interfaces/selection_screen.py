import json
import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner

class PantallaSeleccion(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ruta_perfil = "src/data/user_profile.json"
        self.mazos = []  # Diccionario interno de mapeo de rutas/orígenes

        layout_global = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Título
        layout_global.add_widget(Label(text="[b]CONFIGURAR PARTIDA[/b]", font_size='24sp', markup=True, size_hint_y=0.15))
        
        # Opciones Jugador 1
        panel_j1 = BoxLayout(orientation='vertical', spacing=10)
        panel_j1.add_widget(Label(text="Jugador 1", font_size='18sp'))
        
        self.spinner_tipo_j1 = Spinner(
            text='Humano',
            values=('Humano', 'IA Fácil', 'IA Normal', 'IA Difícil'),
            size_hint=(None, None), size=(200, 44), pos_hint={'center_x': 0.5}
        )
        
        self.spinner_mazo_j1 = Spinner(
            text='Cargando...',
            values=(),
            size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5}
        )
        
        panel_j1.add_widget(self.spinner_tipo_j1)
        panel_j1.add_widget(self.spinner_mazo_j1)
        layout_global.add_widget(panel_j1)
        
        # Opciones Jugador 2
        panel_j2 = BoxLayout(orientation='vertical', spacing=10)
        panel_j2.add_widget(Label(text="Jugador 2", font_size='18sp'))
        
        self.spinner_tipo_j2 = Spinner(
            text='Humano',
            values=('Humano', 'IA Fácil', 'IA Normal', 'IA Difícil'),
            size_hint=(None, None), size=(200, 44), pos_hint={'center_x': 0.5}
        )
        self.spinner_mazo_j2 = Spinner(
            text='Cargando...',
            values=(),
            size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5}
        )
        
        panel_j2.add_widget(self.spinner_tipo_j2)
        panel_j2.add_widget(self.spinner_mazo_j2)
        layout_global.add_widget(panel_j2)
        
        # Botones de Acción
        layout_botones = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=0.2)
        btn_volver = Button(text="VOLVER", background_color=(0.8, 0.2, 0.2, 1))
        btn_volver.bind(on_release=lambda x: self.cambiar_pantalla('menu_screen'))
        
        btn_iniciar = Button(text="INICIAR PARTIDA", background_color=(0.2, 0.8, 0.2, 1))
        btn_iniciar.bind(on_release=self.iniciar_partida)
        
        layout_botones.add_widget(btn_volver)
        layout_botones.add_widget(btn_iniciar)
        layout_global.add_widget(layout_botones)
        
        self.add_widget(layout_global)

    def on_enter(self):
        """Se ejecuta automáticamente al cargar la pantalla. Actualiza la lista de mazos."""
        self.mazos = self.obtener_lista_mazos()
        opciones_visuales = [m['nombre'] for m in self.mazos]
        
        if opciones_visuales:
            self.spinner_mazo_j1.values = tuple(opciones_visuales)
            self.spinner_mazo_j2.values = tuple(opciones_visuales)
            
            # Evitar que el texto quede desactualizado si se eliminó algún mazo
            if self.spinner_mazo_j1.text not in opciones_visuales:
                self.spinner_mazo_j1.text = opciones_visuales[0]
            if self.spinner_mazo_j2.text not in opciones_visuales:
                self.spinner_mazo_j2.text = opciones_visuales[0]

    def obtener_lista_mazos(self):
        mazos = []
        
        # 1. Escanear los mazos premade de las carpetas de datos
        base_path = "src/data/premade_decks"
        if os.path.exists(base_path):
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if file.endswith('.json'):
                        full_path = os.path.join(root, file).replace('\\', '/')
                        mazos.append({
                            'nombre': f"[Premade] {file.replace('.json', '')}", 
                            'ruta': full_path,
                            'tipo_origen': 'archivo'
                        })
        
        # 2. Inyectar dinámicamente tus mazos guardados desde el perfil de usuario
        if os.path.exists(self.ruta_perfil):
            try:
                with open(self.ruta_perfil, "r", encoding="utf-8") as f:
                    perfil = json.load(f)
                
                decks_guardados = perfil.get("decks", {})
                for nombre_mazo in decks_guardados.keys():
                    mazos.append({
                        'nombre': f"[Personal] {nombre_mazo}",
                        'ruta': nombre_mazo, # Almacenamos el identificador del mazo para el perfil
                        'tipo_origen': 'perfil'
                    })
            except Exception as e:
                print(f"[!] Error al leer mazos personales del perfil: {e}")

        # Fallback de seguridad
        if not mazos:
            mazos.append({
                'nombre': '[Premade] Dermapatch', 
                'ruta': 'src/data/premade_decks/tag_theme/dermapatch_basic_deck.json',
                'tipo_origen': 'archivo'
            })
            
        return mazos

    def cambiar_pantalla(self, nombre_pantalla):
        self.manager.current = nombre_pantalla

    def iniciar_partida(self, instance):
        # Encontrar las referencias seleccionadas
        config_j1 = next((m for m in self.mazos if m['nombre'] == self.spinner_mazo_j1.text), None)
        config_j2 = next((m for m in self.mazos if m['nombre'] == self.spinner_mazo_j2.text), None)
        
        if not config_j1 or not config_j2:
            return

        # El game_settings empaquetará tanto la ruta física o la key del perfil como el origen correspondiente
        self.manager.app.game_settings = {
            'p1': {
                'tipo': self.spinner_tipo_j1.text, 
                'mazo': config_j1['ruta'],
                'origen': config_j1['tipo_origen']
            },
            'p2': {
                'tipo': self.spinner_tipo_j2.text, 
                'mazo': config_j2['ruta'],
                'origen': config_j2['tipo_origen']
            }
        }
        
        self.cambiar_pantalla('game_screen')