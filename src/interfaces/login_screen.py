import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle

from src.domain.grid_background import FondoCuadriculado
from src.domain.audio_manager import AudioManager
from server.cloud_sync import CloudSyncManager


class LoginScreen(Screen):
    """
    Pantalla de Autenticación y Sincronización en la Nube para Chacalitos TCG.
    Permite iniciar sesión, registrarse o continuar en Modo Offline / Invitado.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 1. Fondo Cuadriculado
        self.fondo_grilla = FondoCuadriculado(size=self.size)
        self.add_widget(self.fondo_grilla, index=0)

        # 2. Contenedor Principal Centrado
        layout_global = BoxLayout(orientation='vertical', padding=[30, 20, 30, 20], spacing=15)

        # Encabezado
        lbl_titulo = Label(
            text="[b][size=26sp]CHACALITOS TCG[/size][/b]\n[size=14sp][color=88bbff]Autenticación y Sincronización en la Nube[/color][/size]",
            markup=True,
            halign='center',
            size_hint_y=0.18
        )
        layout_global.add_widget(lbl_titulo)

        # 3. Tarjeta Central con Canvas Dark Mode
        self.panel_tarjeta = BoxLayout(
            orientation='vertical',
            padding=[25, 20, 25, 20],
            spacing=12,
            size_hint=(0.65, 0.68),
            pos_hint={'center_x': 0.5}
        )

        with self.panel_tarjeta.canvas.before:
            Color(0.12, 0.14, 0.18, 0.95)
            self.rect_tarjeta = RoundedRectangle(
                pos=self.panel_tarjeta.pos,
                size=self.panel_tarjeta.size,
                radius=[12, 12, 12, 12]
            )

        self.panel_tarjeta.bind(
            pos=lambda inst, v: setattr(self.rect_tarjeta, 'pos', inst.pos),
            size=lambda inst, v: setattr(self.rect_tarjeta, 'size', inst.size)
        )

        # Campo: Usuario
        lbl_user = Label(text="[b]Usuario:[/b]", markup=True, size_hint_y=None, height=24, halign='left')
        lbl_user.bind(size=lbl_user.setter('text_size'))
        self.panel_tarjeta.add_widget(lbl_user)

        self.txt_username = TextInput(
            multiline=False,
            font_size='16sp',
            size_hint_y=None,
            height=42,
            background_color=(0.18, 0.22, 0.28, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.3, 0.7, 1, 1),
            hint_text="Tu nombre de jugador"
        )
        self.panel_tarjeta.add_widget(self.txt_username)

        # Campo: Contraseña
        lbl_pass = Label(text="[b]Contraseña:[/b]", markup=True, size_hint_y=None, height=24, halign='left')
        lbl_pass.bind(size=lbl_pass.setter('text_size'))
        self.panel_tarjeta.add_widget(lbl_pass)

        self.txt_password = TextInput(
            password=True,
            multiline=False,
            font_size='16sp',
            size_hint_y=None,
            height=42,
            background_color=(0.18, 0.22, 0.28, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.3, 0.7, 1, 1),
            hint_text="Mínimo 4 caracteres"
        )
        self.txt_password.bind(on_text_validate=self.accion_iniciar_sesion)
        self.panel_tarjeta.add_widget(self.txt_password)

        # Label de Estado / Feedback al usuario
        self.lbl_estado = Label(
            text="[color=aaaaaa]Ingresa tus datos o juega en modo offline.[/color]",
            markup=True,
            font_size='13sp',
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=36
        )
        self.lbl_estado.bind(size=self.lbl_estado.setter('text_size'))
        self.panel_tarjeta.add_widget(self.lbl_estado)

        # Botones de Acción (Login / Registro)
        box_acciones = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=46)
        
        self.btn_login = Button(
            text="INICIAR SESIÓN",
            font_size='15sp',
            background_color=(0.2, 0.6, 0.9, 1),
            bold=True
        )
        self.btn_login.bind(on_release=self.accion_iniciar_sesion)
        box_acciones.add_widget(self.btn_login)

        self.btn_register = Button(
            text="REGISTRARSE",
            font_size='15sp',
            background_color=(0.25, 0.75, 0.45, 1),
            bold=True
        )
        self.btn_register.bind(on_release=self.accion_registrarse)
        box_acciones.add_widget(self.btn_register)

        self.panel_tarjeta.add_widget(box_acciones)

        # Botón de Cerrar Sesión (Visible sólo si ya está logueado)
        self.btn_logout = Button(
            text="CERRAR SESIÓN ACTUAL",
            font_size='13sp',
            size_hint_y=None,
            height=36,
            background_color=(0.7, 0.25, 0.25, 1)
        )
        self.btn_logout.bind(on_release=self.accion_cerrar_sesion)
        self.panel_tarjeta.add_widget(self.btn_logout)

        layout_global.add_widget(self.panel_tarjeta)

        # 4. Botón Inferior: Modo Invitado / Offline
        self.btn_offline = Button(
            text="JUGAR MODO INVITADO / OFFLINE",
            font_size='16sp',
            size_hint=(0.65, None),
            height=46,
            pos_hint={'center_x': 0.5},
            background_color=(0.4, 0.45, 0.5, 1)
        )
        self.btn_offline.bind(on_release=self.accion_modo_offline)
        layout_global.add_widget(self.btn_offline)

        self.add_widget(layout_global)

    def on_enter(self):
        """Al ingresar a la pantalla, actualizamos el estado de la sesión."""
        AudioManager().play_bgm('titanicmonarch.ogg')
        esta_conectado = CloudSyncManager.is_logged_in()
        
        if esta_conectado:
            usuario = CloudSyncManager.get_current_user()
            self.lbl_estado.text = f"[color=00ff88]Sesión activa como: [b]{usuario}[/b][/color]"
            self.btn_logout.opacity = 1.0
            self.btn_logout.disabled = False
            self.btn_login.text = "CAMBIAR CUENTA"
        else:
            self.lbl_estado.text = "[color=aaaaaa]Ingresa tus datos o juega en modo offline.[/color]"
            self.btn_logout.opacity = 0.0
            self.btn_logout.disabled = True
            self.btn_login.text = "INICIAR SESIÓN"

    def _bloquear_controles(self, bloquear=True):
        """Desactiva o activa los botones durante las llamadas de red."""
        self.btn_login.disabled = bloquear
        self.btn_register.disabled = bloquear
        self.btn_offline.disabled = bloquear
        self.txt_username.disabled = bloquear
        self.txt_password.disabled = bloquear

    def accion_iniciar_sesion(self, _instance):
        user = self.txt_username.text.strip()
        pwd = self.txt_password.text.strip()

        if not user or not pwd:
            self.lbl_estado.text = "[color=ff4444]Por favor ingresa usuario y contraseña.[/color]"
            return

        self._bloquear_controles(True)
        self.lbl_estado.text = "[color=ffdd44]Conectando con el servidor...[/color]"

        def _tarea_red():
            resultado = CloudSyncManager.login(user, pwd)
            Clock.schedule_once(lambda dt: self._procesar_resultado(resultado, "login"), 0)

        threading.Thread(target=_tarea_red, daemon=True).start()

    def accion_registrarse(self, _instance):
        user = self.txt_username.text.strip()
        pwd = self.txt_password.text.strip()

        if len(user) < 3 or len(pwd) < 4:
            self.lbl_estado.text = "[color=ff4444]Usuario (min 3) o contraseña (min 4) muy cortos.[/color]"
            return

        self._bloquear_controles(True)
        self.lbl_estado.text = "[color=ffdd44]Registrando cuenta en la nube...[/color]"

        def _tarea_red():
            resultado = CloudSyncManager.register(user, pwd)
            Clock.schedule_once(lambda dt: self._procesar_resultado(resultado, "registro"), 0)

        threading.Thread(target=_tarea_red, daemon=True).start()

    def _procesar_resultado(self, resultado: dict, tipo: str):
        self._bloquear_controles(False)

        if resultado.get("success"):
            usuario = resultado.get("username", self.txt_username.text.strip())
            accion_txt = "¡Bienvenido de nuevo," if tipo == "login" else "¡Cuenta registrada con éxito,"
            self.lbl_estado.text = f"[color=00ff88]{accion_txt} [b]{usuario}[/b]![/color]"
            AudioManager().play_sfx("draw")
            
            # Limpiar campos y redirigir al menú principal
            self.txt_password.text = ""
            Clock.schedule_once(lambda dt: self.cambiar_pantalla('menu_screen'), 1.0)
        else:
            error_msg = resultado.get("error", "Error desconocido")
            self.lbl_estado.text = f"[color=ff4444]Error: {error_msg}[/color]"
            AudioManager().play_sfx("error1")

    def accion_cerrar_sesion(self, _instance):
        CloudSyncManager.logout()
        self.lbl_estado.text = "[color=ffbb33]Has cerrado sesión. Modo Local activado.[/color]"
        self.btn_logout.opacity = 0.0
        self.btn_logout.disabled = True
        self.btn_login.text = "INICIAR SESIÓN"
        AudioManager().play_sfx("card_place")

    def accion_modo_offline(self, _instance):
        self.cambiar_pantalla('menu_screen')

    def cambiar_pantalla(self, nombre_pantalla):
        self.manager.current = nombre_pantalla
