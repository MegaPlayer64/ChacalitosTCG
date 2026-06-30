file_path = "src/data/cards.csv"
import csv
from src.domain.unit import Unit
import os
import json

# from domain.skills.registry import SkillRegistry

class CardLoader:
    @staticmethod
    def load_units(file_path):
        units = []
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    c_type = str(row.get('CardType', '')).lower().strip()
                    if not c_type:
                        c_type = 'unit'

                    # Limpieza de datos numéricos (maneja el caso de los .0 del CSV y valores N/A)
                    def safe_int(val, default=0):
                        if not val or str(val).strip().upper() == 'N/A' or str(val).strip() == '-':
                            return default
                        try:
                            return int(float(val))
                        except:
                            return default

                    # Instanciamos la unidad con TODOS los argumentos que pide Unit.__init__
                    if c_type == 'unit':
                        new_unit = Unit(
                            id=safe_int(row['ID']),
                            name=row['Nombre'],
                            cost=safe_int(row['Coste']),
                            health=safe_int(row['Vida']),
                            attack=safe_int(row['Ataque']),
                            speed=safe_int(row['Velocidad']),
                            range_atk=safe_int(row['Rango_ataque'], default=1),
                            groups=row.get('Grupos', ''),
                            rarity=row.get('Rareza', 'Común'),
                            description=row.get('Descripción habilidad especial', '')
                        )
                        units.append(new_unit)
                    else:
                        from src.domain.card import Card
                        new_card = Card(
                            id=safe_int(row['ID']),
                            name=row['Nombre'],
                            card_type=c_type,
                            cost=safe_int(row['Coste']),
                            groups=row.get('Grupos', ''),
                            rarity=row.get('Rareza', 'Común'),
                            description=row.get('Descripción habilidad especial', '')
                        )
                        units.append(new_card)
            return units
        except Exception as e:
            print(f"Error al leer el CSV: {e}")
            return []

    @staticmethod
    def load_deck_old(deck_recipe_path, csv_path="src/data/cards.csv"):
        import json
        import copy
        try:
            with open(deck_recipe_path, 'r', encoding='utf-8') as f:
                card_ids = json.load(f)
            
            all_units = CardLoader.load_units(csv_path)
            units_by_id = {u.id: u for u in all_units}
            
            deck = []
            for cid in card_ids:
                if cid in units_by_id:
                    deck.append(copy.deepcopy(units_by_id[cid]))
                else:
                    print(f"[!] Warning: Carta con ID {cid} no encontrada en la base de datos.")
            return deck
        except Exception as e:
            print(f"Error al cargar el mazo {deck_recipe_path}: {e}")
            return []
    
    @staticmethod
    def get_card_stats_by_id(card_id, csv_path="src/data/cards.csv"):
        """Busca una carta específica por su ID en el CSV y devuelve su objeto listo."""
        all_cards = CardLoader.load_units(csv_path)
        for card in all_cards:
            if card.id == card_id:
                return card
        return None

    @staticmethod
    def load_deck(deck_recipe_path, csv_path="src/data/cards.csv", ruta_perfil="src/data/user_profile.json"):
        """
        Detecta si la referencia es un mazo predefinido (.json) o un mazo personal 
        almacenado dentro del perfil del usuario. Retorna una lista de OBJETOS instanciados.
        """
        import copy
        card_ids = []

        # === 1. EXTRAER LAS IDs DE CARTAS DEL ORIGEN CORRECTO ===
        # Caso A: Es un mazo personal guardado en el perfil (No termina en .json)
        if not str(deck_recipe_path).endswith('.json'):
            if os.path.exists(ruta_perfil):
                try:
                    with open(ruta_perfil, "r", encoding="utf-8") as f:
                        perfil = json.load(f)
                    mazos_usuario = perfil.get("decks", {})
                    if deck_recipe_path in mazos_usuario:
                        print(f"[+] Cargando mazo personal desde el perfil: {deck_recipe_path}")
                        card_ids = mazos_usuario[deck_recipe_path]
                except Exception as e:
                    print(f"[!] Error leyendo mazo personal '{deck_recipe_path}': {e}")
            
            # Si no se encontraron IDs, aplicamos fallback a mazo básico premade
            if not card_ids:
                deck_recipe_path = "src/data/premade_decks/tag_theme/dermapatch_basic_deck.json"

        # Caso B: Archivo físico .json tradicional (Modo Historia / Premade)
        if str(deck_recipe_path).endswith('.json'):
            try:
                with open(deck_recipe_path, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                card_ids = datos if isinstance(datos, list) else datos.get("cards", [])
            except Exception as e:
                print(f"[!] Error crítico al abrir mazo físico {deck_recipe_path}: {e}")
                return []

        # === 2. INFLAR LAS IDs CON LOS OBJETOS REALES DEL CSV ===
        all_units = CardLoader.load_units(csv_path)
        units_by_id = {u.id: u for u in all_units}
        
        deck_de_objetos = []
        for cid in card_ids:
            # Forzamos conversión a entero por si acaso
            cid_int = int(cid)
            if cid_int in units_by_id:
                # Usamos deepcopy para que cada carta en el mazo sea única en memoria
                deck_de_objetos.append(copy.deepcopy(units_by_id[cid_int]))
            else:
                print(f"[!] Warning: Carta con ID {cid_int} no encontrada en la base de datos CSV.")
                
        return deck_de_objetos