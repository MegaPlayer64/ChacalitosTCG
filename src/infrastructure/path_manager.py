"""
Módulo de Gestión Dinámica de Rutas (PathManager) para LBSB Engine v2.

Diseñado para soportar 100% ejecución congelada con PyInstaller (.exe)
y despliegues móviles con Buildozer (.apk Android), garantizando permisos
de lectura/escritura y compatibilidad con sincronización futura en la nube.
"""

import os
import sys
import shutil
import json


class PathManager:
    _user_data_dir = None
    _asset_base_dir = None

    @classmethod
    def get_asset_base_dir(cls) -> str:
        """
        Retorna la ruta base de recursos empaquetados (Read-Only).
        - En PyInstaller congelado: sys._MEIPASS.
        - En modo normal / desarrollo: Directorio raíz del proyecto.
        """
        if cls._asset_base_dir is not None:
            return cls._asset_base_dir

        if getattr(sys, "frozen", False):
            cls._asset_base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Subir dos niveles desde src/infrastructure -> raíz del proyecto
            cls._asset_base_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))

        return cls._asset_base_dir

    @classmethod
    def get_user_data_dir(cls) -> str:
        """
        Retorna la ruta segura de almacenamiento persistente con permisos de escritura (Read/Write).
        - Android (Buildozer): App.get_running_app().user_data_dir.
        - Windows congelado (PyInstaller): %APPDATA%/LBSB_Engine
        - Linux congelado: ~/.local/share/LBSB_Engine o XDG_DATA_HOME
        - Modo desarrollo (no congelado): <project_root>/src/data
        """
        if cls._user_data_dir is not None and os.path.exists(cls._user_data_dir):
            return cls._user_data_dir

        user_dir = None

        # 1. Caso Android (Buildozer / Kivy)
        try:
            from kivy.utils import platform
            if platform == 'android':
                from kivy.app import App
                app = App.get_running_app()
                if app and getattr(app, "user_data_dir", None):
                    user_dir = app.user_data_dir
                else:
                    user_dir = os.environ.get("ANDROID_PRIVATE", os.path.expanduser("~"))
        except Exception:
            pass

        # 2. Caso Ejecutable Congelado (PyInstaller en PC)
        if not user_dir and getattr(sys, "frozen", False):
            if sys.platform.startswith("win"):
                appdata = os.environ.get("APPDATA")
                if appdata:
                    user_dir = os.path.join(appdata, "LBSB_Engine")
                else:
                    user_dir = os.path.join(os.path.dirname(sys.executable), "user_data")
            elif sys.platform.startswith("linux"):
                xdg_data = os.environ.get("XDG_DATA_HOME")
                if xdg_data:
                    user_dir = os.path.join(xdg_data, "LBSB_Engine")
                else:
                    user_dir = os.path.expanduser("~/.local/share/LBSB_Engine")
            else:
                user_dir = os.path.expanduser("~/Library/Application Support/LBSB_Engine")

        # 3. Caso Desarrollo local estándar
        if not user_dir:
            base_dir = cls.get_asset_base_dir()
            user_dir = os.path.join(base_dir, "src", "data")

        cls._user_data_dir = os.path.abspath(user_dir)
        cls.ensure_data_dir_exists()
        return cls._user_data_dir

    @classmethod
    def ensure_data_dir_exists(cls) -> str:
        """Crea el directorio de datos si no existe y lo retorna."""
        if not cls._user_data_dir:
            cls.get_user_data_dir()
        os.makedirs(cls._user_data_dir, exist_ok=True)
        return cls._user_data_dir

    @classmethod
    def get_asset_path(cls, relative_path: str) -> str:
        """
        Retorna la ruta absoluta para un archivo de recurso/asset relativo a la raíz.
        Ejemplo: get_asset_path("src/data/cards.csv")
        """
        return os.path.abspath(os.path.join(cls.get_asset_base_dir(), relative_path))

    @classmethod
    def get_user_profile_path(cls) -> str:
        """
        Retorna la ruta segura del archivo 'user_profile.json' con permisos de escritura.
        Si el archivo no existe en el directorio de usuario (ej: primera ejecución en Android o .exe),
        lo inicializa copiándolo desde la plantilla empaquetada o creando una estructura válida
        con soporte para sincronización en la nube (auth_token, user_id, last_synced).
        """
        data_dir = cls.get_user_data_dir()
        profile_path = os.path.join(data_dir, "user_profile.json")

        if not os.path.exists(profile_path):
            cls._initialize_default_profile(profile_path)
        else:
            cls._ensure_cloud_keys(profile_path)

        return profile_path

    @classmethod
    def get_data_file_path(cls, filename: str) -> str:
        """
        Resuelve la ruta para un archivo de datos:
        - Si es 'user_profile.json', redirige a get_user_profile_path().
        - Si ya existe en el directorio de usuario (escritura), retorna esa ruta.
        - Si existe en los assets empaquetados (lectura), retorna la ruta del asset.
        - Por defecto, retorna la ruta proyectada en el directorio de datos del usuario.
        """
        basename = os.path.basename(filename)
        if basename == "user_profile.json":
            return cls.get_user_profile_path()

        # Comprobar en datos de usuario
        user_path = os.path.join(cls.get_user_data_dir(), basename)
        if os.path.exists(user_path):
            return user_path

        # Comprobar en assets empaquetados
        candidates = [
            cls.get_asset_path(filename),
            cls.get_asset_path(os.path.join("src", "data", basename)),
            cls.get_asset_path(os.path.join("data", basename)),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate

        return user_path

    @classmethod
    def _initialize_default_profile(cls, target_path: str):
        """Copia la plantilla o genera un perfil inicial con claves de nube."""
        template_candidates = [
            cls.get_asset_path(os.path.join("src", "data", "user_profile.json")),
            cls.get_asset_path("user_profile.json"),
        ]
        copied = False
        for template in template_candidates:
            if os.path.exists(template) and os.path.abspath(template) != os.path.abspath(target_path):
                try:
                    shutil.copy2(template, target_path)
                    cls._ensure_cloud_keys(target_path)
                    copied = True
                    break
                except Exception as e:
                    print(f">> [PathManager] Falló copia de plantilla {template}: {e}")

        if not copied:
            default_data = {
                "auth_token": None,
                "user_id": None,
                "last_synced": 0,
                "username": "TesterDante",
                "coins": 500,
                "craft_essence": 0,
                "tickets": 3,
                "inventory": {
                    "23": 4,
                    "22": 4,
                    "9": 4,
                    "8": 4,
                    "7": 4,
                    "13": 4,
                    "34": 4,
                    "42": 5,
                    "44": 4,
                    "46": 4,},
                "decks": {
                    "starter": [
                            23,
                            23,
                            23,
                            23,
                            22,
                            22,
                            22,
                            22,
                            9,
                            9,
                            9,
                            9,
                            8,
                            8,
                            8,
                            8,
                            7,
                            7,
                            7,
                            7,
                            13,
                            13,
                            13,
                            13,
                            34,
                            34,
                            34,
                            34,
                            42,
                            42,
                            42,
                            42,
                            44,
                            44,
                            44,
                            44,
                            46,
                            46,
                            46,
                            46
                            ]
                },
                "active_missions": [],
                "last_daily_reset": "",
                "currencies": {"coins": 500, "essence": 0, "tickets": 3},
                "battle_pass": {
                    "current_season": "",
                    "level": 1,
                    "exp": 0,
                    "claimed_levels": []
                }
            }
            try:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(default_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f">> [PathManager] Error al generar perfil por defecto: {e}")

    @classmethod
    def _ensure_cloud_keys(cls, profile_path: str):
        """Garantiza que las claves de nube (auth_token, user_id, last_synced) existan."""
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            updated = False
            for key, default_val in [("auth_token", None), ("user_id", None), ("last_synced", 0)]:
                if key not in data:
                    data[key] = default_val
                    updated = True

            if updated:
                with open(profile_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    @classmethod
    def load_json(cls, file_path: str) -> dict:
        """Carga de forma segura un archivo JSON."""
        try:
            if not os.path.exists(file_path):
                return {}
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f">> [PathManager] Error al leer JSON ({file_path}): {e}")
            return {}

    @classmethod
    def save_json(cls, file_path: str, data: dict) -> bool:
        """Guarda de forma segura un diccionario en formato JSON."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f">> [PathManager] Error al guardar JSON ({file_path}): {e}")
            return False

