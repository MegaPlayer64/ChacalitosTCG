# Ubicación asumida: src/interfaces/audio_manager.py o similar
import os
from kivy.core.audio import SoundLoader
from kivy.logger import Logger

class AudioManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AudioManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        self.sounds = {}
        self.current_bgm = None
        self.music_volume = 0.5
        self.sfx_volume = 0.8
        
        # 1. Encontrar la carpeta 'src' de forma dinámica
        # os.path.dirname(__file__) nos da la carpeta actual (ej: interfaces/)
        # '..' sube un nivel directamente a 'src/'
        self.src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # 2. Definir las rutas específicas para música y efectos
        self.music_dir = os.path.join(self.src_dir, 'audio', 'music')
        self.sound_dir = os.path.join(self.src_dir, 'audio', 'sound')
        
        # 3. Precargar efectos de sonido comunes usando la carpeta de 'sound'
        self.preload_sound('click', 'click.wav') # Cambia por el nombre real si tienes uno genérico
        self.preload_sound('draw', '240776__f4ngy__card-flip.wav')
        self.preload_sound('damage', '573376__johnloser__cyber-punch-01.wav')

    def preload_sound(self, name, filename):
        # Buscamos los SFX específicamente en la subcarpeta 'sound'
        path = os.path.join(self.sound_dir, filename)
        if os.path.exists(path):
            sound = SoundLoader.load(path)
            if sound:
                self.sounds[name] = sound
                Logger.info(f"Audio: SFX cargado -> {name} desde {path}")
            else:
                Logger.warning(f"Audio: Error al parsear el archivo {path}")
        else:
            Logger.warning(f"Audio: Archivo SFX no encontrado en {path}")

    def play_sfx(self, name):
        """Reproduce un efecto de sonido corto."""
        if name in self.sounds:
            self.sounds[name].volume = self.sfx_volume
            self.sounds[name].play()
        else:
            # Intento de carga dinámica si no se precargó
            Logger.debug(f"Audio: SFX '{name}' no precargado.")

    def play_bgm(self, filename):
        """Reproduce música de fondo desde la carpeta src/audio/music/"""
        if self.current_bgm:
            self.current_bgm.stop()

        # Construye la ruta hacia src/audio/music/tu_archivo.ogg
        path = os.path.join(self.music_dir, filename)
        
        if os.path.exists(path):
            self.current_bgm = SoundLoader.load(path)
            if self.current_bgm:
                self.current_bgm.loop = True
                self.current_bgm.volume = self.music_volume
                self.current_bgm.play()
                Logger.info(f"Audio: Reproduciendo BGM -> {filename}")
            else:
                Logger.error(f"Audio: No se pudo cargar el archivo de música {path}")
        else:
            Logger.error(f"Audio: Archivo de música no encontrado en {path}")


    def stop_bgm(self):
        if self.current_bgm:
            self.current_bgm.stop()

    def set_volumes(self, music_vol, sfx_vol):
        self.music_volume = music_vol
        self.sfx_volume = sfx_vol
        if self.current_bgm:
            self.current_bgm.volume = self.music_volume