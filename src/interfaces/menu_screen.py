import os
import threading
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from server.cloud_sync import CloudSyncManager
from src.domain.audio_manager import AudioManager
from src.domain.grid_background import FondoCuadriculado
from src.infrastructure.path_manager import PathManager


def resolver_logo_seguro() -> str | None:
    """Busca el archivo BetaLogo.png en las rutas conocidas de assets."""
    candidatos = [
        PathManager.get_asset_path('images/BetaLogo.png'),
        PathManager.get_asset_path('src/images/BetaLogo.png'),
        PathManager.get_asset_path('art/BetaLogo.png'),
    ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            return ruta
    return None


class MenuPrincipal(Screen):
    def __init__(self, **kwargs):
        print("   [MenuPrincipal] -> Inicio __init__")
        super().__init__(**kwargs)
        self.menu_jugar_abierto = False

        # Layout principal de toda la pantalla (Vertical)
        layout_global = BoxLayout(orientation='vertical', padding=[24, 14, 24, 12], spacing=12)

        # Fondo cuadriculado interactivo
        fondo_grilla = FondoCuadriculado()
        self.add_widget(fondo_grilla, index=0)

        # =====================================================================
        # 1. BARRA SUPERIOR: ICONOS DE PROGRESO (IZQ) + CUENTA CLOUD (DER)
        # =====================================================================
        barra_superior = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=46,
            spacing=10,
        )

        # -- Grupo Izquierdo: Accesos rápidos compactos por icono --
        layout_iconos_rapidos = BoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            width=214,
            spacing=8,
        )

        btn_misiones = Button(
            text="📋\n[size=10sp]Misiones[/size]",
            markup=True,
            font_size='15sp',
            halign='center',
            valign='middle',
            background_color=(0.18, 0.52, 0.74, 1),
        )
        btn_pase = Button(
            text="🏆\n[size=10sp]Pase[/size]",
            markup=True,
            font_size='15sp',
            halign='center',
            valign='middle',
            background_color=(0.82, 0.52, 0.12, 1),
        )
        self.btn_calendario = Button(
            text="📅\n[size=10sp]Calendario[/size]",
            markup=True,
            font_size='15sp',
            halign='center',
            valign='middle',
            background_color=(0.22, 0.55, 0.35, 1),
        )

        btn_misiones.bind(on_release=lambda x: self.cambiar_pantalla('missions_screen'))
        btn_pase.bind(on_release=lambda x: self.cambiar_pantalla('battle_pass'))
        self.btn_calendario.bind(on_release=lambda x: self.cambiar_pantalla('calendar_screen'))

        layout_iconos_rapidos.add_widget(btn_misiones)
        layout_iconos_rapidos.add_widget(btn_pase)
        layout_iconos_rapidos.add_widget(self.btn_calendario)
        barra_superior.add_widget(layout_iconos_rapidos)

        # -- Grupo Derecho: Estado Cloud / Sesión --
        self.layout_auth = BoxLayout(
            orientation='horizontal',
            spacing=8,
            padding=[0, 4, 0, 4],
        )

        self.lbl_auth_status = Label(
            text="⚪ Modo Local",
            markup=True,
            font_size='13sp',
            halign='right',
            valign='middle',
        )
        self.lbl_auth_status.bind(size=self.lbl_auth_status.setter('text_size'))

        self.btn_auth_action = Button(
            text="🔑 Iniciar Sesión",
            font_size='12sp',
            size_hint=(None, None),
            size=(135, 36),
            background_color=(0.2, 0.5, 0.8, 1),
        )
        self.btn_auth_action.bind(on_release=self.accion_auth_boton)

        self.btn_account_manage = Button(
            text="⚙️",
            font_size='14sp',
            size_hint=(None, None),
            size=(36, 36),
            background_color=(0.3, 0.35, 0.4, 1),
        )
        self.btn_account_manage.bind(on_release=lambda x: self.cambiar_pantalla('login_screen'))

        self.layout_auth.add_widget(self.lbl_auth_status)
        self.layout_auth.add_widget(self.btn_auth_action)
        self.layout_auth.add_widget(self.btn_account_manage)
        barra_superior.add_widget(self.layout_auth)

        layout_global.add_widget(barra_superior)

        # =====================================================================
        # 2. LOGO CON CARGA DEFENSIVA
        # =====================================================================
        ruta_logo = resolver_logo_seguro()
        if ruta_logo:
            imagen_logo = Image(
                source=ruta_logo,
                size_hint_y=0.31,
                allow_stretch=True,
                keep_ratio=True,
            )
            layout_global.add_widget(imagen_logo)
        else:
            print("   [MenuPrincipal] Advertencia: 'images/BetaLogo.png' no encontrado. Usando título de texto.")
            lbl_titulo_fallback = Label(
                text="[b]CHACALITOS TCG[/b]",
                markup=True,
                font_size='32sp',
                size_hint_y=0.25,
                color=(0.9, 0.8, 0.2, 1),
            )
            layout_global.add_widget(lbl_titulo_fallback)

        # =====================================================================
        # 3. ZONA CENTRAL: MENÚ PRINCIPAL + SUBMENÚ LATERAL DE MODOS DE JUEGO
        # =====================================================================
        zona_central = BoxLayout(
            orientation='horizontal',
            spacing=18,
            size_hint_y=0.61,
        )

        # Espaciador izquierdo dinámico (centra el menú cuando el submenú está cerrado)
        self.espaciador_izq = BoxLayout(size_hint_x=0.26)
        zona_central.add_widget(self.espaciador_izq)

        # -- Columna Principal de Navegación (5 botones limpios) --
        self.panel_principal = BoxLayout(
            orientation='vertical',
            spacing=11,
            size_hint_x=0.48,
        )

        self.btn_jugar_principal = Button(
            text="⚔️  JUGAR   ▸",
            font_size='18sp',
            bold=True,
            size_hint_y=None,
            height=52,
            background_color=(0.20, 0.58, 0.88, 1),
        )
        btn_mazos = Button(
            text="🃏  COLECCIÓN Y MAZOS",
            font_size='15sp',
            size_hint_y=None,
            height=46,
        )
        btn_gacha = Button(
            text="🛒  TIENDA / BANNERS",
            font_size='15sp',
            size_hint_y=None,
            height=46,
        )
        btn_opciones = Button(
            text="⚙️  OPCIONES",
            font_size='15sp',
            size_hint_y=None,
            height=46,
        )
        btn_salir = Button(
            text="🚪  SALIR",
            font_size='15sp',
            size_hint_y=None,
            height=44,
            background_color=(0.55, 0.22, 0.22, 1),
        )

        self.btn_jugar_principal.bind(on_release=self.toggle_panel_jugar)
        btn_mazos.bind(on_release=lambda x: self.cambiar_pantalla('inventory_screen'))
        btn_gacha.bind(on_release=lambda x: self.cambiar_pantalla('banner_screen'))
        btn_opciones.bind(on_release=lambda x: self.cambiar_pantalla('options_screen'))
        btn_salir.bind(on_release=self.cerrar_aplicacion)

        self.panel_principal.add_widget(self.btn_jugar_principal)
        self.panel_principal.add_widget(btn_mazos)
        self.panel_principal.add_widget(btn_gacha)
        self.panel_principal.add_widget(btn_opciones)
        self.panel_principal.add_widget(btn_salir)
        self.panel_principal.add_widget(BoxLayout())  # Empuja los botones hacia arriba ordenadamente
        zona_central.add_widget(self.panel_principal)

        # -- Panel Lateral Desplegable: Selección de Modo de Juego --
        self.panel_modos = BoxLayout(
            orientation='vertical',
            spacing=10,
            padding=[14, 12, 14, 12],
            size_hint_x=0.001,
            opacity=0.0,
            disabled=True,
        )
        with self.panel_modos.canvas.before:
            Color(0.10, 0.13, 0.20, 0.92)
            self._bg_modos = RoundedRectangle(pos=self.panel_modos.pos, size=self.panel_modos.size, radius=[12])
        self.panel_modos.bind(
            pos=lambda inst, val: setattr(self._bg_modos, 'pos', val),
            size=lambda inst, val: setattr(self._bg_modos, 'size', val),
        )

        # Cabecera del submenú lateral
        cabecera_modos = BoxLayout(orientation='horizontal', size_hint_y=None, height=32)
        lbl_modos = Label(
            text="[b]ELIGE MODO DE JUEGO[/b]",
            markup=True,
            font_size='14sp',
            color=(0.55, 0.82, 1.0, 1),
            halign='left',
            valign='middle',
        )
        lbl_modos.bind(size=lbl_modos.setter('text_size'))

        btn_cerrar_modos = Button(
            text="✕",
            font_size='14sp',
            size_hint=(None, None),
            size=(32, 30),
            background_color=(0.45, 0.25, 0.25, 1),
        )
        btn_cerrar_modos.bind(on_release=lambda x: self.cerrar_panel_jugar())

        cabecera_modos.add_widget(lbl_modos)
        cabecera_modos.add_widget(btn_cerrar_modos)
        self.panel_modos.add_widget(cabecera_modos)

        # Tarjetas de los 3 modos de juego
        modos = [
            (
                "🎮  PARTIDA LOCAL\n[size=11sp][color=CFD8DC]Duelo rápido vs IA o 2 jugadores locales[/color][/size]",
                (0.18, 0.48, 0.72, 1),
                'selection_screen',
            ),
            (
                "🌐  MULTIJUGADOR ONLINE\n[size=11sp][color=CFD8DC]Salas en red contra otros jugadores[/color][/size]",
                (0.18, 0.58, 0.46, 1),
                'online_lobby_screen',
            ),
            (
                "🗼  TORRE ARCADE\n[size=11sp][color=CFD8DC]Desafío escalonado piso por piso[/color][/size]",
                (0.54, 0.30, 0.68, 1),
                'arcade_screen',
            ),
        ]

        for texto_modo, color_btn, pantalla_destino in modos:
            btn_modo = Button(
                text=texto_modo,
                markup=True,
                font_size='14sp',
                bold=True,
                size_hint_y=None,
                height=58,
                halign='left',
                valign='middle',
                padding=[14, 0],
                background_color=color_btn,
            )
            btn_modo.bind(size=btn_modo.setter('text_size'))
            btn_modo.bind(on_release=lambda inst, p=pantalla_destino: self.cambiar_pantalla(p))
            self.panel_modos.add_widget(btn_modo)

        self.panel_modos.add_widget(BoxLayout())  # Espaciador inferior interno
        zona_central.add_widget(self.panel_modos)

        # Espaciador derecho dinámico
        self.espaciador_der = BoxLayout(size_hint_x=0.26)
        zona_central.add_widget(self.espaciador_der)

        layout_global.add_widget(zona_central)

        # =====================================================================
        # 4. FOOTER CON VERSIÓN
        # =====================================================================
        lbl_footer = Label(text="xXmegaplayer64Xx - 2026", font_size='12sp', size_hint_y=None, height=22)
        layout_global.add_widget(lbl_footer)

        self.add_widget(layout_global)
        print("   [MenuPrincipal] -> Fin __init__ OK")

    # -------------------------------------------------------------------------
    # CONTROL DEL SUBMENÚ LATERAL DE MODOS DE JUEGO
    # -------------------------------------------------------------------------
    def toggle_panel_jugar(self, _instance=None):
        if self.menu_jugar_abierto:
            self.cerrar_panel_jugar()
        else:
            self.abrir_panel_jugar()

    def abrir_panel_jugar(self):
        self.menu_jugar_abierto = True
        self.btn_jugar_principal.text = "⚔️  JUGAR   ◂"
        self.btn_jugar_principal.background_color = (0.26, 0.68, 0.96, 1)
        self.panel_modos.disabled = False

        Animation.cancel_all(self.espaciador_izq, 'size_hint_x')
        Animation.cancel_all(self.espaciador_der, 'size_hint_x')
        Animation.cancel_all(self.panel_principal, 'size_hint_x')
        Animation.cancel_all(self.panel_modos, 'size_hint_x', 'opacity')

        Animation(size_hint_x=0.05, duration=0.20, t='out_quad').start(self.espaciador_izq)
        Animation(size_hint_x=0.42, duration=0.20, t='out_quad').start(self.panel_principal)
        Animation(size_hint_x=0.48, opacity=1.0, duration=0.22, t='out_quad').start(self.panel_modos)
        Animation(size_hint_x=0.05, duration=0.20, t='out_quad').start(self.espaciador_der)

    def cerrar_panel_jugar(self, instantaneo=False):
        self.menu_jugar_abierto = False
        self.btn_jugar_principal.text = "⚔️  JUGAR   ▸"
        self.btn_jugar_principal.background_color = (0.20, 0.58, 0.88, 1)
        self.panel_modos.disabled = True

        Animation.cancel_all(self.espaciador_izq, 'size_hint_x')
        Animation.cancel_all(self.espaciador_der, 'size_hint_x')
        Animation.cancel_all(self.panel_principal, 'size_hint_x')
        Animation.cancel_all(self.panel_modos, 'size_hint_x', 'opacity')

        if instantaneo:
            self.espaciador_izq.size_hint_x = 0.26
            self.panel_principal.size_hint_x = 0.48
            self.panel_modos.size_hint_x = 0.001
            self.panel_modos.opacity = 0.0
            self.espaciador_der.size_hint_x = 0.26
        else:
            Animation(size_hint_x=0.26, duration=0.18, t='out_quad').start(self.espaciador_izq)
            Animation(size_hint_x=0.48, duration=0.18, t='out_quad').start(self.panel_principal)
            Animation(size_hint_x=0.001, opacity=0.0, duration=0.16, t='out_quad').start(self.panel_modos)
            Animation(size_hint_x=0.26, duration=0.18, t='out_quad').start(self.espaciador_der)

    # -------------------------------------------------------------------------
    # NAVEGACIÓN Y CICLO DE VIDA
    # -------------------------------------------------------------------------
    def cerrar_aplicacion(self, _instance):
        from kivy.app import App
        App.get_running_app().stop()

    def cambiar_pantalla(self, nombre_pantalla):
        self.manager.current = nombre_pantalla

    def on_enter(self):
        print("   [MenuPrincipal] -> Entrando a pantalla (on_enter)")
        self.cerrar_panel_jugar(instantaneo=True)
        Clock.schedule_once(lambda dt: self._iniciar_bgm_seguro(), 0.1)
        self.actualizar_estado_auth()
        self.actualizar_boton_calendario()

    def actualizar_boton_calendario(self):
        """Actualiza el icono y color del botón del calendario si hay recompensa diaria pendiente."""
        try:
            from src.domain.weekly_calendar_manager import WeeklyCalendarManager
            wcm = WeeklyCalendarManager()
            if wcm.can_claim_today():
                st = wcm.get_status()
                day = st.get("current_day", 1)
                self.btn_calendario.text = f"🎁\n[size=10sp][b]¡Día {day}![/b][/size]"
                self.btn_calendario.background_color = (0.15, 0.80, 0.35, 1)
            else:
                self.btn_calendario.text = "📅\n[size=10sp]Calendario[/size]"
                self.btn_calendario.background_color = (0.22, 0.55, 0.35, 1)
        except Exception as e:
            print(f">> [MenuPrincipal] Advertencia al actualizar botón de calendario: {e}")

    def _iniciar_bgm_seguro(self):
        try:
            AudioManager().play_bgm('titanicmonarch.ogg')
        except Exception as e:
            print(f"   [Audio Warning] No se pudo reproducir BGM: {e}")

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
        """Dispara la sincronización en un hilo secundario para no congelar la UI."""
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