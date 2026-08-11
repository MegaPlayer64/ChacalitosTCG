from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from src.interfaces.controllers.online_controller import OnlineController
from src.domain.grid_background import FondoCuadriculado
import json
import os

class OnlineLobbyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Fondo E-ink compatible (Alto contraste)
        fondo_grilla = FondoCuadriculado(size=self.size)
        self.add_widget(fondo_grilla, index=0)
        
        # Layout Principal
        self.layout_global = BoxLayout(orientation='vertical', padding=40, spacing=20)
        
        # Título
        lbl_titulo = Label(
            text="[b]LOBBY MULTIJUGADOR[/b]", 
            markup=True, 
            font_size='28sp', 
            size_hint_y=0.15,
            color=(0, 0, 0, 1) # Negro para alto contraste
        )
        self.layout_global.add_widget(lbl_titulo)
        
        # Panel de Estado Dinámico
        self.lbl_estado = Label(
            text="Estado: Desconectado", 
            font_size='20sp', 
            size_hint_y=0.1,
            color=(0.2, 0.2, 0.2, 1)
        )
        self.layout_global.add_widget(self.lbl_estado)
        
        # Grid para Inputs
        self.decks = {}
        self.cargar_mazos()
        
        grid_inputs = GridLayout(cols=2, spacing=15, size_hint_y=0.5, size_hint_x=0.8, pos_hint={'center_x': 0.5})
        
        # Labels e Inputs (Alto Contraste)
        grid_inputs.add_widget(Label(text="IP del Servidor:", font_size='18sp', color=(0, 0, 0, 1), halign='right'))
        self.input_ip = TextInput(text="127.0.0.1", font_size='18sp', multiline=False)
        grid_inputs.add_widget(self.input_ip)
        
        grid_inputs.add_widget(Label(text="Puerto:", font_size='18sp', color=(0, 0, 0, 1), halign='right'))
        self.input_port = TextInput(text="8888", font_size='18sp', multiline=False)
        grid_inputs.add_widget(self.input_port)
        
        grid_inputs.add_widget(Label(text="Nombre Jugador:", font_size='18sp', color=(0, 0, 0, 1), halign='right'))
        self.input_name = TextInput(text="Jugador1", font_size='18sp', multiline=False)
        grid_inputs.add_widget(self.input_name)
        
        grid_inputs.add_widget(Label(text="Mazo:", font_size='18sp', color=(0, 0, 0, 1), halign='right'))
        opciones_mazo = [f"{nombre} ({len(cartas)} cartas)" for nombre, cartas in self.decks.items()]
        texto_inicial = opciones_mazo[0] if opciones_mazo else "Sin mazos guardados"
        self.spn_deck = Spinner(text=texto_inicial, values=opciones_mazo, font_size='16sp')
        grid_inputs.add_widget(self.spn_deck)
        
        self.layout_global.add_widget(grid_inputs)
        
        # Botones
        layout_botones = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=0.2, size_hint_x=0.8, pos_hint={'center_x': 0.5})
        
        self.btn_buscar = Button(
            text="BUSCAR PARTIDA", 
            font_size='20sp', 
            background_color=(0.1, 0.8, 0.1, 1), # Verde oscuro
            color=(1, 1, 1, 1)
        )
        self.btn_buscar.bind(on_release=self.iniciar_busqueda)
        
        self.btn_cancelar = Button(
            text="CANCELAR / VOLVER", 
            font_size='20sp', 
            background_color=(0.8, 0.1, 0.1, 1), # Rojo oscuro
            color=(1, 1, 1, 1)
        )
        self.btn_cancelar.bind(on_release=self.volver_menu)
        
        layout_botones.add_widget(self.btn_buscar)
        layout_botones.add_widget(self.btn_cancelar)
        self.layout_global.add_widget(layout_botones)
        
        self.add_widget(self.layout_global)
        
        # Instancia del Controlador
        self.online_controller = OnlineController()
        
        # Registrar Callbacks
        self.online_controller.on_match_found = self.al_encontrar_partida
        self.online_controller.on_disconnect = self.al_desconectar

    def on_pre_enter(self, *args):
        self.cargar_mazos()
        opciones_mazo = [f"{nombre} ({len(cartas)} cartas)" for nombre, cartas in self.decks.items()]
        self.spn_deck.values = opciones_mazo
        if opciones_mazo:
            if self.spn_deck.text not in opciones_mazo:
                self.spn_deck.text = opciones_mazo[0]
        else:
            self.spn_deck.text = "Sin mazos guardados"

    def cargar_mazos(self):
        ruta = "src/data/user_profile.json"
        if os.path.exists(ruta):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    perfil = json.load(f)
                    self.decks = perfil.get("decks", {})
            except Exception:
                self.decks = {}
        else:
            self.decks = {}

    def iniciar_busqueda(self, instance):
        seleccion = self.spn_deck.text
        if "Sin mazos guardados" in seleccion or "cartas" not in seleccion:
            self.lbl_estado.text = "Selecciona un mazo válido antes de buscar partida"
            return
            
        nombre_mazo = seleccion.split(" (")[0]
        mazo_ids = self.decks.get(nombre_mazo, [])
        if len(mazo_ids) < 40:
            self.lbl_estado.text = "Selecciona un mazo válido antes de buscar partida"
            return

        ip = self.input_ip.text.strip()
        puerto = int(self.input_port.text.strip()) if self.input_port.text.strip().isdigit() else 8888
        nombre = self.input_name.text.strip() or "JugadorAnonimo"
        
        self.lbl_estado.text = "Estado: Conectando al servidor..."
        self.btn_buscar.disabled = True
        
        self.online_controller.connect(ip, puerto, nombre)
        
        import kivy.clock
        kivy.clock.Clock.schedule_once(lambda dt: self._enviar_join(nombre, mazo_ids), 0.5)

    def _enviar_join(self, nombre, mazo_ids):
        if self.online_controller.connected:
            self.lbl_estado.text = "Estado: Buscando oponente..."
            self.manager.local_deck = mazo_ids
            self.online_controller.join_matchmaking(deck=mazo_ids)
        else:
            self.lbl_estado.text = "Estado: Error de conexión."
            self.btn_buscar.disabled = False

    def al_encontrar_partida(self, msg):
        self.lbl_estado.text = f"¡Partida Encontrada contra {msg.get('opponent_name')}! Cargando tablero..."
        
        # Guardar controller y rol en el App Manager para PantallaJuego
        self.manager.online_controller = self.online_controller
        self.manager.online_role = msg.get("player_role") 
        self.manager.online_opponent = msg.get("opponent_name")
        self.manager.opponent_deck = msg.get("opponent_deck", [])
        self.manager.online_seed = msg.get("seed", 0)
        self.manager.is_online_game = True
        
        # Transición
        import kivy.clock
        kivy.clock.Clock.schedule_once(lambda dt: self.ir_a_juego(), 1)
        
    def ir_a_juego(self):
        self.manager.current = 'game_screen'

    def al_desconectar(self, msg=None):
        self.lbl_estado.text = "Estado: Desconectado."
        self.btn_buscar.disabled = False
        
    def volver_menu(self, instance):
        if self.online_controller.connected:
            self.online_controller.disconnect()
        self.lbl_estado.text = "Estado: Desconectado."
        self.btn_buscar.disabled = False
        self.manager.current = 'menu_screen'
