from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Rectangle

class KivyView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=5, **kwargs)
        self.cells = {} # Diccionario para guardar las referencias a los botones (x, y)

    def build_interface(self, game_state):
        self.clear_widgets() # Limpia la pantalla antes de redibujar

        # 1. HEADER: Barras de Vida (Sustituye a get_hp_bar)
        header = BoxLayout(orientation='vertical', size_hint_y=0.2)
        for player in game_state.players:
            header.add_widget(Label(text=f"{player.name} - Energía: {player.current_energy}", size_hint_y=0.4))
            # Barra de vida real en lugar de caracteres '='
            pb = ProgressBar(max=80, value=player.health, size_hint_y=0.6)
            header.add_widget(pb)
        self.add_widget(header)

        # 2. TABLERO 6x5 (Sustituye a draw_board)
        board_layout = GridLayout(cols=6, rows=5, spacing=2, size_hint_y=0.5)
        for y in range(5):
            for x in range(6):
                unit = game_state.board.get_unit_at(x, y)
                
                # Creamos el botón de la celda
                cell_btn = Button(
                    text=unit.name[0].upper() if unit else ".",
                    background_normal='', # Para que los colores se vean sólidos
                    background_color=(0.2, 0.2, 0.2, 1) if not unit else (0.1, 0.5, 0.8, 1)
                )
                
                # Guardamos la referencia para actualizaciones rápidas
                self.cells[(x, y)] = cell_btn
                board_layout.add_widget(cell_btn)
        
        self.add_widget(board_layout)

        # 3. MANO DEL JUGADOR (Sustituye al print de la mano)
        hand_layout = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.2)
        p1 = game_state.players[0]
        for i, card in enumerate(p1.hand):
            card_btn = Button(
                text=f"{card.name}\n({card.cost})",
                font_size='12sp',
                halign='center'
            )
            hand_layout.add_widget(card_btn)
        
        self.add_widget(hand_layout)

        # 4. LOG DE MENSAJES (Sustituye a show_message)
        self.msg_label = Label(text="Inicia el turno...", size_hint_y=0.1, color=(1, 1, 0, 1))
        self.add_widget(self.msg_label)

    def update_message(self, message):
        self.msg_label.text = f">> {message}"