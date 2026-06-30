import json
import os

class CraftSystem:
    @staticmethod
    def reciclar_excesos(ruta_perfil="src/data/user_profile.json"):
        # Importación local para evitar dependencias cíclicas con Kivy
        from src.infrastructure.loaders.card_loader import CardLoader

        if not os.path.exists(ruta_perfil):
            print(f"[!] CraftSystem: No se encontró el perfil en {ruta_perfil}")
            return {"exito": False, "mensaje": "Perfil no encontrado"}

        try:
            with open(ruta_perfil, "r", encoding="utf-8") as f:
                perfil = json.load(f)

            # Inicializar la clave de esencia si no existe
            if "craft_essence" not in perfil:
                perfil["craft_essence"] = 0

            # Forzar copia explícita del inventario para asegurar la mutación
            inventario = dict(perfil.get("inventory", {}))
            total_recicladas = 0
            esencia_ganada = 0

            valores_esencia = {
                "Común": 10,
                "Especial": 25,
                "Épica": 100,
                "Excelencia": 400
            }

            # Procesamos las cartas buscando excesos mayores al límite técnico de 4 copias
            for card_id_str, cantidad in list(inventario.items()):
                cantidad_int = int(cantidad)
                if cantidad_int > 4:
                    exceso = cantidad_int - 4
                    carta_obj = CardLoader.get_card_stats_by_id(int(card_id_str))
                    
                    if carta_obj:
                        rareza = getattr(carta_obj, 'rarity', 'Común')
                        valor = valores_esencia.get(rareza, 10)
                        
                        esencia_ganada += (exceso * valor)
                        total_recicladas += exceso
                        inventario[card_id_str] = 4  # Ajustamos al tope de copias permitidas

            if total_recicladas == 0:
                return {"exito": False, "mensaje": "No tienes cartas repetidas (más de 4 copias) para reciclar."}

            # ASIGNACIÓN DIRECTA Y ABSOLUTA AL DICCIONARIO PRINCIPAL
            perfil["craft_essence"] += esencia_ganada
            perfil["inventory"] = inventario

            # ESCRITURA FORZADA EN DISCO
            with open(ruta_perfil, "w", encoding="utf-8") as f:
                json.dump(perfil, f, indent=2, ensure_ascii=False)
            
            print(f"[+] CraftSystem: JSON guardado exitosamente. Esencia actual: {perfil['craft_essence']}")

            return {
                "exito": True,
                "cartas_rotas": total_recicladas,
                "esencia_obtenida": esencia_ganada,
                "total_esencia": perfil["craft_essence"]
            }

        except Exception as e:
            # Imprime directamente en la terminal de VS Code para capturar fallos de sintaxis o IO
            print(f"[!] ERROR CRÍTICO EN CRAFTSYSTEM: {e}")
            return {"exito": False, "mensaje": f"Error en el proceso: {e}"}