import os
import sys
from kivy.utils import platform

# 1. AGREGAR 'src' AL PATH DE INMEDIATO (Para que las importaciones de abajo funcionen)
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# 2. PARÁMETROS DE ENTORNO GRÁFICOS (Mismo orden para evitar congelamientos)
if platform == 'android':
    pass

elif platform == 'linux':
    os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
    os.environ['vblank_mode'] = '0'
    os.environ['KIVY_GL_BACKEND'] = 'sdl2'
    os.environ['SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = '1'
    
    from kivy.config import Config
    Config.set('graphics', 'width', '960')
    Config.set('graphics', 'height', '540')
    Config.set('graphics', 'fullscreen', '0')
    Config.write()

elif platform == 'win':
    from kivy.config import Config
    Config.set('graphics', 'width', '1280')
    Config.set('graphics', 'height', '720')
    Config.set('graphics', 'fullscreen', '0')
    Config.write()

# 3. AHORA SÍ, LAS IMPORTACIONES DEL MOTOR Y KIVY
from kivy.uix import screenmanager

try:
    # Como el path se agregó en el paso 1, estas importaciones ya no fallarán:
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

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

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

        from src.interfaces.options_screen import PantallaOpciones
        sm.add_widget(PantallaOpciones(name='options_screen'))
        
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