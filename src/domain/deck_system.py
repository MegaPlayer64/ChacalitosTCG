import json
import os

class DeckSystem:
    @staticmethod
    def guardar_mazo(nombre_mazo, lista_ids, ruta_perfil="src/data/user_profile.json"):
        if not os.path.exists(ruta_perfil):
            return False
            
        try:
            with open(ruta_perfil, "r", encoding="utf-8") as f:
                perfil = json.load(f)
                
            # BLINDAJE: Si 'decks' no existe en el JSON, lo inicializamos como diccionario vacío
            if "decks" not in perfil:
                perfil["decks"] = {}
                
            # Guardamos las IDs como enteros limpios
            perfil["decks"][nombre_mazo] = [int(cid) for cid in lista_ids]
            
            with open(ruta_perfil, "w", encoding="utf-8") as f:
                json.dump(perfil, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[!] Error al guardar mazo: {e}")
            return False