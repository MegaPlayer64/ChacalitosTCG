import random
import json
import os
from src.infrastructure.path_manager import PathManager

class GachaSystem:
    @staticmethod
    def abrir_sobre_avanzado(tipo_banner="GENERAL", cantidad_cartas=5, costo=100, pago_con_ticket=False, ruta_perfil=None):
        from src.infrastructure.loaders.card_loader import CardLoader

        ruta_perfil = ruta_perfil or PathManager.get_user_profile_path()
        if not os.path.exists(ruta_perfil):
            return {"exito": False, "mensaje": "Perfil no encontrado"}

        with open(ruta_perfil, "r", encoding="utf-8") as f:
            perfil = json.load(f)

        # Validación de costo
        if pago_con_ticket:
            costo_tickets = 1  # 1 ticket por sobre
            if perfil.get("tickets", 0) < costo_tickets:
                return {"exito": False, "mensaje": "¡No tienes suficientes Tickets! 🎟️"}
        else:
            if perfil.get("coins", 0) < costo:
                return {"exito": False, "mensaje": "¡Monedas insuficientes! 🪙"}

        # 1. CARGAR CARTAS Y EXCLUIR FICHAS (TOKENS)
        todas_las_cartas = CardLoader.load_units(PathManager.get_data_file_path("cards.csv"))
        cartas_colectables = [
            c for c in todas_las_cartas 
            if getattr(c, 'rarity', '') != "Ficha" and getattr(c, 'card_type', '') != "Ficha"
        ]

        # 2. CONFIGURACIÓN DE BANNERS POR COLECCIÓN / TEMÁTICA
        ids_destacadas = []
        multiplicador_rate_up = 2.0  # Duplica las probabilidades relativas de la carta destacada

        tipo_banner_upper = tipo_banner.upper()

         # 2. FILTRAR EL POOL SEGÚN EL BANNER ELEGIDO
        if tipo_banner == "SIMCE":
            # int(c.id) para comparar números. range(1, 62) incluye del 1 al 61.
            pool_banner = [c for c in todas_las_cartas if int(c.id) in range(1, 62) or int(c.id) == 81 or int(c.id) == 88 or int(c.id) == 130]
            ids_destacadas = ["60", "61", "88", "130"]
            
        elif tipo_banner == "ALIANZAS":
            # range(1, 55) incluye 1-55 | range(68, 74) incluye 68-73
            pool_banner = [
                c for c in todas_las_cartas 
                if int(c.id) in range(1, 55) or int(c.id) in range(68, 74) or int(c.id) == 81
            ]
            ids_destacadas = ["68", "69", "70", "71", "72", "73"]
        
        elif tipo_banner == "TICKETPACK1":
            pool_banner = [c for c in todas_las_cartas if int(c.id) in range(1, 59) or int(c.id) in range(62, 67) or int(c.id) in range(74, 82)] 
            ids_destacadas = ["74","75","76","77","78","79","80"]

        elif tipo_banner == "FIESTASPATRIAS":
            pool_banner = [c for c in todas_las_cartas if int(c.id) in range(1, 59) or int(c.id) in range(74, 88)]
            ids_destacadas["83","84","86","87"]

        elif tipo_banner == "HALLOWEEN":
            pool_banner = [c for c in todas_las_cartas if int(c.id) in range(1, 59) or int(c.id) in range(89, 93)]

        else:
            # Banner General por defecto si no coincide ninguno
            pool_banner = todas_las_cartas
            ids_destacadas = []
        # Fallback de seguridad
        if not pool_banner:
            pool_banner = todas_las_cartas

        # Fallback de contención
        if not pool_banner:
            pool_banner = cartas_colectables

        # 3. GENERACIÓN DE LAS 5 CARTAS DEL SOBRE
        cartas_ganadas = []

        for i in range(cantidad_cartas):
            es_slot_garantizado = (i == cantidad_cartas - 1)  # El 5.º slot (índice 4) es garantizado

            # A. TABLA DE PROBABILIDADES DE RAREZA
            if es_slot_garantizado:
                # Slot 5: Mínimo Especial (65% Especial, 25% Épica, 10% Excelencia / Evento)
                rareza_elegida = random.choices(
                    population=["Especial", "Épica", "Excelencia"],
                    weights=[65, 25, 8],
                    k=1
                )[0]
            else:
                # Slots 1 a 4: Estándar (70% Común, 20% Especial, 8% Épica, 2% Excelencia / Evento)
                rareza_elegida = random.choices(
                    population=["Común", "Especial", "Épica", "Excelencia"],
                    weights=[70, 20, 7, 2],
                    k=1
                )[0]

            # B. FILTRAR POOL POR RAREZA DENTRO DEL BANNER
            pool_rareza = [c for c in pool_banner if getattr(c, 'rarity', 'Común') == rareza_elegida]

            # C. FALLBACK DE DEGRADACIÓN SEGURA (Si el banner no incluye esa rareza específica)
            if not pool_rareza:
                for fallback_rarity in ["Común", "Especial", "Épica", "Excelencia"]:
                    pool_rareza = [c for c in pool_banner if getattr(c, 'rarity', 'Común') == fallback_rarity]
                    if pool_rareza:
                        break
            if not pool_rareza:
                pool_rareza = pool_banner  # Última contención de seguridad absolute

            # D. SELECCIÓN CON RATE UP PONDERADO (2x multiplicador para destacadas)
            pesos_cartas = []
            for carta in pool_rareza:
                if str(carta.id) in ids_destacadas:
                    pesos_cartas.append(multiplicador_rate_up)
                else:
                    pesos_cartas.append(1.0)

            carta_seleccionada = random.choices(pool_rareza, weights=pesos_cartas, k=1)[0]
            cartas_ganadas.append(carta_seleccionada)

            # E. REGISTRO EN INVENTARIO DEL PERFIL
            card_id_str = str(carta_seleccionada.id)
            if "inventory" not in perfil:
                perfil["inventory"] = {}
            perfil["inventory"][card_id_str] = perfil["inventory"].get(card_id_str, 0) + 1

        # 4. DESCONTAR MONEDAS O TICKETS Y GUARDAR PERFIL
        if pago_con_ticket:
            perfil["tickets"] -= 1
            print(f"[🎟️] Tickets restantes: {perfil['tickets']}")
        else:
            perfil["coins"] -= costo
            print(f"[💰] Monedas restantes: {perfil['coins']}")

        with open(ruta_perfil, "w", encoding="utf-8") as f:
            json.dump(perfil, f, indent=2, ensure_ascii=False)

        return {
            "exito": True,
            "cartas": cartas_ganadas,
            "nuevas_monedas": perfil["coins"],
            "nuevos_tickets": perfil.get("tickets", 0)
        }