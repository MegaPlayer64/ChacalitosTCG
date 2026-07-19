# src/infrastructure/sheets_database.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class SheetsDatabase:
    def __init__(self):
        # 1. Configurar la conexión con las credenciales de Google API
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Necesitarás descargar un archivo .json de credenciales desde Google Cloud Console
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        self.client = gspread.authorize(creds)
        
        # 2. Abrir tu hoja de cálculo por su nombre exacto
        self.sheet = self.client.open("ChacalitosTCG_DB")

    def obtener_perfil_completo(self, target_username):
        """Descarga los datos de las 3 pestañas y arma el JSON para el juego."""
        try:
            # --- TABLA 1: USUARIO ---
            sheet_users = self.sheet.worksheet("usuarios")
            user_row = sheet_users.find(target_username)
            if not user_row:
                return None # Usuario no existe
                
            row_data = sheet_users.row_values(user_row.row)
            coins = int(row_data[1])
            craft_essence = int(row_data[2])

            # --- TABLA 2: INVENTARIO ---
            sheet_inv = self.sheet.worksheet("inventarios")
            # Obtenemos todas las filas y filtramos las que pertenecen al usuario
            all_inv = sheet_inv.get_all_records()
            user_inventory = {
                str(item["card_id"]): int(item["cantidad"]) 
                for item in all_inv if item["username"] == target_username
            }

            # --- TABLA 3: MAZOS ---
            sheet_decks = self.sheet.worksheet("mazos")
            all_decks = sheet_decks.get_all_records()
            
            # Reconstruimos los mazos dinámicos del usuario
            user_decks = {}
            for deck in all_decks:
                if deck["username"] == target_username:
                    # Convertimos la string "7,7,7..." de vuelta a una lista de enteros [7, 7, 7...]
                    cartas_lista = [int(x) for x in str(deck["cartas"]).split(",") if x.strip()]
                    user_decks[deck["nombre_mazo"]] = cartas_lista

            # --- RETORNAMOS LA ESTRUCTURA IDENTICA A TU JSON ---
            return {
                "username": target_username,
                "coins": coins,
                "inventory": user_inventory,
                "decks": user_decks,
                "craft_essence": craft_essence
            }
            
        except Exception as e:
            print(f"Error cargando desde Google Sheets: {e}")
            return None