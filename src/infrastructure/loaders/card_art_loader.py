"""
Cargador de Arte y Configuración de Encuadres de Cartas (CardArtLoader).

Gestiona la resolución de imágenes de cartas (.png, .jpg, .webp o placeholder)
y la persistencia de configuraciones de encuadre (zoom, offset_x, offset_y)
utilizando PathManager para compatibilidad con PC y móvil.
"""

import os
from src.infrastructure.path_manager import PathManager

DEFAULT_ART_CONFIG = {
    "zoom": 1.0,
    "offset_x": 0.0,
    "offset_y": 0.0
}


class CardArtLoader:
    _cached_configs = None

    @classmethod
    def get_config_file_path(cls) -> str:
        """Obtiene la ruta resuelta de card_art_config.json mediante PathManager."""
        return PathManager.get_data_file_path("card_art_config.json")

    @classmethod
    def load_all_configs(cls, force_reload: bool = False) -> dict:
        """Carga todas las configuraciones de encuadre desde el archivo JSON."""
        if cls._cached_configs is not None and not force_reload:
            return cls._cached_configs

        config_path = cls.get_config_file_path()
        data = PathManager.load_json(config_path)
        if not isinstance(data, dict):
            data = {}
        cls._cached_configs = data
        return cls._cached_configs

    @classmethod
    def save_all_configs(cls, configs: dict = None) -> bool:
        """Guarda el diccionario de configuraciones de encuadre en el archivo JSON."""
        if configs is not None:
            cls._cached_configs = configs
        elif cls._cached_configs is None:
            cls._cached_configs = cls.load_all_configs()

        config_path = cls.get_config_file_path()
        return PathManager.save_json(config_path, cls._cached_configs)

    @classmethod
    def get_art_config(cls, card_id: str | int) -> dict:
        """
        Retorna la configuración de encuadre para una carta específica:
        {"zoom": float, "offset_x": float, "offset_y": float}
        """
        cid_str = str(card_id).strip()
        configs = cls.load_all_configs()
        card_cfg = configs.get(cid_str)
        if not card_cfg or not isinstance(card_cfg, dict):
            return dict(DEFAULT_ART_CONFIG)

        return {
            "zoom": float(card_cfg.get("zoom", DEFAULT_ART_CONFIG["zoom"])),
            "offset_x": float(card_cfg.get("offset_x", DEFAULT_ART_CONFIG["offset_x"])),
            "offset_y": float(card_cfg.get("offset_y", DEFAULT_ART_CONFIG["offset_y"]))
        }

    @classmethod
    def set_art_config(
        cls, 
        card_id: str | int, 
        zoom: float, 
        offset_x: float, 
        offset_y: float, 
        auto_save: bool = True
    ) -> bool:
        """Actualiza la configuración de encuadre de una carta y opcionalmente persiste en disco."""
        cid_str = str(card_id).strip()
        configs = cls.load_all_configs()
        configs[cid_str] = {
            "zoom": round(float(zoom), 3),
            "offset_x": round(float(offset_x), 1),
            "offset_y": round(float(offset_y), 1)
        }
        cls._cached_configs = configs
        if auto_save:
            return cls.save_all_configs()
        return True

    @staticmethod
    def get_card_art_path(card_id: str | int) -> str:
        """
        Devuelve la ruta absoluta de la imagen de la carta usando PathManager.
        Busca .png, .jpg, .jpeg y .webp en:
        1. src/images/cards/{cid_str}.ext
        2. assets/cards/{cid_str}.ext
        Si no la encuentra, retorna el placeholder en src/images/cards/placeholder.png.
        """
        cid_str = str(card_id).strip()
        extensions = [".png", ".jpg", ".jpeg", ".webp"]

        candidate_dirs = [
            os.path.join("src", "images", "cards"),
            os.path.join("assets", "cards"),
            os.path.join("images", "cards"),
        ]

        for folder in candidate_dirs:
            for ext in extensions:
                rel_path = os.path.join(folder, f"{cid_str}{ext}")
                full_path = PathManager.get_asset_path(rel_path)
                if os.path.exists(full_path):
                    return full_path

        # Placeholder si aún no tiene ilustración propia
        placeholder_candidates = [
            os.path.join("src", "images", "cards", "placeholder.png"),
            os.path.join("assets", "cards", "placeholder.png"),
            os.path.join("src", "images", "BetaLogo.png"),
        ]

        for p_cand in placeholder_candidates:
            p_full = PathManager.get_asset_path(p_cand)
            if os.path.exists(p_full):
                return p_full

        return ""