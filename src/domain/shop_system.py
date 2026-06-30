import json
import os
import random
from datetime import datetime

class ShopSystem:
    @staticmethod
    def obtener_rotacion_diaria(csv_path="src/data/cards.csv"):
        """Genera 3 cartas fijas para el día de hoy usando la fecha como semilla."""
        from src.infrastructure.loaders.card_loader import CardLoader

        todas_las_cartas = CardLoader.load_units(csv_path)
        if not todas_las_cartas:
            return []

        # Creamos una semilla usando el año, mes y día actual (ej: 20260628)
        fecha_hoy = datetime.now().strftime("%Y%m%d")
        random.seed(int(fecha_hoy))

        # Seleccionamos 3 cartas al azar del pool total para el día de hoy
        # Usamos sample para que no se repitan entre sí en la misma vitrina
        cantidad_ofertas = min(3, len(todas_las_cartas))
        cartas_hoy = random.sample(todas_las_cartas, cantidad_ofertas)

        # Precios fijos en esencias según su rareza
        precios = {
            "Común": 40,
            "Especial": 100,
            "Épica": 400,
            "Excelencia": 1600
        }

        ofertas = []
        for carta in cartas_hoy:
            rareza = getattr(carta, 'rarity', 'Común')
            ofertas.append({
                "id": carta.id,
                "nombre": carta.name,
                "rareza": rareza,
                "coste_energia": carta.cost,
                "tipo": 'unit' if hasattr(carta, 'attack') else getattr(carta, 'card_type', 'unit'),
                "precio_esencia": precios.get(rareza, 40)
            })

        # IMPORTANTE: Reseteamos la semilla de random para no alterar los sobres de gacha
        random.seed(None)
        return ofertas

    @staticmethod
    def comprar_carta_tienda(card_id, precio_esencia, ruta_perfil="src/data/user_profile.json"):
        """Procesa la compra deduciendo la esencia artesanal y añadiendo la ID al inventario."""
        if not os.path.exists(ruta_perfil):
            return {"exito": False, "mensaje": "Perfil no encontrado"}

        try:
            with open(ruta_perfil, "r", encoding="utf-8") as f:
                perfil = json.load(f)

            if perfil.get("craft_essence", 0) < precio_esencia:
                return {"exito": False, "mensaje": "Esencia insuficiente ✨"}

            # Verificar el tope técnico de 4 copias
            inventario = perfil.get("inventory", {})
            card_id_str = str(card_id)
            cantidad_actual = int(inventario.get(card_id_str, 0))

            if cantidad_actual >= 4:
                return {"exito": False, "mensaje": "¡Ya tienes el límite máximo de 4 copias de esta carta!"}

            # Aplicar transacción
            perfil["craft_essence"] -= precio_esencia
            inventario[card_id_str] = cantidad_actual + 1
            perfil["inventory"] = inventario

            with open(ruta_perfil, "w", encoding="utf-8") as f:
                json.dump(perfil, f, indent=2, ensure_ascii=False)

            return {"exito": True, "nueva_esencia": perfil["craft_essence"]}

        except Exception as e:
            print(f"[!] Error en ShopSystem: {e}")
            return {"exito": False, "mensaje": "Error al procesar el archivo de guardado"}