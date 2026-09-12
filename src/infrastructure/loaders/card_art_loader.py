import os
from src.infrastructure.path_manager import PathManager

class CardArtLoader:
    @staticmethod
    def get_card_art_path(card_id: str | int) -> str:
        """
        Devuelve la ruta absoluta de la imagen de la carta usando PathManager.
        Busca .png, .jpg y .webp en la carpeta assets/cards/.
        Si no la encuentra, retorna la imagen placeholder.png.
        """
        cid_str = str(card_id).strip()
        extensions = [".png", ".jpg", ".jpeg", ".webp"]

        for ext in extensions:
            rel_path = f"assets/cards/{cid_str}{ext}"
            full_path = PathManager.get_asset_path(rel_path)
            if os.path.exists(full_path):
                return full_path

        # Imagen por defecto si la carta no tiene arte aún
        placeholder = PathManager.get_asset_path("assets/images/cards/placeholder.png")
        if os.path.exists(placeholder):
            return placeholder

        return ""