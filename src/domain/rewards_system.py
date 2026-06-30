import json
import os

class RewardsSystem:
    @staticmethod
    def otorgar_recompensa(victoria, dificultad_rival="HUMANO", ruta_perfil="src/data/user_profile.json"):
        if not os.path.exists(ruta_perfil):
            return None

        try:
            with open(ruta_perfil, "r", encoding="utf-8") as f:
                perfil = json.load(f)

            # Valores Base de recompensa
            monedas_base = 30 if victoria else 10
            esencia_base = 5 if victoria else 2

            # Multiplicadores de reto según la IA configurada
            multiplicadores = {
                "IA FÁCIL": 1.0,
                "IA NORMAL": 1.5,
                "IA DIFÍCIL": 2.5,
                "HUMANO": 1.0
            }
            mult = multiplicadores.get(dificultad_rival.upper(), 1.0)

            monedas_finales = int(monedas_base * mult)
            esencia_final_ganada = int(esencia_base * mult)

            # Actualizar economías del JSON
            perfil["coins"] = perfil.get("coins", 0) + monedas_finales
            perfil["craft_essence"] = perfil.get("craft_essence", 0) + esencia_final_ganada

            with open(ruta_perfil, "w", encoding="utf-8") as f:
                json.dump(perfil, f, indent=2, ensure_ascii=False)

            print(f"[💰] Recompensas aplicadas: +{monedas_finales} 🪙, +{esencia_final_ganada} ✨ (Rival: {dificultad_rival})")
            return {"monedas": monedas_finales, "esencia": esencia_final_ganada}

        except Exception as e:
            print(f"[!] Error al procesar recompensas: {e}")
            return None