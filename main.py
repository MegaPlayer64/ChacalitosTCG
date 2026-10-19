import os
import sys

# ==============================================================================
# 1. REGLA MAESTRA: RENDERIZADO POR SOFTWARE (LLVMpipe)
#    Elimina los conflictos de drivers NVIDIA, PRIME y compositores en Linux
# ==============================================================================
is_android = 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_ENTRYPOINT' in os.environ
is_linux = sys.platform.startswith('linux') and not is_android

if is_linux:
    # Fuerza el renderizado por CPU para garantizar estabilidad al 100%
    os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
    os.environ['vblank_mode'] = '0'
    os.environ['KIVY_GL_BACKEND'] = 'sdl2'
    os.environ['SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = '1'

    from kivy.config import Config
    Config.set('graphics', 'multisamples', '0')
    Config.set('graphics', 'width', '960')
    Config.set('graphics', 'height', '540')
    Config.set('graphics', 'fullscreen', '0')
    Config.set('graphics', 'resizable', '0')
    Config.write()

# ==============================================================================
# 2. CONFIGURACIÓN DEL PATH DE IMPORTACIONES
# ==============================================================================
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# ==============================================================================
# 3. IMPORTACIONES DE KIVY Y MOTOR
# ==============================================================================
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager

Window.size = (960, 540)
Window.clearcolor = (0.15, 0.15, 0.2, 1)

from src.infrastructure.path_manager import PathManager

try:
    from src.infrastructure.loaders.card_loader import CardLoader
    from src.domain.player import Player
    from src.domain.game_state import GameState
    from src.interfaces.controllers.human_controller import HumanController
    from src.interfaces.controllers.ai_controller import AIController
    from src.interfaces.view import ConsoleView
except ImportError as e:
    print(f"\n[ERROR CRITICO] Fallo de importación: {e}\n")
    sys.exit(1)


def resolve_safe_asset(relative_path: str) -> str | None:
    """Resuelve la ruta de un asset mediante PathManager validando su existencia física."""
    try:
        candidate = PathManager.get_asset_path(relative_path)
        if os.path.exists(candidate):
            return candidate

        alt_candidate = PathManager.get_asset_path(os.path.join("src", relative_path))
        if os.path.exists(alt_candidate):
            return alt_candidate
    except Exception as e:
        print(f">> [Main] Advertencia al resolver asset '{relative_path}': {e}")
    return None


class ChacalitosTCG(App):
    def build(self):
        beta_logo = resolve_safe_asset("images/BetaLogo.png")
        if beta_logo:
            try:
                self.icon = beta_logo
            except Exception as e:
                print(f">> [Main] No se pudo asignar el icono de la ventana: {e}")

        # Carga modular de vistas/pantallas
        from src.interfaces.menu_screen import MenuPrincipal
        from src.interfaces.game_screen import PantallaJuego
        from src.interfaces.selection_screen import PantallaSeleccion
        from src.interfaces.online_lobby_screen import OnlineLobbyScreen
        from src.interfaces.vs_screen import PantallaVersus
        from src.interfaces.result_screen import PantallaResultado
        from src.interfaces.inventory_screen import PantallaInventario
        from src.interfaces.banner_screen import PantallaBanner
        from src.interfaces.deck_builder_screen import PantallaDeckBuilder
        from src.interfaces.shop_screen import PantallaTienda
        from src.interfaces.options_screen import PantallaOpciones
        from src.interfaces.arcade_screen import PantallaArcade
        from src.interfaces.pantalla_misiones import PantallaMisiones
        from src.interfaces.battle_pass_view import BattlePassView
        from src.interfaces.login_screen import LoginScreen

        sm = ScreenManager()

        print("1. Cargando MenuPrincipal...")
        sm.add_widget(MenuPrincipal(name='menu_screen'))

        print("2. Cargando PantallaSeleccion...")
        sm.add_widget(PantallaSeleccion(name='selection_screen'))

        print("3. Cargando OnlineLobbyScreen...")
        sm.add_widget(OnlineLobbyScreen(name='online_lobby_screen'))

        print("4. Cargando PantallaVersus...")
        sm.add_widget(PantallaVersus(name='vs_screen'))

        print("5. Cargando PantallaJuego...")
        sm.add_widget(PantallaJuego(name='game_screen'))

        print("6. Cargando PantallaResultado...")
        sm.add_widget(PantallaResultado(name='result_screen'))

        print("7. Cargando PantallaInventario...")
        sm.add_widget(PantallaInventario(name='inventory_screen'))

        print("8. Cargando PantallaBanner...")
        sm.add_widget(PantallaBanner(name='banner_screen'))

        print("9. Cargando PantallaDeckBuilder...")
        sm.add_widget(PantallaDeckBuilder(name='deck_builder_screen'))

        print("10. Cargando PantallaTienda...")
        sm.add_widget(PantallaTienda(name='shop_screen'))

        print("11. Cargando PantallaOpciones...")
        sm.add_widget(PantallaOpciones(name='options_screen'))

        print("12. Cargando PantallaArcade...")
        sm.add_widget(PantallaArcade(name='arcade_screen'))

        print("13. Cargando PantallaMisiones...")
        sm.add_widget(PantallaMisiones(name='missions_screen'))

        print("14. Cargando BattlePassView...")
        sm.add_widget(BattlePassView(name='battle_pass'))

        print("15. Cargando LoginScreen...")
        sm.add_widget(LoginScreen(name='login_screen'))

        print(">> ¡Carga de pantallas completada con éxito!")

        sm.current = 'menu_screen'
        sm.app = self
        self.game_settings = None
        return sm

    def on_start(self):
        """Inicialización de la aplicación y actualización del lienzo."""
        Clock.schedule_once(self._refresh_viewport, 0.1)

        try:
            import threading
            from server.cloud_sync import CloudSyncManager
            if CloudSyncManager.is_logged_in():
                print(">> [Main] Sesión de usuario activa. Sincronizando en segundo plano...")
                threading.Thread(target=CloudSyncManager.sync_profile, daemon=True).start()
        except Exception as e:
            print(f">> [Main] Sincronización en segundo plano omitida: {e}")

    def _refresh_viewport(self, dt):
        try:
            Window.canvas.ask_update()
            Window.update_viewport()
            print(">> [Main] Canvas y viewport actualizados (Modo Software activo).")
        except Exception as e:
            print(f">> [Main] Advertencia al forzar refresco: {e}")


def main():
    try:
        print("Cargando Base de Datos de Cartas...")
        CardLoader.load_units()
        ChacalitosTCG().run()
    except Exception as e:
        print(f"\n[!] Error Inesperado: {e}")


if __name__ == '__main__':
    main()