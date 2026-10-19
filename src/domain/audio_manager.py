import os
from kivy.core.audio import SoundLoader
from kivy.logger import Logger
from src.infrastructure.path_manager import PathManager


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
        self.current_bgm_name = None
        self.music_volume = 0.5
        self.sfx_volume = 0.8
        
        # Mapeo de identificadores a nombres de archivos
        self.sfx_map = {
            'move': 'walk1.wav',
            'draw': 'card1.wav',
            'damage': 'punch1.wav',
            'dead': 'deadunit.wav',
            'deploy': 'summonunit.wav',
            'select1': 'select1.wav',
            'select2': 'select2.wav',
            'heal': 'heal.wav',
            'error1': 'error1.wav',
            'error2': 'error2.wav',
            'error3': 'error3.wav',
            'gundam1': 'gundamappear.wav',
            'quemadasdodge': 'quemadasdodge.wav',
            'yukatamiku': 'yukatamiku.ogg',
        }

    def _resolve_audio_path(self, category: str, filename: str) -> str:
        """Resuelve rutas relativas de audio mediante PathManager (compatible con PC/Android/Frozen)."""
        # Prueba 1: assets/audio/{category}/{filename}
        rel_path = os.path.join('audio', category, filename)
        full_path = PathManager.get_asset_path(rel_path)
        
        # Fallback: src/audio/{category}/{filename}
        if not os.path.exists(full_path):
            fallback_path = PathManager.get_asset_path(os.path.join('src', 'audio', category, filename))
            if os.path.exists(fallback_path):
                return fallback_path

        return full_path

    def get_sound(self, name: str):
        """Carga perezosa (Lazy Loading): Solo lee el disco la primera vez que se reproduce el efecto."""
        if name in self.sounds:
            return self.sounds[name]

        if name in self.sfx_map:
            filename = self.sfx_map[name]
            path = self._resolve_audio_path('sound', filename)

            if os.path.exists(path):
                try:
                    sound = SoundLoader.load(path)
                    if sound:
                        self.sounds[name] = sound
                        Logger.info(f"Audio: SFX cargado bajo demanda -> {name}")
                        return sound
                    else:
                        Logger.warning(f"Audio: Kivy no pudo parsear el archivo {path}")
                except Exception as e:
                    Logger.error(f"Audio: Excepción al cargar SFX {path}: {e}")
            else:
                Logger.warning(f"Audio: Archivo SFX no encontrado en {path}")

        return None

    def play_sfx(self, name: str):
        """Reproduce un efecto de sonido corto."""
        sound = self.get_sound(name)
        if sound:
            sound.volume = self.sfx_volume
            sound.play()

    def play_bgm(self, filename: str):
        """Reproduce música de fondo desde la carpeta de música usando PathManager."""
        if self.current_bgm and self.current_bgm_name == filename:
            if self.current_bgm.state != 'play':
                self.current_bgm.play()
            return

        if self.current_bgm:
            self.current_bgm.stop()

        path = self._resolve_audio_path('music', filename)

        if os.path.exists(path):
            try:
                sound = SoundLoader.load(path)
                if sound:
                    self.current_bgm = sound
                    self.current_bgm.loop = True
                    self.current_bgm.volume = self.music_volume
                    self.current_bgm.play()
                    self.current_bgm_name = filename
                    Logger.info(f"Audio: Reproduciendo BGM -> {filename}")
                else:
                    self.current_bgm_name = None
                    Logger.error(f"Audio: No se pudo cargar el archivo BGM {path}")
            except Exception as e:
                self.current_bgm_name = None
                Logger.error(f"Audio: Excepción al reproducir BGM {path}: {e}")
        else:
            self.current_bgm_name = None
            Logger.error(f"Audio: Archivo de BGM no encontrado en {path}")

    def stop_bgm(self):
        if self.current_bgm:
            self.current_bgm.stop()
            self.current_bgm_name = None

    def set_volumes(self, music_vol: float, sfx_vol: float):
        self.music_volume = music_vol
        self.sfx_volume = sfx_vol
        if self.current_bgm:
            self.current_bgm.volume = self.music_volume