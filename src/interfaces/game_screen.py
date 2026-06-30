from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

from src.domain.game_state import GameState
from src.domain.action import Action, ActionType


class PantallaJuego(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout_tablero_global = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.unidad_seleccionada_coords = None 
        
        # --- 1. BARRA SUPERIOR (Datos de la partida y Turno) ---
        barra_info = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        
        self.lbl_j1 = Label(text="J1 (Tú): 80 HP\nEnergía: 1/1", halign='left', markup=True)
        self.lbl_turno = Label(text="[b]TURNO --[/b]", halign='center', markup=True, font_size='18sp')
        self.lbl_j2 = Label(text="J2 (Rival): 80 HP\nEnergía: 1/1", halign='right', markup=True)
        
        btn_rendirse = Button(text="Rendirse", size_hint_x=0.15, background_color=(0.5, 0.2, 0.2, 1))
        btn_rendirse.bind(on_release=lambda x: self.volver_al_menu())
        
        btn_reiniciar = Button(text="Reiniciar", size_hint_x=0.15, background_color=(0.2, 0.6, 0.8, 1))
        btn_reiniciar.bind(on_release=self.reiniciar_partida)
        
        btn_pasar_turno = Button(text="Pasar\nTurno", size_hint_x=0.15, background_color=(0.8, 0.6, 0.1, 1))
        btn_pasar_turno.bind(on_release=self.pasar_turno)
        
        self.btn_atacar_base = Button(text="Atacar\nBase", size_hint_x=0.15, background_color=(0.8, 0.2, 0.2, 1))
        self.btn_atacar_base.bind(on_release=self.atacar_base)
        
        barra_info.add_widget(self.lbl_j1)
        barra_info.add_widget(btn_rendirse)
        barra_info.add_widget(btn_reiniciar)
        barra_info.add_widget(self.lbl_turno) # Centro
        barra_info.add_widget(self.btn_atacar_base)
        barra_info.add_widget(btn_pasar_turno)
        barra_info.add_widget(self.lbl_j2)
        
        layout_tablero_global.add_widget(barra_info)
        
        # --- 2. CUADRÍCULA DE JUEGO (6x5) ---
        grilla_tablero = GridLayout(cols=6, rows=5, spacing=4, size_hint_y=0.6)
        self.celdas_graficas = {}
        
        for y in range(5):
            for x in range(6):
                btn_celda = Button(text=".", font_size='14sp')
                btn_celda.coordenadas = (x, y)
                btn_celda.bind(on_release=self.celda_clickeada)
                
                grilla_tablero.add_widget(btn_celda)
                self.celdas_graficas[(x, y)] = btn_celda
                
        layout_tablero_global.add_widget(grilla_tablero)
        
        # --- 3. ZONA INFERIOR (Mano) ---
        self.layout_mano = BoxLayout(orientation='horizontal', size_hint_y=0.25, spacing=5)
        self.layout_mano.add_widget(Label(text="[Zona de Mano - Esperando Cartas]", markup=True))
        
        layout_tablero_global.add_widget(self.layout_mano)
        self.add_widget(layout_tablero_global)
        
        self.game_state = None
        self.ai_controller = None 
        self.carta_seleccionada_index = None

    def celda_clickeada(self, instance):
        x, y = instance.coordenadas
        jugador = self.game_state.get_current_player()
        unidad_en_celda = self.game_state.board.get_unit_at(x, y)
        
        # MODO A: RESOLVIENDO HABILIDAD PENDIENTE (Targeting)
        if getattr(self.game_state, 'pending_ability', None):
            accion = Action(player_id=jugador.id, type=ActionType.RESOLVE_ABILITY, payload={'target': (x, y)})
            if self.game_state.apply_action(accion):
                print(f">> Habilidad resuelta en ({x}, {y})")
            else:
                print(f">> [!] Resolución inválida en ({x}, {y})")
            self.actualizar_interfaz_completa()
            return
        
        # MODO B: CARTA DE LA MANO SELECCIONADA (Invocación o Spell)
        if self.carta_seleccionada_index is not None:
            carta = jugador.hand[self.carta_seleccionada_index]
            is_spell = getattr(carta, 'card_type', 'unit').lower() == 'spell'
            tipo_accion = ActionType.PLAY_SPELL if is_spell else ActionType.PLAY_CARD
            payload = {'card_index': self.carta_seleccionada_index, 'target' if is_spell else 'to': (x, y)}
            
            accion = Action(player_id=jugador.id, type=tipo_accion, payload=payload)
            if self.game_state.apply_action(accion):
                self.carta_seleccionada_index = None
                self.actualizar_interfaz_completa()
            else:
                print(f">> [!] Invocación/Hechizo denegado en ({x}, {y})")
            return

        # MODO C: UNIDAD DEL TABLERO SELECCIONADA (Mover, Atacar o Activar)
        if self.unidad_seleccionada_coords:
            origen = self.unidad_seleccionada_coords
            
            if origen == (x, y):
                accion = Action(player_id=jugador.id, type=ActionType.ACTIVATE_ABILITY, payload={'from': origen})
            elif unidad_en_celda and unidad_en_celda.owner_id != jugador.id:
                accion = Action(player_id=jugador.id, type=ActionType.ATTACK, payload={'from': origen, 'target': (x, y)})
            else:
                accion = Action(player_id=jugador.id, type=ActionType.MOVE, payload={'from': origen, 'to': (x, y)})
            
            if self.game_state.apply_action(accion):
                print(f">> Acción realizada desde {origen} hacia {(x, y)}")
            else:
                print(f">> [!] Acción denegada desde {origen}")
                
            self.unidad_seleccionada_coords = None
            self.actualizar_interfaz_completa()
            return

        # MODO D: SELECCIÓN INICIAL DE UNIDAD
        if unidad_en_celda and unidad_en_celda.owner_id == jugador.id:
            self.unidad_seleccionada_coords = (x, y)
            self.celdas_graficas[(x, y)].background_color = (0.2, 0.8, 0.2, 1) # Feedback verde

    def atacar_base(self, instance):
        if not self.unidad_seleccionada_coords:
            print(">> [!] Selecciona una unidad tuya primero para atacar la base.")
            return
            
        jugador = self.game_state.get_current_player()
        origen = self.unidad_seleccionada_coords
        accion = Action(player_id=jugador.id, type=ActionType.ATTACK, payload={'from': origen, 'target': 'B'})
        
        if self.game_state.apply_action(accion):
            print(f">> ¡Ataque a la base ejecutado desde {origen}!")
        else:
            print(f">> [!] Ataque a la base denegado.")
            
        self.unidad_seleccionada_coords = None
        self.actualizar_interfaz_completa()

    def dibujar_mano(self, mano_jugador):
        self.layout_mano.clear_widgets()
        self.carta_seleccionada_index = None

        if not mano_jugador:
            self.layout_mano.add_widget(Label(text="[Mano Vacía]"))
            return

        for i, carta in enumerate(mano_jugador):
            texto_carta = f"{carta['nombre']}\nCoste: {carta['coste']}E"
            
            btn_carta = Button(
                text=texto_carta,
                font_size='14sp',
                background_color=(0.1, 0.1, 0.3, 1) if carta['tipo'] == 'spell' else (0.3, 0.3, 0.3, 1),
                halign='center'
            )
            btn_carta.indice_mano = i 
            btn_carta.bind(on_release=self.seleccionar_carta)
            self.layout_mano.add_widget(btn_carta)

    def seleccionar_carta(self, instance):
        for btn in self.layout_mano.children:
            # Restaurar colores según si es hechizo o unidad
            es_spell = 'E' in btn.text and btn.background_color == (0.8, 0.6, 0.1, 1) # Detectar si estaba dorada
            btn.background_color = (0.3, 0.3, 0.3, 1)

        instance.background_color = (0.8, 0.6, 0.1, 1) # Dorado seleccionado
        self.carta_seleccionada_index = instance.indice_mano

    def actualizar_interfaz_completa(self):
        if not self.game_state:
            return
            
        jugador_actual = self.game_state.get_current_player()
        p1 = self.game_state.players[0]
        p2 = self.game_state.players[1]
        
        # Estado de la IA / Turno
        turno_actual = getattr(self.game_state, 'turn', 0)
        self.lbl_turno.text = f"[color=aaffaa][b]TURNO {turno_actual}[/b][/color]\nActivo: {jugador_actual.name}"
        
        pending = getattr(self.game_state, 'pending_ability', None)
        lbl_estado = "\n[color=ff3333][b]¡SELECCIONA OBJETIVO![/b][/color]" if pending else ""
        
        self.lbl_j1.text = f"J1: {p1.health} HP\nEnergía: {getattr(p1, 'current_energy', 0)}/{getattr(p1, 'max_energy', 0)}" + (lbl_estado if self.game_state.current_player_id == 0 else "")
        self.lbl_j2.text = f"J2: {p2.health} HP\nEnergía: {getattr(p2, 'current_energy', 0)}/{getattr(p2, 'max_energy', 0)}" + (lbl_estado if self.game_state.current_player_id == 1 else "")
        
        # Limpiar Tablero Visual
        for (cx, cy), btn in self.celdas_graficas.items():
            btn.text = "."
            btn.background_color = (0.15, 0.15, 0.15, 1) 
            
        # Redibujar Tropas
        for (cx, cy), unit in self.game_state.board.grid.items():
            boton = self.celdas_graficas[(cx, cy)]
            boton.text = f"{unit.name}\n{unit.attack} ⚔️ | {unit.health} ❤️"
            boton.background_color = (0.2, 0.5, 0.8, 1) if unit.owner_id == 0 else (0.8, 0.3, 0.3, 1)

        # Redibujar Mano
        mano_formateada = [
            {"nombre": c.name, "coste": c.cost, "tipo": getattr(c, 'card_type', 'unit')} 
            for c in jugador_actual.hand
        ]
        self.dibujar_mano(mano_formateada)
        
        # Evaluar Condición de Victoria
        if p1.health <= 0 or p2.health <= 0:
            ganador = p1 if p2.health <= 0 else p2
            perdedor = p2 if ganador == p1 else p1
            self.finalizar_partida_ui(ganador, perdedor)

    def on_pre_enter(self, *args):
        from src.domain.player import Player
        from src.interfaces.controllers.ai_controller import AIController

        app = self.manager.app
        settings = getattr(app, 'game_settings', None)

        if not settings:
            settings = {
                'p1': {'tipo': 'Humano', 'mazo': 'src/data/premade_decks/challenges/imagine_a_cool_name.json'},
                'p2': {'tipo': 'Humano', 'mazo': 'src/data/premade_decks/tag_theme/fev_basic_deck.json'}
            }

        p1 = Player(player_id=0, name="Jugador 1")
        p2 = Player(player_id=1, name="Jugador 2" if 'Humano' in settings['p2']['tipo'] else f"IA ({settings['p2']['tipo']})")

        def _dificultad(tipo):
            if 'Fácil' in tipo: return 'EASY'
            if 'Normal' in tipo: return 'MEDIUM'
            return 'HARD'

        self.ai_controller = None
        p1.is_ai = 'Humano' not in settings['p1']['tipo']
        p2.is_ai = 'Humano' not in settings['p2']['tipo']

        if p2.is_ai:
            self.ai_controller = AIController(player_id=1, difficulty=_dificultad(settings['p2']['tipo']), delay=0)
        elif p1.is_ai:
            self.ai_controller = AIController(player_id=0, difficulty=_dificultad(settings['p1']['tipo']), delay=0)

        # OJO AQUÍ: Asegúrate que GameState inicializa turn=1 si quieres que empiece en 1.
        self.game_state = GameState([p1, p2], settings['p1']['mazo'], settings['p2']['mazo'])

        self.carta_seleccionada_index = None
        self.unidad_seleccionada_coords = None
        self._ia_corriendo = False
        self._ia_fallos_consecutivos = 0
        
        # En on_pre_enter de game_screen.py
        p1 = Player(player_id=0, name="Jugador 1")
        p1.crisby_cost_reduction_active = False
        p1.d_economia_cost_reduction_active = False

        p2 = Player(player_id=1, name="Jugador 2")
        p2.crisby_cost_reduction_active = False
        p2.d_economia_cost_reduction_active = False

        self.actualizar_interfaz_completa()
        self._ejecutar_turno_ia_si_toca()

    def pasar_turno(self, instance):
        jugador_actual = self.game_state.get_current_player()
        accion = Action(player_id=jugador_actual.id, type=ActionType.END_TURN, payload={})
        
        self.game_state.apply_action(accion)
        self.carta_seleccionada_index = None
        self.unidad_seleccionada_coords = None
        self.actualizar_interfaz_completa()
        self._ejecutar_turno_ia_si_toca()

    def _ejecutar_turno_ia_si_toca(self):
        if not self.ai_controller or not self.game_state or getattr(self, '_ia_corriendo', False):
            return
            
        jugador_actual = self.game_state.get_current_player()
        if jugador_actual.id == self.ai_controller.player_id and getattr(jugador_actual, 'is_ai', False):
            self._ia_corriendo = True
            self._ia_fallos_consecutivos = 0
            Clock.schedule_once(self._tick_ia, 0.6)

    def _tick_ia(self, dt):
        if not self.ai_controller or not self.game_state:
            self._ia_corriendo = False
            return

        jugador_actual = self.game_state.get_current_player()
        if not (jugador_actual.id == self.ai_controller.player_id and getattr(jugador_actual, 'is_ai', False)):
            self._ia_corriendo = False
            return

        if self._ia_fallos_consecutivos >= 3:
            print(">> [IA] Demasiados fallos. Forzando fin de turno.")
            accion = Action(player_id=self.ai_controller.player_id, type=ActionType.END_TURN, payload={})
            self.game_state.apply_action(accion)
            self.actualizar_interfaz_completa()
            self._ia_corriendo = False
            return

        accion = self.ai_controller.get_action(self.game_state)
        exito = self.game_state.apply_action(accion)
        self.actualizar_interfaz_completa()

        if accion.type == ActionType.END_TURN:
            self._ia_corriendo = False
            return

        if not exito:
            self._ia_fallos_consecutivos += 1
        else:
            self._ia_fallos_consecutivos = 0

        jugador_tras_accion = self.game_state.get_current_player()
        if jugador_tras_accion.id == self.ai_controller.player_id and getattr(jugador_tras_accion, 'is_ai', False):
            Clock.schedule_once(self._tick_ia, 0.4)
        else:
            self._ia_corriendo = False

    def finalizar_partida_ui(self, ganador_obj, perdedor_obj):
        # Programamos el cambio para dentro de 0.1 segundos
        # Esto evita que Kivy crashee por cambiar de pantalla durante un cálculo
        def _cambiar(dt):
            pantalla_resultados = self.manager.get_screen('result_screen')
            pantalla_resultados.configurar(
                ganador_nombre=ganador_obj.name,
                perdedor_nombre=perdedor_obj.name,
                jugador_local_id=0,
                ganador_id=ganador_obj.id
            )
            self.manager.current = 'result_screen'
            
        Clock.schedule_once(_cambiar, 0.1)

    def reiniciar_partida(self, instance):
        self._ia_corriendo = False
        self.manager.current = 'selection_screen'

    def volver_al_menu(self):
        self._ia_corriendo = False
        self.manager.current = 'menu_screen'