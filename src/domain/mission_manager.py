import os
import json
import random
import datetime

class MissionManager:
    PROFILE_PATH = "src/data/user_profile.json"
    CATALOG_PATH = "src/data/daily_missions_catalog.json"

    @classmethod
    def _load_profile(cls, profile_path=None):
        path = profile_path or cls.PROFILE_PATH
        if not os.path.exists(path):
            return {
                "username": "Jugador",
                "coins": 0,
                "craft_essence": 0,
                "inventory": {},
                "decks": {},
                "tickets": 0,
                "active_missions": [],
                "last_daily_reset": ""
            }
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Error al cargar perfil de usuario ({path}): {e}")
            return {}

    @classmethod
    def _save_profile(cls, perfil, profile_path=None):
        path = profile_path or cls.PROFILE_PATH
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(perfil, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[!] Error al guardar perfil de usuario ({path}): {e}")
            return False

    @classmethod
    def _load_catalog(cls, catalog_path=None):
        path = catalog_path or cls.CATALOG_PATH
        if not os.path.exists(path):
            print(f"[!] Catálogo de misiones no encontrado en {path}")
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Error al leer catálogo de misiones ({path}): {e}")
            return []

    @classmethod
    def _normalize_tags(cls, tags):
        if not tags:
            return []
        if isinstance(tags, str):
            return [t.strip().lower() for t in tags.replace('\n', ',').split(',') if t.strip()]
        elif isinstance(tags, (list, tuple, set)):
            return [str(t).strip().lower() for t in tags if str(t).strip()]
        return []

    @classmethod
    def _tag_matches(cls, target_tag, entity_tags):
        if not target_tag or str(target_tag).strip().lower() in ("todos", "any", "all", "*", ""):
            return True
        
        target = str(target_tag).strip().lower()
        tags_list = cls._normalize_tags(entity_tags)
        
        for t in tags_list:
            if target == t:
                return True
            if target == "mish" and ("mish" in t or t.startswith("mish-")):
                return True
            if target in t or t in target:
                return True
        return False

    @classmethod
    def get_or_create_daily_missions(cls, profile_path=None, catalog_path=None):
        """
        Verifica la fecha actual y entrega las 3 misiones del día.
        Si la fecha no coincide o no hay misiones, selecciona 3 al azar del catálogo.
        """
        profile_path = profile_path or cls.PROFILE_PATH
        catalog_path = catalog_path or cls.CATALOG_PATH

        perfil = cls._load_profile(profile_path)
        hoy = datetime.date.today().isoformat()

        last_reset = perfil.get("last_daily_reset", "")
        active = perfil.get("active_missions", [])

        if last_reset != hoy or not active:
            catalog = cls._load_catalog(catalog_path)
            if catalog:
                count = min(3, len(catalog))
                selected = random.sample(catalog, count)
                active = []
                for m in selected:
                    active.append({
                        "id": m["id"],
                        "description": m["description"],
                        "type": m["type"],
                        "target_tag": m.get("target_tag", "todos"),
                        "required_amount": int(m.get("required_amount", 1)),
                        "progress": 0,
                        "completed": False,
                        "claimed": False,
                        "reward_coins": int(m.get("reward_coins", 50)),
                        "reward_essence": int(m.get("reward_essence", 10))
                    })
                perfil["active_missions"] = active
                perfil["last_daily_reset"] = hoy
                cls._save_profile(perfil, profile_path)
                print(f"[📋 MISIONES] ¡Rotación diaria de misiones actualizada ({hoy}): {len(active)} misiones activas!")

        return perfil.get("active_missions", [])

    @classmethod
    def track_damage(cls, player_id, amount, tags=None, profile_path=None):
        """
        Registra daño infligido por el Jugador 1 (player_id == 0).
        """
        if player_id != 0 or amount <= 0:
            return
        
        profile_path = profile_path or cls.PROFILE_PATH
        cls.get_or_create_daily_missions(profile_path)
        perfil = cls._load_profile(profile_path)
        active = perfil.get("active_missions", [])
        changed = False

        for m in active:
            if m.get("type") == "deal_damage" and not m.get("completed", False):
                if cls._tag_matches(m.get("target_tag", "todos"), tags):
                    m["progress"] = min(m["required_amount"], m.get("progress", 0) + int(amount))
                    if m["progress"] >= m["required_amount"]:
                        m["completed"] = True
                        print(f"🎉 ¡Misión Diaria Completada: {m['description']}!")
                    changed = True

        if changed:
            perfil["active_missions"] = active
            cls._save_profile(perfil, profile_path)

    @classmethod
    def track_heal(cls, player_id, amount, tags=None, profile_path=None):
        """
        Registra curación recibida/aplicada por el Jugador 1 (player_id == 0).
        """
        if player_id != 0 or amount <= 0:
            return
        
        profile_path = profile_path or cls.PROFILE_PATH
        cls.get_or_create_daily_missions(profile_path)
        perfil = cls._load_profile(profile_path)
        active = perfil.get("active_missions", [])
        changed = False

        for m in active:
            if m.get("type") == "heal_hp" and not m.get("completed", False):
                if cls._tag_matches(m.get("target_tag", "todos"), tags):
                    m["progress"] = min(m["required_amount"], m.get("progress", 0) + int(amount))
                    if m["progress"] >= m["required_amount"]:
                        m["completed"] = True
                        print(f"🎉 ¡Misión Diaria Completada: {m['description']}!")
                    changed = True

        if changed:
            perfil["active_missions"] = active
            cls._save_profile(perfil, profile_path)

    @classmethod
    def track_kill(cls, killer_player_id, killer_tags=None, victim_tags=None, profile_path=None):
        """
        Registra la eliminación de una unidad enemiga por parte del Jugador 1 (killer_player_id == 0).
        """
        if killer_player_id != 0:
            return

        profile_path = profile_path or cls.PROFILE_PATH
        cls.get_or_create_daily_missions(profile_path)
        perfil = cls._load_profile(profile_path)
        active = perfil.get("active_missions", [])
        changed = False

        for m in active:
            if not m.get("completed", False):
                m_type = m.get("type")
                if m_type == "kill_unit_with_tag":
                    if cls._tag_matches(m.get("target_tag", "todos"), killer_tags):
                        m["progress"] = min(m["required_amount"], m.get("progress", 0) + 1)
                        if m["progress"] >= m["required_amount"]:
                            m["completed"] = True
                            print(f"🎉 ¡Misión Diaria Completada: {m['description']}!")
                        changed = True
                elif m_type == "kill_target_tag":
                    if cls._tag_matches(m.get("target_tag", "todos"), victim_tags):
                        m["progress"] = min(m["required_amount"], m.get("progress", 0) + 1)
                        if m["progress"] >= m["required_amount"]:
                            m["completed"] = True
                            print(f"🎉 ¡Misión Diaria Completada: {m['description']}!")
                        changed = True

        if changed:
            perfil["active_missions"] = active
            cls._save_profile(perfil, profile_path)

    @classmethod
    def claim_reward(cls, mission_id, profile_path=None):
        """
        Reclama la recompensa de una misión completada.
        Otorga monedas y esencias al perfil del usuario.
        """
        profile_path = profile_path or cls.PROFILE_PATH
        perfil = cls._load_profile(profile_path)
        active = perfil.get("active_missions", [])

        for m in active:
            if m.get("id") == mission_id:
                if not m.get("completed", False):
                    return {"exito": False, "mensaje": "Misión aún en progreso."}
                if m.get("claimed", False):
                    return {"exito": False, "mensaje": "Recompensa ya reclamada."}

                coins = int(m.get("reward_coins", 0))
                essence = int(m.get("reward_essence", 0))

                perfil["coins"] = perfil.get("coins", 0) + coins
                perfil["craft_essence"] = perfil.get("craft_essence", 0) + essence
                m["claimed"] = True

                perfil["active_missions"] = active
                cls._save_profile(perfil, profile_path)

                print(f"[🎁 RECOMPENSA RECLAMADA] +{coins} 🪙  +{essence} ✨ para la misión: {m['description']}")
                return {
                    "exito": True,
                    "mensaje": f"+{coins} 🪙  +{essence} ✨",
                    "coins_ganadas": coins,
                    "esencia_ganada": essence,
                    "nuevas_monedas": perfil["coins"],
                    "nueva_esencia": perfil["craft_essence"],
                    "mission": m
                }

        return {"exito": False, "mensaje": "Misión no encontrada."}
