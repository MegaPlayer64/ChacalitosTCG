import json
import os
import random

class RewardsSystem:
    @staticmethod
    def otorgar_recompensa(
        victoria, 
        dificultad_rival="HUMANO", 
        duracion_segundos=60, 
        ruta_perfil="src/data/user_profile.json"
    ):
        if not os.path.exists(ruta_perfil):
            return None

        try:
            with open(ruta_perfil, "r", encoding="utf-8") as f:
                perfil = json.load(f)

            # 1. Valores Base de recompensa
            monedas_base = 30 if victoria else 10
            esencia_base = 5 if victoria else 2

            # 2. Multiplicadores de reto según la IA configurada
            multiplicadores = {
                "IA FÁCIL": 1.0,
                "IA NORMAL": 1.5,
                "IA DIFÍCIL": 2.5,
                "HUMANO": 1.0
            }
            mult = multiplicadores.get(dificultad_rival.upper(), 1.0)

            monedas_finales = int(monedas_base * mult)
            esencia_final_ganada = int(esencia_base * mult)

            # 3. Lógica del Ticket de Gacha (25% de probabilidad)
            ticket_ganado = False
            # Filtro anti-exploit: Solo si la partida duró al menos 60 segundos
            if duracion_segundos >= 60 and random.random() <= 0.25:
                ticket_ganado = True
                perfil["tickets"] = perfil.get("tickets", 0) + 1

            # 4. Actualizar economías en la estructura del JSON
            perfil["coins"] = perfil.get("coins", 0) + monedas_finales
            perfil["craft_essence"] = perfil.get("craft_essence", 0) + esencia_final_ganada

            # 5. Guardar en disco
            with open(ruta_perfil, "w", encoding="utf-8") as f:
                json.dump(perfil, f, indent=2, ensure_ascii=False)

            # 6. Logging y Retorno de datos
            msg_ticket = " | 🎟️ ¡1 Ticket de Gacha obtenido!" if ticket_ganado else ""
            print(f"[💰] Recompensas aplicadas: +{monedas_finales} 🪙, +{esencia_final_ganada} ✨{msg_ticket} (Rival: {dificultad_rival})")

            return {
                "monedas": monedas_finales, 
                "esencia": esencia_final_ganada,
                "ticket_ganado": ticket_ganado
            }

        except Exception as e:
            print(f"[!] Error al procesar recompensas: {e}")
            return None