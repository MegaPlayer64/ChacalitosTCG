import json
import os
import random
from src.infrastructure.path_manager import PathManager


class GachaSystem:
    # Cartas exclusivas fuera de sobres (99 = Richi (Discurso) por calendario diario 7 días)
    EXCLUIDAS_DE_SOBRES = {99}
    RAREZAS_EXCLUIDAS = {"Ficha", "Evento"}

    # Configuración declarativa de banners (sin range() manuales)
    BANNERS = {
        "SIMCE": {
            "destacadas": {60, 61, 88, 120, 130, 131, 134, 170, 172},
            "tags_comunes": {"Cabezal de Tren", "Ex-estudiantes", "Deportistas"},
            "comunes_extra": set(),
            "permitir_excelencias": True,
        },
        "ALIANZAS": {
            "destacadas": {68, 69, 70, 72, 73, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 169},
            "tags_comunes": {"3_NAI", "Danza", "PlaceHolder"},
            "comunes_extra": set(),
            "permitir_excelencias": True,
        },
        "HALLOWEEN": {
            "destacadas": {81, 89, 91, 92, 152, 153, 154, 155, 173},
            "tags_comunes": {"Tralaleros", "PlaceHolder", "3_NAI"},
            "comunes_extra": {82},  # Gorro Soviético (buscado por Helen Soviética #154)
            "permitir_excelencias": True,
        },
        "FERIA_LIBRO": {
            "destacadas": {75, 76, 77, 80, 101, 103, 104, 133, 139, 140},
            "tags_comunes": {"Literatura", "Sucesores", "Nuevo"},
            "comunes_extra": set(),
            "permitir_excelencias": True,
        },
        "GALAS": {
            "destacadas": {121, 125, 132, 157, 158, 159, 160, 161, 162, 163, 168, 171},
            "tags_comunes": {"Mish-B", "Sucesores", "Fuerzas Especiales Valenzuela"},
            "comunes_extra": set(),
            "permitir_excelencias": True,
        },
        "RAICES": {
            "destacadas": {66, 67, 79, 83, 84, 86, 87, 117, 142, 149},
            "tags_comunes": {"Mish-A", "Cabezal de Tren"},
            "comunes_extra": set(),
            "permitir_excelencias": True,
        },
        "JURASICO": {
            "destacadas": {94, 95, 98, 135, 146, 147, 166, 167},
            "tags_comunes": {"Ex-estudiantes", "Nuevo", "Tralaleros", "PlaceHolder"},
            "comunes_extra": set(),
            "permitir_excelencias": True,
        },
        # Master Pack de Tickets gratuitos (popurrí sin cartas Excelencia)
        "MASTER_PACK": {
            "destacadas": {
                66, 67, 73, 76, 77, 79, 80, 81, 98, 113, 114, 115, 121,
                131, 132, 133, 134, 135, 142, 146, 147, 149, 166, 167, 170, 173,
            },
            "tags_comunes": {
                "3_NAI", "Artista", "Cabezal de Tren", "Danza", "Deportistas",
                "Ex-estudiantes", "Fuerzas Especiales Valenzuela", "Futboleros",
                "Literatura", "Mish-A", "Mish-B", "Músico", "Nuevo", "PlaceHolder", "Tecnológico",
            },
            "comunes_extra": {82},
            "permitir_excelencias": False,
        },
    }

    # Alias retrocompatibles con nombres antiguos de la UI
    BANNER_ALIASES = {
        "FIESTASPATRIAS": "RAICES",
        "TICKETPACK1": "MASTER_PACK",
        "TICKETS": "MASTER_PACK",
    }

    @staticmethod
    def _extraer_grupos(carta) -> set:
        raw = (
            getattr(carta, "groups", None)
            or getattr(carta, "grupos", None)
            or getattr(carta, "Grupos", "")
        )
        if isinstance(raw, (list, tuple, set)):
            return {str(g).strip() for g in raw if str(g).strip() and str(g).strip() != "-"}
        return {g.strip() for g in str(raw).split(",") if g.strip() and g.strip() != "-"}

    @classmethod
    def _filtrar_pool_banner(cls, tipo_banner_upper: str, cartas_colectables: list):
        clave = cls.BANNER_ALIASES.get(tipo_banner_upper, tipo_banner_upper)
        config = cls.BANNERS.get(clave)

        # Banner GENERAL por defecto: todas las colectables sin Rate Up
        if not config:
            return cartas_colectables, set(), True

        destacadas = config["destacadas"]
        tags_objetivo = config["tags_comunes"]
        comunes_extra = config["comunes_extra"]
        permitir_excelencias = config.get("permitir_excelencias", True)

        pool_banner = []
        for c in cartas_colectables:
            cid = int(c.id)
            rareza = getattr(c, "rarity", "Común")

            if not permitir_excelencias and rareza == "Excelencia":
                continue

            # 1. Base universal (IDs 1..59)
            if cid <= 59:
                pool_banner.append(c)
            # 2. Cartas destacadas del banner
            elif cid in destacadas:
                pool_banner.append(c)
            # 3. Comunes post-59 heredadas automáticamente por etiqueta
            elif rareza == "Común":
                if cid in comunes_extra or (cls._extraer_grupos(c) & tags_objetivo):
                    pool_banner.append(c)

        ids_destacadas = {str(i) for i in destacadas}
        return pool_banner, ids_destacadas, permitir_excelencias

    @classmethod
    def abrir_sobre_avanzado(cls, tipo_banner="GENERAL", cantidad_cartas=5, costo=100, pago_con_ticket=False, ruta_perfil=None):
        from src.infrastructure.loaders.card_loader import CardLoader

        ruta_perfil = ruta_perfil or PathManager.get_user_profile_path()
        if not os.path.exists(ruta_perfil):
            return {"exito": False, "mensaje": "Perfil no encontrado"}

        with open(ruta_perfil, "r", encoding="utf-8") as f:
            perfil = json.load(f)

        # Validación de costo
        if pago_con_ticket:
            costo_tickets = 1
            if perfil.get("tickets", 0) < costo_tickets:
                return {"exito": False, "mensaje": "¡No tienes suficientes Tickets! 🎟️"}
        else:
            if perfil.get("coins", 0) < costo:
                return {"exito": False, "mensaje": "¡Monedas insuficientes! 🪙"}

        # 1. CARGAR CARTAS Y FILTRAR SOLO COLECTABLES DE SOBRE (153 cartas)
        todas_las_cartas = CardLoader.load_units(PathManager.get_data_file_path("cards.csv"))
        cartas_colectables = [
            c for c in todas_las_cartas
            if int(c.id) not in cls.EXCLUIDAS_DE_SOBRES
            and getattr(c, "rarity", "") not in cls.RAREZAS_EXCLUIDAS
            and getattr(c, "card_type", "") != "Ficha"
        ]

        # 2. FILTRAR EL POOL SEGÚN EL BANNER ELEGIDO
        multiplicador_rate_up = 2.0
        tipo_banner_upper = tipo_banner.upper()
        pool_banner, ids_destacadas, permitir_excelencias = cls._filtrar_pool_banner(
            tipo_banner_upper, cartas_colectables
        )

        if not pool_banner:
            pool_banner = cartas_colectables

        # 3. GENERACIÓN DE LAS 5 CARTAS DEL SOBRE
        cartas_ganadas = []

        for i in range(cantidad_cartas):
            es_slot_garantizado = (i == cantidad_cartas - 1)

            # A. TABLA DE PROBABILIDADES DE RAREZA
            if permitir_excelencias:
                if es_slot_garantizado:
                    rareza_elegida = random.choices(
                        population=["Especial", "Épica", "Excelencia"],
                        weights=[65, 25, 10],
                        k=1,
                    )[0]
                else:
                    rareza_elegida = random.choices(
                        population=["Común", "Especial", "Épica", "Excelencia"],
                        weights=[70, 20, 8, 2],
                        k=1,
                    )[0]
                orden_fallback = ["Común", "Especial", "Épica", "Excelencia"]
            else:
                # Banner gratuito de tickets (Master Pack): sin Excelencias
                if es_slot_garantizado:
                    rareza_elegida = random.choices(
                        population=["Especial", "Épica"],
                        weights=[75, 25],
                        k=1,
                    )[0]
                else:
                    rareza_elegida = random.choices(
                        population=["Común", "Especial", "Épica"],
                        weights=[72, 20, 8],
                        k=1,
                    )[0]
                orden_fallback = ["Común", "Especial", "Épica"]

            # B. FILTRAR POOL POR RAREZA DENTRO DEL BANNER
            pool_rareza = [c for c in pool_banner if getattr(c, "rarity", "Común") == rareza_elegida]

            # C. FALLBACK DE DEGRADACIÓN SEGURA
            if not pool_rareza:
                for fallback_rarity in orden_fallback:
                    pool_rareza = [c for c in pool_banner if getattr(c, "rarity", "Común") == fallback_rarity]
                    if pool_rareza:
                        break
            if not pool_rareza:
                pool_banner_seguro = [
                    c for c in pool_banner
                    if permitir_excelencias or getattr(c, "rarity", "Común") != "Excelencia"
                ]
                pool_rareza = pool_banner_seguro or pool_banner

            # D. SELECCIÓN CON RATE UP PONDERADO (2x para destacadas del banner)
            pesos_cartas = [
                multiplicador_rate_up if str(carta.id) in ids_destacadas else 1.0
                for carta in pool_rareza
            ]

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
            "nuevos_tickets": perfil.get("tickets", 0),
        }