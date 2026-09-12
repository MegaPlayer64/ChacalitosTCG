"""
Módulo de Sincronización y Autenticación en la Nube (CloudSyncManager).

Permite autenticación remota (/api/login y /api/register) y sincronización
bidireccional Offline-First (/api/sync) de perfiles de usuario en Chacalitos TCG.
"""

import time
import requests
from src.infrastructure.path_manager import PathManager

DEFAULT_SERVER_URL = "http://192.168.1.15:8000"


class CloudSyncManager:
    SERVER_URL = DEFAULT_SERVER_URL
    TIMEOUT = 5

    @classmethod
    def set_server_url(cls, url: str):
        """Permite modificar dinámicamente la URL del servidor."""
        cls.SERVER_URL = url.rstrip("/")

    @classmethod
    def is_logged_in(cls) -> bool:
        """Verifica si el usuario actual tiene un auth_token guardado."""
        profile_path = PathManager.get_user_profile_path()
        profile_data = PathManager.load_json(profile_path)
        token = profile_data.get("auth_token")
        return bool(token)

    @classmethod
    def get_current_user(cls) -> str:
        """Retorna el nombre de usuario de la sesión activa o 'Invitado'."""
        profile_path = PathManager.get_user_profile_path()
        profile_data = PathManager.load_json(profile_path)
        if profile_data.get("auth_token"):
            return profile_data.get("username", "Jugador")
        return "Invitado"

    @classmethod
    def login(cls, username: str, password: str) -> dict:
        """Inicia sesión contra el servidor remoto."""
        return cls.login_or_register(username, password, register=False)

    @classmethod
    def register(cls, username: str, password: str) -> dict:
        """Registra una nueva cuenta en el servidor remoto."""
        return cls.login_or_register(username, password, register=True)

    @classmethod
    def login_or_register(cls, username: str, password: str, register: bool = False) -> dict:
        """
        Ejecuta la solicitud de login o registro contra el backend FastAPI.
        Actualiza el archivo de perfil local con el token y datos del usuario si tiene éxito.
        """
        username_clean = str(username).strip()
        if not username_clean or not password:
            return {"success": False, "error": "Usuario y contraseña no pueden estar vacíos."}

        endpoint = "/api/register" if register else "/api/login"
        url = f"{cls.SERVER_URL}{endpoint}"

        try:
            res = requests.post(
                url,
                json={"username": username_clean, "password": password},
                timeout=cls.TIMEOUT
            )
            if res.status_code == 200:
                data = res.json()
                profile_path = PathManager.get_user_profile_path()
                profile_data = PathManager.load_json(profile_path)

                profile_data["auth_token"] = data.get("token")
                profile_data["user_id"] = data.get("user_id")
                profile_data["username"] = data.get("username", username_clean)

                PathManager.save_json(profile_path, profile_data)
                
                # Intentar sincronizar inmediatamente después de iniciar sesión
                cls.sync_profile()

                return {"success": True, "data": data, "username": profile_data["username"]}
            
            try:
                error_detail = res.json().get("detail", f"Error {res.status_code} del servidor")
            except Exception:
                error_detail = f"Error {res.status_code} del servidor"
            return {"success": False, "error": error_detail}

        except requests.exceptions.ConnectionError:
            return {
                "success": False, 
                "error": f"No se pudo conectar con el servidor ({cls.SERVER_URL}). Comprueba tu red o juega en modo offline."
            }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "El servidor tardó demasiado en responder (Tiempo de espera agotado)."}
        except Exception as e:
            return {"success": False, "error": f"Fallo de conexión: {e}"}

    @classmethod
    def logout(cls) -> bool:
        """Cierra la sesión local borrando el auth_token y el user_id del perfil."""
        profile_path = PathManager.get_user_profile_path()
        profile_data = PathManager.load_json(profile_path)
        profile_data["auth_token"] = None
        profile_data["user_id"] = None
        return PathManager.save_json(profile_path, profile_data)

    @classmethod
    def sync_profile(cls) -> dict:
        """
        Sincronización Offline-First bidireccional basada en timestamps:
        - Si la nube tiene last_synced mayor: Descarga y actualiza el perfil local.
        - Si el perfil local tiene last_synced mayor o igual: Sube la copia local al servidor.
        """
        profile_path = PathManager.get_user_profile_path()
        profile_data = PathManager.load_json(profile_path)
        token = profile_data.get("auth_token")

        if not token:
            return {"success": False, "synced": False, "message": "Sin sesión activa. Modo local."}

        headers = {"Authorization": f"Bearer {token}"}
        url_sync = f"{cls.SERVER_URL}/api/sync"

        try:
            # 1. Consultar estado en la nube
            res = requests.get(url_sync, headers=headers, timeout=cls.TIMEOUT)
            if res.status_code == 401:
                # Token expirado o inválido
                cls.logout()
                return {"success": False, "synced": False, "message": "Sesión expirada. Inicia sesión nuevamente."}

            if res.status_code != 200:
                return {"success": False, "synced": False, "message": f"Servidor respondió con código {res.status_code}"}

            cloud_info = res.json()
            cloud_last_synced = float(cloud_info.get("last_synced") or 0)
            local_last_synced = float(profile_data.get("last_synced") or 0)

            # 2. Descargar de la nube si el servidor es más reciente
            if cloud_last_synced > local_last_synced and cloud_info.get("profile_data"):
                new_profile = cloud_info["profile_data"]
                new_profile["auth_token"] = token
                new_profile["user_id"] = profile_data.get("user_id")
                new_profile["last_synced"] = cloud_last_synced
                PathManager.save_json(profile_path, new_profile)
                print(">> [CloudSync] Perfil actualizado desde la nube exitosamente.")
                return {
                    "success": True, 
                    "synced": True, 
                    "action": "download", 
                    "message": "Datos descargados y actualizados desde la nube."
                }

            # 3. Subir a la nube si la copia local es más reciente o la nube está vacía
            else:
                # Actualizar timestamp local
                profile_data["last_synced"] = time.time()
                push_res = requests.post(
                    url_sync,
                    json={"profile_data": profile_data},
                    headers=headers,
                    timeout=cls.TIMEOUT
                )
                if push_res.status_code == 200:
                    server_last_synced = push_res.json().get("last_synced", profile_data["last_synced"])
                    profile_data["last_synced"] = server_last_synced
                    PathManager.save_json(profile_path, profile_data)
                    print(">> [CloudSync] Perfil sincronizado y subido a la nube.")
                    return {
                        "success": True, 
                        "synced": True, 
                        "action": "upload", 
                        "message": "Progreso subido a la nube correctamente."
                    }
                else:
                    return {
                        "success": False, 
                        "synced": False, 
                        "message": f"Error al subir perfil ({push_res.status_code})"
                    }

        except requests.exceptions.ConnectionError:
            print(f">> [CloudSync] Servidor offline en {cls.SERVER_URL}. Continuando en modo local.")
            return {"success": False, "synced": False, "message": "Servidor offline. Jugando en modo local."}
        except requests.exceptions.Timeout:
            print(">> [CloudSync] Tiempo de espera agotado al sincronizar.")
            return {"success": False, "synced": False, "message": "Tiempo de espera agotado con el servidor."}
        except Exception as e:
            print(f">> [CloudSync] Excepción al sincronizar: {e}")
            return {"success": False, "synced": False, "message": f"Error de sincronización: {e}"}