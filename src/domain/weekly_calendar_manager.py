import os
import json
import datetime
from src.infrastructure.path_manager import PathManager


class WeeklyCalendarManager:
    """
    Gestor del Calendario Semanal de Recompensas por inicio de sesión / paso de tiempo.
    
    Estructura de recompensas (Ciclo de 7 días):
      - Día 1: 300 Monedas de Oro 🪙
      - Día 2: 60 Esencia de Creación ✨
      - Día 3: 1 Ticket de Invocación Gacha 🎟️
      - Día 4: 600 Monedas de Oro 🪙
      - Día 5: 120 Esencia de Creación ✨
      - Día 6: 2 Tickets de Invocación Gacha 🎟️
      - Día 7: ¡Carta N°99 Richi (Discurso)! 🎴 (+ 500 Monedas de Oro de bonificación)
    
    Comportamiento con el paso del tiempo:
      - Cada día calendario real (YYYY-MM-DD), el jugador puede reclamar el siguiente día disponible.
      - Al completar el Día 7 y llegar un nuevo día, el calendario reinicia automáticamente su ciclo
        (Ciclo 2, 3...) para que el jugador continúe acumulando recompensas cada semana.
    """

    WEEKLY_REWARDS = [
        {
            "day": 1,
            "type": "coins",
            "amount": 300,
            "title": "Día 1",
            "label": "300 Monedas",
            "icon": "🪙",
            "description": "Oro para abrir sobres y forjar cartas en la tienda."
        },
        {
            "day": 2,
            "type": "essence",
            "amount": 60,
            "title": "Día 2",
            "label": "60 Esencia",
            "icon": "✨",
            "description": "Esencia mágica para fabricar cartas directamente."
        },
        {
            "day": 3,
            "type": "tickets",
            "amount": 1,
            "title": "Día 3",
            "label": "1 Ticket",
            "icon": "🎟️",
            "description": "Ticket para invocar en los banners de gacha."
        },
        {
            "day": 4,
            "type": "coins",
            "amount": 600,
            "title": "Día 4",
            "label": "600 Monedas",
            "icon": "🪙",
            "description": "¡Bolsa abundante de monedas para tu economía!"
        },
        {
            "day": 5,
            "type": "essence",
            "amount": 120,
            "title": "Día 5",
            "label": "120 Esencia",
            "icon": "✨",
            "description": "Esencia artesanal para crear cartas de alto rango."
        },
        {
            "day": 6,
            "type": "tickets",
            "amount": 2,
            "title": "Día 6",
            "label": "2 Tickets",
            "icon": "🎟️",
            "description": "¡Doble oportunidad para conseguir cartas raras!"
        },
        {
            "day": 7,
            "type": "card",
            "card_id": "99",
            "card_name": "Richi (Discurso)",
            "amount": 1,
            "title": "Día 7",
            "label": "Richi [Discurso]",
            "icon": "🎴",
            "bonus_coins": 500,
            "description": "¡Gran Recompensa! Copia garantizada de la carta N°99 Richi (Discurso) + 500 Monedas."
        }
    ]

    def __init__(self, profile_path=None):
        self.profile_path = profile_path or PathManager.get_user_profile_path()
        self.profile_data = self._load_profile()
        self._ensure_calendar_data()

    def _load_profile(self):
        if not os.path.exists(self.profile_path):
            return {
                "coins": 0,
                "craft_essence": 0,
                "tickets": 0,
                "inventory": {},
                "currencies": {"coins": 0, "essence": 0, "tickets": 0},
                "weekly_calendar": {
                    "current_cycle": 1,
                    "claimed_days": [],
                    "last_claim_date": ""
                }
            }
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f">> [WeeklyCalendarManager] Error al leer perfil ({self.profile_path}): {e}")
            return {}

    def _save_profile(self):
        try:
            os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(self.profile_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f">> [WeeklyCalendarManager] Error al guardar perfil ({self.profile_path}): {e}")
            return False

    def _ensure_calendar_data(self):
        """Garantiza la presencia de las claves del calendario semanal e inicializa ciclos."""
        # Monedas y divisas
        coins = self.profile_data.setdefault("coins", 0)
        essence = self.profile_data.setdefault("craft_essence", self.profile_data.get("essence", 0))
        tickets = self.profile_data.setdefault("tickets", 0)
        self.profile_data.setdefault("currencies", {"coins": coins, "essence": essence, "tickets": tickets})
        self.profile_data.setdefault("inventory", {})

        cal = self.profile_data.setdefault("weekly_calendar", {})
        cal.setdefault("current_cycle", 1)
        cal.setdefault("claimed_days", [])
        cal.setdefault("last_claim_date", "")

        # Comprobar si corresponde reiniciar ciclo (si ya completó el día 7 y es un día nuevo)
        today_str = datetime.date.today().isoformat()
        last_claim = cal.get("last_claim_date", "")
        claimed_days = cal.get("claimed_days", [])

        if len(claimed_days) >= 7 and last_claim != today_str:
            print(f">> [WeeklyCalendar]: ¡Ciclo {cal.get('current_cycle', 1)} completado! Iniciando nuevo ciclo semanal...")
            cal["current_cycle"] = cal.get("current_cycle", 1) + 1
            cal["claimed_days"] = []
            self._save_profile()

    def get_status(self):
        """
        Retorna el estado detallado del calendario semanal para alimentar la interfaz.
        """
        self._ensure_calendar_data()
        cal = self.profile_data["weekly_calendar"]
        today_str = datetime.date.today().isoformat()
        last_claim = cal.get("last_claim_date", "")
        claimed_days = cal.get("claimed_days", [])

        claimed_today = (last_claim == today_str)

        if claimed_today:
            # Ya reclamó hoy; el día actual alcanzado es el último reclamado
            current_day = max(claimed_days) if claimed_days else 1
            can_claim_today = False
        else:
            # No ha reclamado hoy; el siguiente día disponible
            current_day = len(claimed_days) + 1
            if current_day > 7:
                current_day = 7
            can_claim_today = True

        # Construir lista de información de cada uno de los 7 días
        days_info = []
        for r in self.WEEKLY_REWARDS:
            d = r["day"]
            if d in claimed_days:
                status = "claimed"
            elif d == current_day and can_claim_today:
                status = "available"
            else:
                status = "locked"

            days_info.append({
                **r,
                "status": status,
                "is_current": (d == current_day),
                "is_grand_prize": (d == 7)
            })

        return {
            "current_cycle": cal.get("current_cycle", 1),
            "current_day": current_day,
            "can_claim_today": can_claim_today,
            "claimed_days": list(claimed_days),
            "last_claim_date": last_claim,
            "days_info": days_info,
            "coins": self.profile_data.get("coins", 0),
            "essence": self.profile_data.get("craft_essence", 0),
            "tickets": self.profile_data.get("tickets", 0),
        }

    def can_claim_today(self) -> bool:
        status = self.get_status()
        return status["can_claim_today"]

    def claim_today(self) -> dict:
        """
        Reclama la recompensa correspondiente al día actual.
        Entrega Oro, Esencia, Tickets o la Carta N°99 Richi (Discurso).
        """
        status = self.get_status()
        if not status["can_claim_today"]:
            return {
                "success": False,
                "message": "Ya reclamaste tu recompensa de hoy. ¡Vuelve mañana para continuar tu calendario!"
            }

        day_to_claim = status["current_day"]
        reward = next((r for r in self.WEEKLY_REWARDS if r["day"] == day_to_claim), None)

        if not reward:
            return {"success": False, "message": "No se encontró recompensa para el día actual."}

        # Aplicar recompensa
        r_type = reward["type"]
        amount = reward.get("amount", 1)

        currencies = self.profile_data.setdefault("currencies", {"coins": 0, "essence": 0, "tickets": 0})
        inventory = self.profile_data.setdefault("inventory", {})

        if r_type == "coins":
            self.profile_data["coins"] = self.profile_data.get("coins", 0) + amount
            currencies["coins"] = self.profile_data["coins"]
        elif r_type in ("essence", "craft_essence"):
            self.profile_data["craft_essence"] = self.profile_data.get("craft_essence", 0) + amount
            currencies["essence"] = self.profile_data["craft_essence"]
        elif r_type == "tickets":
            self.profile_data["tickets"] = self.profile_data.get("tickets", 0) + amount
            currencies["tickets"] = self.profile_data["tickets"]
        elif r_type == "card":
            card_id = str(reward.get("card_id", "99"))
            inventory[card_id] = inventory.get(card_id, 0) + amount
            # Bonificación adicional de oro si está definida
            bonus = reward.get("bonus_coins", 0)
            if bonus > 0:
                self.profile_data["coins"] = self.profile_data.get("coins", 0) + bonus
                currencies["coins"] = self.profile_data["coins"]

        # Registrar reclamo
        cal = self.profile_data.setdefault("weekly_calendar", {})
        claimed_days = cal.setdefault("claimed_days", [])
        if day_to_claim not in claimed_days:
            claimed_days.append(day_to_claim)
        cal["last_claim_date"] = datetime.date.today().isoformat()

        self._save_profile()
        print(f">> [WeeklyCalendar]: ¡Día {day_to_claim} reclamado con éxito! Recompensa: {reward.get('label')}")

        return {
            "success": True,
            "day": day_to_claim,
            "reward": reward,
            "message": f"¡Has reclamado {reward.get('label')} con éxito!"
        }

    def reset_for_testing(self, simulate_next_day=True):
        """Herramienta de desarrollo/pruebas para avanzar o reiniciar el estado de reclamo."""
        cal = self.profile_data.setdefault("weekly_calendar", {})
        if simulate_next_day:
            # Simula que la última fecha fue ayer
            cal["last_claim_date"] = "2020-01-01"
        else:
            cal["current_cycle"] = 1
            cal["claimed_days"] = []
            cal["last_claim_date"] = ""
        self._save_profile()

