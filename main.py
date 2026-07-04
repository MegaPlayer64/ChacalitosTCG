# main.py
from kivy.uix import screenmanager
import os
import sys

# Agregamos la carpeta 'src' al path para que Python encuentre tus módulos
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

try:
    from src.infrastructure.loaders.card_loader import CardLoader
    from src.domain.player import Player
    from src.domain.game_state import GameState
    from src.application.game_engine import GameEngine
    from src.interfaces.controllers.human_controller import HumanController
    from src.interfaces.controllers.ai_controller import AIController
    from src.interfaces.view import ConsoleView
except ImportError as e:
    print(f"\n[ERROR CRITICO] Fallo de importación, posible dependencia circular: {e}\n")
    sys.exit(1)

# pyrefly: ignore [missing-import]
from kivy.app import App
# pyrefly: ignore [missing-import]
from kivy.uix.screenmanager import ScreenManager


def start_integration_test():
    print("\n" + "="*40)
    print("   INICIANDO TEST DE INTEGRACIÓN LBSB   ")
    print("="*40)

    # 1. Inicializar CardLoader
    print("\n[1] Cargando Base de Datos de Cartas...")
    csv_path = "src/data/cards.csv"
    all_cards = CardLoader.load_units(csv_path)
    print(f" -> Cartas cargadas exitosamente: {len(all_cards)} (Incluye Unidades, Spells y Buildings)")

    # 2. Configurar Jugadores
    print("\n[2] Configurando Jugadores...")
    p1 = Player(player_id=0, name="Jugador 1")
    p2 = Player(player_id=1, name="Jugador 2")
    
    # 3. Instanciar Motor y Estado
    print("\n[3] Instanciando GameState y Tablero 6x5...")
    
    # 4. Seleccionar el mazo
    print("Qué mazo quieres seleccionar: \n 1.- Dermapatch \n 2.- 3nai \n 3.- CT \n 4.- FEV \n 5.- News \n 6.- Tralareros \n 7.- Mazo Mish-A Pre ser Mish-A")
    deck1 = input("Mazo para Jugador 1: ")
    deck2 = input("Mazo para Jugador 2: ")
    if deck1 == "1":
        deck1 = "src/data/premade_decks/tag_theme/dermapatch_basic_deck.json"
    elif deck1 == "2":
        deck1 = "src/data/premade_decks/tag_theme/3nai_basic_deck.json"
    elif deck1 == "3":
        deck1 = "src/data/premade_decks/tag_theme/ct_basic_deck.json"
    elif deck1 == "4":  
        deck1 = "src/data/premade_decks/tag_theme/fev_basic_deck.json"
    elif deck1 == "5":
        deck1 = "src/data/premade_decks/tag_theme/news_basic_deck.json"
    elif deck1 == "6":
        deck1 = "src/data/premade_decks/tag_theme/tt_basic_deck.json"
    elif deck1 == "7":
        deck1 = "src/data/premade_decks/challenges/imagine_a_cool_name.json"
        
    if deck2 == "1":
        deck2 = "src/data/premade_decks/tag_theme/dermapatch_basic_deck.json"
    elif deck2 == "2":
        deck2 = "src/data/premade_decks/tag_theme/3nai_basic_deck.json"
    elif deck2 == "3":
        deck2 = "src/data/premade_decks/tag_theme/ct_basic_deck.json"
    elif deck2 == "4":  
        deck2 = "src/data/premade_decks/tag_theme/fev_basic_deck.json"
    elif deck2 == "5":
        deck2 = "src/data/premade_decks/tag_theme/news_basic_deck.json"
    elif deck2 == "6":
        deck2 = "src/data/premade_decks/tag_theme/tt_basic_deck.json"
    elif deck2 == "7":
        deck2 = "src/data/premade_decks/challenges/imagine_a_cool_name.json"
    # NOTA: Al instanciar GameState, internamente se cargan los mazos, se barajan y se roban 5 cartas a cada Jugador.
    state = GameState([p1, p2], deck1, deck2)
    # controllers = [HumanController(), AIController(player_id=1)]
    opcion = input("¿Quieres jugar tu contra la IA, contra otro jugador o simular un combate en tre IA? (1 para IA, 2 para otro jugador, 3 para IA vs IA): ")

 
    if opcion == "1":
        dificulty = input("¿Quieres jugar contra una IA [EASY, MEDIUM, HARD]?: ").upper()
        controllers = [HumanController(), AIController(player_id=1, difficulty=dificulty)]
        p2.is_ai = True
    elif opcion == "2":
        controllers = [HumanController(), HumanController()]
    else:
        dificulty = input("¿Quieres jugar contra una IA [EASY, MEDIUM, HARD]?: ").upper()
        controllers = [AIController(player_id=0, difficulty=dificulty), AIController(player_id=1, difficulty=dificulty)]
        p1.is_ai = True
        p2.is_ai = True
    engine = GameEngine(state, controllers)
    view = ConsoleView()

    # 4. Imprimir Estado Actual Post-Robo Inicial
    print("\n[4] Verificando Estado Inicial...")
    print(f" -> {p1.name} | Vida: {p1.health} HP | Cartas en mano: {len(p1.hand)} | Mazo restante: {len(p1.deck)}")
    print(f" -> {p2.name} | Vida: {p2.health} HP | Cartas en mano: {len(p2.hand)} | Mazo restante: {len(p2.deck)}")

    print("\n[5] Dibujando Tablero Inicial Limpio:")
    view.draw_board(state)

    print("\n[6] Iniciando Loop de Juego.")
    print(" -> INSTRUCCIÓN PARA TEST: Selecciona la acción [4] Jugar Carta.")
    print(" -> Prueba invocar una unidad para el J1 en X >= 2 (Debería fallar por restricción de zona).")
    print(" -> Prueba invocar una unidad para el J1 en X < 2  (Debería ser exitoso).")
    print("-" * 40 + "\n")

    # Arrancamos el motor
    engine.run()

class LBSBGameApp(App):
    def build(self):
        from src.interfaces.menu_screen import MenuPrincipal
        from src.interfaces.game_screen import PantallaJuego

        sm = ScreenManager()
        
        # Registrar pantallas vinculándolas por su identificador de texto
        sm.add_widget(MenuPrincipal(name='menu_screen'))
        
        from src.interfaces.selection_screen import PantallaSeleccion
        sm.add_widget(PantallaSeleccion(name='selection_screen'))
        
        from src.interfaces.vs_screen import PantallaVersus
        sm.add_widget(PantallaVersus(name='vs_screen'))
        
        sm.add_widget(PantallaJuego(name='game_screen'))
        
        from src.interfaces.result_screen import PantallaResultado
        sm.add_widget(PantallaResultado(name='result_screen'))

        from src.interfaces.inventory_screen import PantallaInventario
        sm.add_widget(PantallaInventario(name='inventory_screen'))
        
        from src.interfaces.banner_screen import PantallaBanner
        sm.add_widget(PantallaBanner(name='banner_screen'))

        from src.interfaces.deck_builder_screen import PantallaDeckBuilder
        sm.add_widget(PantallaDeckBuilder(name='deck_builder_screen'))

        from src.interfaces.shop_screen import PantallaTienda
        sm.add_widget(PantallaTienda(name='shop_screen'))

        print(f"Pantallas registradas: {sm.screen_names}")
        
        # Guardar una referencia de la app en el manager para facilitar accesos directos
        sm.app = self 
        self.game_settings = None
        return sm

def main():
    try:
        print("Cargando Base de Datos de Cartas...")
        CardLoader.load_units("src/data/cards.csv")
        LBSBGameApp().run()
    except Exception as e:
        print(f"\n[!] Error Inesperado: {e}")

if __name__ == '__main__':
    main()