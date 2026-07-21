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
        if tipo_banner == "SIMCE1":
            # int(c.id) para comparar números. range(1, 62) incluye del 1 al 61.
            pool_banner = [c for c in todas_las_cartas if int(c.id) in range(1, 61)]
            ids_destacadas = ["60", "61"]
            
        elif tipo_banner == "MISHEXPANSIONPACK1":
            # range(1, 60) incluye 1-59 | range(62, 68) incluye 62-67
            pool_banner = [
                c for c in todas_las_cartas 
                if int(c.id) in range(1, 60) or int(c.id) in range(62, 67)
            ]
            # Extraemos solo el str(c.id) y separamos correctamente el operador 'or'
            ids_destacadas = [
                str(c.id) for c in todas_las_cartas 
                if "Mish-A" in getattr(c, 'groups', '') or "Mish-B" in getattr(c, 'groups', '')
            ]
            
        elif tipo_banner == "ALIANZAS3RO":
            # range(1, 60) incluye 1-59 | range(68, 74) incluye 68-73
            pool_banner = [
                c for c in todas_las_cartas 
                if int(c.id) in range(1, 60) or int(c.id) in range(68, 73)
            ]
            ids_destacadas = ["68", "69", "70", "71", "72", "73"]
            
        else:
            # Banner General por defecto si no coincide ninguno
            pool_banner = todas_las_cartas
            ids_destacadas = []
        # Fallback de seguridad
        if not pool_banner:
            pool_banner = todas_las_cartas

# 3. BUCLE PARA GENERAR LAS RECOMPENSAS
        cartas_ganadas = []
        
        for _ in range(cantidad_cartas):
            # A. Calculamos la rareza teórica
            rareza_elegida = random.choices(
                population=["Común", "Especial", "Épica", "Excelencia"],
                weights=[70, 20, 8, 2],
                k=1
            )[0]
            
            # B. Intentamos buscar esa rareza DENTRO del pool permitido del banner
            pool_rareza = [c for c in pool_banner if getattr(c, 'rarity', 'Común') == rareza_elegida]
            
            # C. LÓGICA DE RATE UP (Solo si el dado acierta y existen destacadas de esa rareza)
            if ids_destacadas and random.random() <= probabilidad_rate_up:
                pool_destacadas = [
                    c for c in pool_banner 
                    if str(c.id) in ids_destacadas and getattr(c, 'rarity', 'Común') == rareza_elegida
                ]
                if pool_destacadas:
                    pool_rareza = pool_destacadas

            # === 🛡️ CORRECCIÓN: BLOQUEO DE CONTENCIÓN ESTRICTA ===
            # Si el banner NO TIENE la rareza elegida (ej: Excelencia en el pack Mish),
            # recalculamos de forma segura sin salirnos jamás de 'pool_banner'.
            if not pool_rareza:
                # Intentamos degradar a una "Épica" del propio banner
                pool_rareza = [c for c in pool_banner if getattr(c, 'rarity', 'Común') == "Épica"]
            if not pool_rareza:
                # Si tampoco hay Épicas, intentamos con una "Especial" del propio banner
                pool_rareza = [c for c in pool_banner if getattr(c, 'rarity', 'Común') == "Especial"]
            if not pool_rareza:
                # Si fallan las anteriores, aseguramos con una "Común" del propio banner
                pool_rareza = [c for c in pool_banner if getattr(c, 'rarity', 'Común') == "Común"]
            if not pool_rareza:
                # Último recurso absoluto: cualquier carta que exista en este banner
                pool_rareza = pool_banner
                
            # D. Elegimos la carta final del pool seguro
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