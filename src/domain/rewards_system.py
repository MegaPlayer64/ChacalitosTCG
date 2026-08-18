import json
import os
import random

class RewardsSystem:
    @staticmethod
    def otorgar_recompensa(
        victoria, 
        dificultad_rival="HUMANO", 
        duracion_segundos=60, 
        ruta_perfil="src/data/user_profile.json",
        monedas_base_override=None,
        mult_extra=1.0
    ):
        if not os.path.exists(ruta_perfil):
            print(f"[!] No se encontró el archivo de perfil en {ruta_perfil}")
            return None

        try:
            with open(ruta_perfil, "r", encoding="utf-8") as f:
                perfil = json.load(f)

            # 1. Determinación de Valores Base y Multiplicadores
            if monedas_base_override is not None:
                # Caso Personalizado / Modo Arcade
                monedas_base = monedas_base_override if victoria else 10
                esencia_base = 10 if victoria else 2
                mult = mult_extra
            else:
                # Caso Estándar
                monedas_base = 30 if victoria else 10
                esencia_base = 5 if victoria else 2

                # Mapeo y parseo tolerante de texto de dificultad
                dif_str = str(dificultad_rival).upper()
                if "DIFÍCIL" in dif_str or "DIFICIL" in dif_str or "HARD" in dif_str:
                    mult = 2.5
                elif "NORMAL" in dif_str or "MEDIUM" in dif_str:
                    mult = 1.5
                elif "FÁCIL" in dif_str or "FACIL" in dif_str or "EASY" in dif_str:
                    mult = 1.0
                else:
                    mult = 1.0

                mult *= mult_extra

            monedas_finales = int(monedas_base * mult)
            esencia_final_ganada = int(esencia_base * mult)

            # 2. Lógica del Ticket de Gacha (25% de probabilidad)
            ticket_ganado = False
            if duracion_segundos >= 60 and random.random() <= 0.25:
                ticket_ganado = True
                perfil["tickets"] = perfil.get("tickets", 0) + 1

            # 3. Actualizar economías en la estructura del JSON
            perfil["coins"] = perfil.get("coins", 0) + monedas_finales
            perfil["craft_essence"] = perfil.get("craft_essence", 0) + esencia_final_ganada

            # 4. Guardar en disco
            with open(ruta_perfil, "w", encoding="utf-8") as f:
                json.dump(perfil, f, indent=2, ensure_ascii=False)

            msg_ticket = " | 🎟️ ¡1 Ticket de Gacha obtenido!" if ticket_ganado else ""
            print(f"[💰] Recompensas aplicadas: +{monedas_finales} 🪙, +{esencia_final_ganada} ✨{msg_ticket} (Rival: {dificultad_rival})")

            return {
                "monedas": monedas_finales, 
                "esencia": esencia_final_ganada,
                "tickets": 1 if ticket_ganado else 0,
            }

        except Exception as e:
            print(f"[!] Error al procesar recompensas: {e}")
            return None