import random
import json
import os

class GachaSystem:
    @staticmethod
    def abrir_sobre_avanzado(tipo_banner="GENERAL", cantidad_cartas=3, costo=100, ruta_perfil="src/data/user_profile.json"):
        from src.infrastructure.loaders.card_loader import CardLoader

        if not os.path.exists(ruta_perfil):
            return {"exito": False, "mensaje": "Perfil no encontrado"}

        with open(ruta_perfil, "r", encoding="utf-8") as f:
            perfil = json.load(f)

        if perfil.get("coins", 0) < costo:
            return {"exito": False, "mensaje": "¡Monedas insuficientes! 🪙"}

        # 1. CARGAR TODAS LAS CARTAS DEL CSV
        todas_las_cartas = CardLoader.load_units("src/data/cards.csv")
        
        # --- CONFIGURACIÓN DEL BANNER ACTUAL ---
        pool_banner = todas_las_cartas
        ids_destacadas = [] # Cartas con "Rate Up" (Probabilidad aumentada)
        probabilidad_rate_up = 0.50 # 50% de chance de que te toque la destacada si aciertas la rareza
        
        # 2. FILTRAR EL POOL SEGÚN EL BANNER ELEGIDO
        if tipo_banner == "FEV":
            pool_banner = [c for c in todas_las_cartas if "Fuerzas Especiales Valenzuela" in getattr(c, 'groups', '') or "FEV" in getattr(c, 'groups', '')]
        
        elif tipo_banner == "TRALALEROS":
            pool_banner = [c for c in todas_las_cartas if "Tralaleros" in getattr(c, 'groups', '')]
        
        elif tipo_banner == "TRUCOS":
            pool_banner = [c for c in todas_las_cartas if getattr(c, 'card_type', 'unit') == 'spell']
        
        elif tipo_banner == "LLEGADA_12":
            # El pool general incluye todas las cartas (pueden salir antiguas)
            pool_banner = todas_las_cartas
            # PERO definimos las IDs de las 12 nuevas cartas para el RATE UP
            # NOTA: Cambia estos números por las IDs reales de tus 12 cartas nuevas en el CSV
            ids_destacadas = ["101", "102", "103", "104", "105", "106", "107", "108", "109", "110", "111", "112"]

        # Fallback de seguridad
        if not pool_banner:
            pool_banner = todas_las_cartas

        # 3. BUCLE PARA GENERAR LAS RECOMPENSAS
        cartas_ganadas = []
        
        for _ in range(cantidad_cartas):
            # A. Calculamos la rareza (Ej: "Tirada Épica!")
            rareza_elegida = random.choices(
                population=["Común", "Especial", "Épica", "Excelencia"],
                weights=[70, 20, 8, 2],
                k=1
            )[0]
            
            # B. Obtenemos las cartas de esa rareza en el banner actual
            pool_rareza = [c for c in pool_banner if getattr(c, 'rarity', 'Común') == rareza_elegida]
            
            # C. LÓGICA DE RATE UP (Probabilidad Aumentada)
            if ids_destacadas and random.random() <= probabilidad_rate_up:
                # El dado de Rate Up acertó. Forzamos a que el pool sea SOLO de las cartas destacadas de esa rareza
                pool_destacadas = [c for c in todas_las_cartas if str(c.id) in ids_destacadas and getattr(c, 'rarity', 'Común') == rareza_elegida]
                
                if pool_destacadas:
                    pool_rareza = pool_destacadas # Sobrescribimos el pool general por el destacado

            # Fallbacks si no hay cartas de esa rareza
            if not pool_rareza:
                pool_rareza = [c for c in todas_las_cartas if getattr(c, 'rarity', 'Común') == rareza_elegida]
            if not pool_rareza:
                pool_rareza = pool_banner
                
            # D. Elegimos la carta final
            carta_individual = random.choice(pool_rareza)
            cartas_ganadas.append(carta_individual)

            # 4. AGREGAR AL INVENTARIO DEL PERFIL
            card_id_str = str(carta_individual.id)
            if "inventory" not in perfil:
                perfil["inventory"] = {}
                
            if card_id_str in perfil["inventory"]:
                perfil["inventory"][card_id_str] += 1
            else:
                perfil["inventory"][card_id_str] = 1

        # 5. DESCONTAR DINERO Y GUARDAR
        perfil["coins"] -= costo
        with open(ruta_perfil, "w", encoding="utf-8") as f:
            json.dump(perfil, f, indent=2, ensure_ascii=False)

        return {
            "exito": True,
            "cartas": cartas_ganadas,
            "nuevas_monedas": perfil["coins"]
        }