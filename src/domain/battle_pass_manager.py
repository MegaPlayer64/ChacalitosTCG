import json
import os
from datetime import datetime
from src.infrastructure.path_manager import PathManager

class BattlePassManager:
    def __init__(self, profile_path=None, season_config_path=None):
        self.profile_path = profile_path or PathManager.get_user_profile_path()
        self.season_config_path = season_config_path or PathManager.get_data_file_path("battle_pass_season.json")
        self.profile_data = self._load_json(self.profile_path)
        self.all_seasons_config = self._load_json(self.season_config_path)
        
        # Determinar la configuración de la temporada activa según el mes actual ("01" a "12")
        current_month = datetime.now().strftime("%m")
        if isinstance(self.all_seasons_config, dict) and current_month in self.all_seasons_config:
            self.season_config = self.all_seasons_config[current_month]
        elif isinstance(self.all_seasons_config, dict) and "season_name" in self.all_seasons_config:
            self.season_config = self.all_seasons_config
        elif isinstance(self.all_seasons_config, dict) and len(self.all_seasons_config) > 0:
            self.season_config = next(iter(self.all_seasons_config.values()))
        else:
            self.season_config = {}
        
        # Inicializar monedas y pase si no existen en el perfil
        coins = self.profile_data.setdefault("coins", 0)
        essence = self.profile_data.setdefault("craft_essence", self.profile_data.get("essence", 0))
        tickets = self.profile_data.setdefault("tickets", 0)
        self.profile_data.setdefault("currencies", {"coins": coins, "essence": essence, "tickets": tickets})
        
        year_str = datetime.now().strftime("%Y")
        season_id = self.season_config.get("season_id", current_month)
        self.profile_data.setdefault("battle_pass", {
            "current_season": f"{year_str}-{season_id}",
            "level": 1,
            "exp": 0,
            "claimed_levels": []
        })

        self.check_monthly_reset()

    def _load_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_profile(self):
        try:
            os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(self.profile_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f">> [!] Error al guardar perfil: {e}")

    def check_monthly_reset(self):
        """Si cambia la temporada (ej: de 01-02 a 03), reinicia el pase de batalla."""
        year_str = datetime.now().strftime("%Y")
        season_id = self.season_config.get("season_id", datetime.now().strftime("%m"))
        expected_season_key = f"{year_str}-{season_id}"
        bp_data = self.profile_data.setdefault("battle_pass", {})
        
        if bp_data.get("current_season") != expected_season_key:
            print(f">> [Battle Pass]: ¡Nueva temporada detectada ({expected_season_key})! Reiniciando pase...")
            bp_data["current_season"] = expected_season_key
            bp_data["level"] = 1
            bp_data["exp"] = 0
            bp_data["claimed_levels"] = []
            self._save_profile()

    def add_match_exp(self, won: bool, turns_played: int):
        """Otorga EXP al finalizar una partida."""
        base_exp = 50 if won else 20
        turn_bonus = min(turns_played * 2, 30)
        total_exp = base_exp + turn_bonus

        bp = self.profile_data["battle_pass"]
        exp_per_lvl = self.season_config.get("exp_per_level", 100)
        max_lvl = self.season_config.get("max_level", 30)

        if bp.get("level", 1) >= max_lvl:
            return {"exp_gained": total_exp, "level_up": False, "new_level": max_lvl}

        bp["exp"] = bp.get("exp", 0) + total_exp
        leveled_up = False

        while bp["exp"] >= exp_per_lvl and bp["level"] < max_lvl:
            bp["exp"] -= exp_per_lvl
            bp["level"] += 1
            leveled_up = True
            print(f">> [Battle Pass]: ¡Subiste al Nivel {bp['level']}!")

        self._save_profile()
        return {"exp_gained": total_exp, "level_up": leveled_up, "new_level": bp["level"]}

    def claim_reward(self, level: int) -> bool:
        """Reclama la recompensa de un nivel específico si está desbloqueado y no reclamado."""
        level_str = str(level)
        bp = self.profile_data.setdefault("battle_pass", {})
        rewards = self.season_config.get("rewards", {})

        current_level = bp.get("level", 1)
        claimed_levels = bp.setdefault("claimed_levels", [])

        if level > current_level:
            print(f">> [Battle Pass]: Aún no alcanzas el nivel {level}.")
            return False

        if level in claimed_levels:
            print(f">> [Battle Pass]: La recompensa del nivel {level} ya fue reclamada.")
            return False

        if level_str not in rewards:
            print(f">> [Battle Pass]: El nivel {level} no tiene recompensa configurada.")
            return False

        reward = rewards[level_str]
        r_type = reward.get("type")
        amount = reward.get("amount", 1)

        # Entregar recompensa sincronizando raíz y 'currencies'
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
            card_id = str(reward.get("card_id", "1"))
            inventory[card_id] = inventory.get(card_id, 0) + amount

        claimed_levels.append(level)
        self._save_profile()
        print(f">> [Battle Pass]: Recompensa del Nivel {level} reclamada: {reward.get('label')}")
        return True