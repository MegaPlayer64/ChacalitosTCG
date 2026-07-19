from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.button import Button
# pyrefly: ignore [missing-import]
from kivy.properties import StringProperty
from src.domain.audio_manager import AudioManager
import os
import psutil

class PantallaOpciones(Screen):
    # Propiedades dinámicas
    username_text = StringProperty("Cargando jugador...")
    user_level = StringProperty("Nivel: --")
    ram_text = StringProperty("RAM del Juego: Calculando...")
    
    def __init__(self, **kwargs):
        super(PantallaOpciones, self).__init__(**kwargs)
        
        # ----------------------------------------
        # CONTENEDOR PRINCIPAL
        # ----------------------------------------
        main_layout = BoxLayout(orientation='vertical', padding=40, spacing=20)

        # Título principal
        title_label = Label(text="OPCIONES GENERALES", font_size='28sp', size_hint_y=None, height=50)
        main_layout.add_widget(title_label)

        # ----------------------------------------
        # SECCIÓN DE AUDIO
        # ----------------------------------------
        audio_layout = BoxLayout(orientation='vertical', spacing=10)
        
        # Slider Música
        self.music_label = Label(text="Música de Fondo: 50%", halign='left', valign='middle')
        self.music_label.bind(size=self.music_label.setter('text_size')) # Necesario en Kivy para alinear texto
        
        self.music_slider = Slider(min=0.0, max=1.0, step=0.05, value=0.5)
        self.music_slider.bind(value=self.on_slider_value_change)
        
        # Slider SFX
        self.sfx_label = Label(text="Efectos de Sonido (SFX): 80%", halign='left', valign='middle')
        self.sfx_label.bind(size=self.sfx_label.setter('text_size'))
        
        self.sfx_slider = Slider(min=0.0, max=1.0, step=0.05, value=0.8)
        self.sfx_slider.bind(value=self.on_slider_value_change)

        # Agregamos los widgets de audio a su layout
        audio_layout.add_widget(self.music_label)
        audio_layout.add_widget(self.music_slider)
        audio_layout.add_widget(self.sfx_label)
        audio_layout.add_widget(self.sfx_slider)
        
        main_layout.add_widget(audio_layout)

        # ----------------------------------------
        # SECCIÓN DE CUENTA DE JUGADOR
        # ----------------------------------------
        account_layout = BoxLayout(orientation='vertical', padding=[0, 20, 0, 20], spacing=10)
        
        acc_title = Label(text="CUENTA DEL JUGADOR", font_size='20sp', halign='left', valign='middle')
        acc_title.bind(size=acc_title.setter('text_size'))
        
        # Etiqueta del Nombre (Color Verde)
        self.user_label = Label(text=self.username_text, font_size='18sp', color=[0.2, 0.8, 0.2, 1], halign='left', valign='middle')
        self.user_label.bind(size=self.user_label.setter('text_size'))
        
        # Etiqueta del Nivel
        self.level_label = Label(text=self.user_level, halign='left', valign='middle')
        self.level_label.bind(size=self.level_label.setter('text_size'))
        
        # Etiqueta de la RAM
        self.ram_label = Label(text=self.ram_text, halign='left', valign='middle')
        self.ram_label.bind(size=self.ram_label.setter('text_size'))
        
        # Botón de Cerrar Sesión
        logout_btn = Button(text="Cerrar Sesión / Cambiar Cuenta", size_hint_y=None, height=45)
        logout_btn.bind(on_release=self.cerrar_sesion)

        # Agregamos los widgets de cuenta a su layout
        account_layout.add_widget(acc_title)
        account_layout.add_widget(self.user_label)
        account_layout.add_widget(self.level_label)
        account_layout.add_widget(self.ram_label)
        account_layout.add_widget(logout_btn)
        
        main_layout.add_widget(account_layout)

        # ----------------------------------------
        # BOTÓN DE RETORNO
        # ----------------------------------------
        back_btn = Button(text="Volver al Menú Principal", size_hint_y=None, height=50)
        back_btn.bind(on_release=self.volver_menu)
        main_layout.add_widget(back_btn)

        # Finalmente, añadimos el contenedor principal a la Pantalla
        self.add_widget(main_layout)

        # Vincular las StringProperties a las etiquetas para que se actualicen solas
        self.bind(username_text=self.user_label.setter('text'))
        self.bind(user_level=self.level_label.setter('text'))
        self.bind(ram_text=self.ram_label.setter('text'))

    # ==========================================
    # LÓGICA DE LA PANTALLA
    # ==========================================
    def on_enter(self, *args):
        """Se ejecuta automáticamente cuando el jugador entra a esta pantalla."""
        # 1. Sincronizar Sliders con el AudioManager
        audio = AudioManager()
        self.music_slider.value = audio.music_volume
        self.sfx_slider.value = audio.sfx_volume
        
        # 2. Cargar datos de la cuenta desde tu backend
        self.username_text = "Not Done Yet Sorry :P"
        self.user_level = "Nivel: -1"
        self.actualizar_ram_consumida()
        
        # Forzamos la actualización visual de los textos de los sliders
        self.on_slider_value_change(None, None)

    def on_slider_value_change(self, instance, value):
        """Actualiza el texto y manda los valores al AudioManager."""
        v_musica = self.music_slider.value
        v_sfx = self.sfx_slider.value
        
        # Actualizamos las etiquetas visuales
        self.music_label.text = f"Música de Fondo: {int(v_musica * 100)}%"
        self.sfx_label.text = f"Efectos de Sonido (SFX): {int(v_sfx * 100)}%"
        
        # Aplicamos al manejador de audio
        AudioManager().set_volumes(v_musica, v_sfx)
    
    def actualizar_ram_consumida(self):
        """Calcula la memoria física real consumida en Megabytes"""
        try:
            proceso = psutil.Process(os.getpid())
            ram_bytes = proceso.memory_info().rss
            ram_megabytes = ram_bytes / (1024 * 1024)
            # 3. Al modificar esta variable, la pantalla de Kivy se actualizará sola de inmediato
            self.ram_text = f"RAM del Juego: {ram_megabytes:.2f} MB"
        except Exception as e:
            self.ram_text = "RAM del Juego: No disponible"

    def cerrar_sesion(self, instance):
        """Lógica para desconectar la cuenta."""
        print("Cerrando sesión...")
        # self.manager.current = 'login_screen'

    def volver_menu(self, instance):
        """Regresa a la pantalla principal."""
        if self.manager:
            self.manager.current = 'menu_screen'
