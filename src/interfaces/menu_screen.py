import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock

from src.domain.grid_background import FondoCuadriculado
from src.domain.audio_manager import AudioManager
from server.cloud_sync import CloudSyncManager


class MenuPrincipal(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Layout principal de toda la pantalla (Vertical)
        layout_global = BoxLayout(orientation='vertical', padding=[25, 15, 25, 15], spacing=12)

        # Fondo cuadriculado interactivo
        fondo_grilla = FondoCuadriculado(size=self.size)
        self.add_widget(fondo_grilla, index=0)

        # --- 1. BARRA SUPERIOR DE ESTADO CLOUD / CUENTA ---
        self.layout_auth = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=38,
            spacing=8
        )

        self.lbl_auth_status = Label(
            text="⚪ Modo Local",
            markup=True,
            font_size='13sp',
            halign='right',
            valign='middle'
        )
        self.lbl_auth_status.bind(size=self.lbl_auth_status.setter('text_size'))

        self.btn_auth_action = Button(
            text="🔑 Iniciar Sesión",
            font_size='12sp',
            size_hint=(None, None),
            size=(135, 34),
            background_color=(0.2, 0.5, 0.8, 1)
        )
        self.btn_auth_action.bind(on_release=self.accion_auth_boton)

        self.btn_account_manage = Button(
            text="⚙️",
            font_size='14sp',
            size_hint=(None, None),
            size=(34, 34),
            background_color=(0.3, 0.35, 0.4, 1)
        )
        self.btn_account_manage.bind(on_release=lambda x: self.cambiar_pantalla('login_screen'))

        self.layout_auth.add_widget(self.lbl_auth_status)
        self.layout_auth.add_widget(self.btn_auth_action)
        self.layout_auth.add_widget(self.btn_account_manage)
        layout_global.add_widget(self.layout_auth)

        # --- 2. LOGO ---
        imagen_logo = Image(
            source='src/images/BetaLogo.png',
            allow_stretch=True,
            keep_ratio=True,
            size_hint_y=0.30,
            pos_hint={'top': 1}
        )
        layout_global.add_widget(imagen_logo)

        # --- 3. CONTENEDOR DE BOTONES ---
        layout_botones = BoxLayout(
            orientation='vertical', 
            spacing=10, 
            size_hint_x=0.62, 
            pos_hint={'center_x': 0.5}
        )

        layout_botones2 = BoxLayout(
            orientation='horizontal', 
            spacing=10, 
            size_hint_x=1, 
            size_hint_y=None, 
            height=46, 
            pos_hint={'center_x': 0.5}
        )

        layout_misiones_pase = BoxLayout(
            orientation='horizontal', 
            spacing=10, 
            size_hint_x=1, 
            size_hint_y=None, 
            height=46, 
            pos_hint={'center_x': 0.5}
        )

        btn_jugar = Button(text="PARTIDA LOCAL", font_size='16sp', size_hint_y=None, height=46)
        btn_online = Button(text="MULTIJUGADOR ONLINE", font_size='16sp', size_hint_y=None, height=46)
        btn_arcade = Button(text="TORRE", font_size='16sp', size_hint_y=None, height=46)
        btn_misiones = Button(text="MISIONES DIARIAS", font_size='15sp', size_hint_y=None, height=46, background_color=(0.2, 0.6, 0.8, 1))
        btn_pase = Button(text="PASE DE BATALLA", font_size='15sp', size_hint_y=None, height=46, background_color=(0.85, 0.55, 0.1, 1))
        btn_mazos = Button(text="COLECCIÓN Y MAZOS", font_size='16sp', size_hint_y=None, height=46)
        btn_gacha = Button(text="TIENDA / BANNERS", font_size='16sp', size_hint_y=None, height=46)
        btn_opciones = Button(text="OPCIONES", font_size='16sp', size_hint_y=None, height=46)
        btn_salir = Button(text="SALIR", font_size='16sp', size_hint_y=None, height=46)

        # Enlaces de navegación
        btn_jugar.bind(on_release=lambda x: self.cambiar_pantalla('selection_screen'))
        btn_online.bind(on_release=lambda x: self.cambiar_pantalla('online_lobby_screen'))
        btn_arcade.bind(on_release=lambda x: self.cambiar_pantalla('arcade_screen'))
        btn_misiones.bind(on_release=lambda x: self.cambiar_pantalla('missions_screen'))
        btn_pase.bind(on_release=lambda x: self.cambiar_pantalla('battle_pass'))
        btn_mazos.bind(on_release=lambda x: self.cambiar_pantalla('inventory_screen'))
        btn_gacha.bind(on_release=lambda x: self.cambiar_pantalla('banner_screen'))
        btn_opciones.bind(on_release=lambda x: self.cambiar_pantalla('options_screen'))
        btn_salir.bind(on_release=lambda x: self.manager.app.stop() if hasattr(self.manager, 'app') else exit())

        layout_botones2.add_widget(btn_jugar)
        layout_botones2.add_widget(btn_online)
        layout_botones2.add_widget(btn_arcade)
        layout_botones.add_widget(layout_botones2)

        layout_misiones_pase.add_widget(btn_misiones)
        layout_misiones_pase.add_widget(btn_pase)
        layout_botones.add_widget(layout_misiones_pase)

        layout_botones.add_widget(btn_mazos)
        layout_botones.add_widget(btn_gacha)
        layout_botones.add_widget(btn_opciones)
        layout_botones.add_widget(btn_salir)

        layout_global.add_widget(layout_botones)

        # Footer con versión
        lbl_footer = Label(text="xXmegaplayer64Xx - 2026", font_size='12sp', size_hint_y=0.08)
        layout_global.add_widget(lbl_footer)

        self.add_widget(layout_global)

    def cambiar_pantalla(self, nombre_pantalla):
        self.manager.current = nombre_pantalla

    def on_enter(self):
        AudioManager().play_bgm('titanicmonarch.ogg')
        self.actualizar_estado_auth()

    def actualizar_estado_auth(self):
        """Actualiza el indicador visual superior según si hay sesión en la nube o no."""
        if CloudSyncManager.is_logged_in():
            usuario = CloudSyncManager.get_current_user()
            self.lbl_auth_status.text = f"[color=00ff88]🟢 Conectado:[/color] [b]{usuario}[/b]"
            self.btn_auth_action.text = "☁️ Sincronizar"
            self.btn_auth_action.background_color = (0.2, 0.65, 0.4, 1)
            self.btn_account_manage.opacity = 1.0
            self.btn_account_manage.disabled = False
        else:
            self.lbl_auth_status.text = "[color=aaaaaa]⚪ Modo Local[/color]"
            self.btn_auth_action.text = "🔑 Iniciar Sesión"
            self.btn_auth_action.background_color = (0.2, 0.5, 0.8, 1)
            self.btn_account_manage.opacity = 0.0
            self.btn_account_manage.disabled = True

    def accion_auth_boton(self, _instance):
        if not CloudSyncManager.is_logged_in():
            self.cambiar_pantalla('login_screen')
        else:
            self.sincronizar_perfil_nube()

    def sincronizar_perfil_nube(self):
        """Dispara la sincronización en hilo secundario para evitar congelamiento de la UI."""
        self.btn_auth_action.disabled = True
        self.btn_auth_action.text = "☁️ Sincronizando..."
        self.lbl_auth_status.text = "[color=ffdd44]Sincronizando con la nube...[/color]"

        def _tarea_sync():
            res = CloudSyncManager.sync_profile()
            Clock.schedule_once(lambda dt: self._finalizar_sincronizacion(res), 0)

        threading.Thread(target=_tarea_sync, daemon=True).start()

    def _finalizar_sincronizacion(self, res: dict):
        self.btn_auth_action.disabled = False
        usuario = CloudSyncManager.get_current_user()
        
        if res.get("success"):
            self.lbl_auth_status.text = f"[color=00ff88]🟢 Conectado:[/color] [b]{usuario}[/b]"
            self.btn_auth_action.text = "✓ Sincronizado"
            AudioManager().play_sfx("draw")
            Clock.schedule_once(lambda dt: setattr(self.btn_auth_action, 'text', "☁️ Sincronizar"), 2.0)
        else:
            msg = res.get("message", "Error de sincronización")
            self.lbl_auth_status.text = f"[color=ffbb33]⚠️ {msg}[/color]"
            self.btn_auth_action.text = "☁️ Sincronizar"
            AudioManager().play_sfx("error1")
            Clock.schedule_once(lambda dt: self.actualizar_estado_auth(), 3.0)