import json
import requests
import traceback
from domain.action import Action
from domain.action_type import ActionType
from interfaces.controllers.ai_controller import AIController


class LLMAIController(AIController):
    def __init__(self, player_id, model_name="gemma2:2b", api_url="http://localhost:11434/api/generate"):
        super().__init__(player_id=player_id, difficulty="LLM", delay=0.3)
        self.model_name = model_name
        self.api_url = api_url
        self.failed_spells_this_turn = set()

    def get_action(self, game_state) -> Action:
        # Reset de fallos si cambió el jugador activo
        if game_state.current_player_id != self.player_id:
            self.failed_spells_this_turn.clear()

        # 1. Resolver habilidades pendientes de forma estructurada
        if getattr(game_state, 'pending_ability', None):
            action = self._resolve_pending_ability_ai(game_state)
            return self._log_and_return_action(action, game_state)

        # 2. Generar lista de acciones legales filtradas
        legal_actions = self._get_smart_legal_actions(game_state)
        if not legal_actions or len(legal_actions) == 0:
            return self._log_and_return_action(Action(ActionType.END_TURN, self.player_id, {}), game_state)

        # 3. Consultar a Gemma
        try:
            llm_action = self._consult_gemma(game_state, legal_actions)
            if llm_action:
                return self._log_and_return_action(llm_action, game_state)
        except Exception as e:
            print(f">> [GEMMA ERROR]: {e}")
            traceback.print_exc()

        # Fallback a la heurística HARD si Gemma no responde a tiempo
        print(">> [LLM Fallback]: Usando heurística HARD.")
        return self._log_and_return_action(self._get_hard_action(game_state, legal_actions), game_state)

    def _get_smart_legal_actions(self, game_state) -> list:
        """Filtra acciones imposibles o fuera de rango antes de mostrárselas a la LLM."""
        raw_actions = self._get_all_legal_actions(game_state)
        filtered_actions = []
        player = game_state.players[self.player_id]

        tropas_propias = [
            u for u in game_state.board.grid.values() 
            if getattr(u, 'owner_id', None) == self.player_id
        ]

        for act in raw_actions:
            # 1. FILTRO DE ATAQUE A BASE (Solo si la tropa está en la zona enemiga)
            if act.type == ActionType.ATTACK and act.payload.get('target') == 'B':
                fx, _ = act.payload['from']
                col_base_valida = [0, 1] if self.player_id == 1 else [4, 5]
                if fx not in col_base_valida:
                    continue

            # 2. FILTRO DE ATAQUE A UNIDADES (Validar rango real y no autoatacarse)
            elif act.type == ActionType.ATTACK and isinstance(act.payload.get('target'), tuple):
                fx, fy = act.payload['from']
                tx, ty = act.payload['target']
                attacker = game_state.board.get_unit_at(fx, fy)
                target_unit = game_state.board.get_unit_at(tx, ty)

                if not attacker or not target_unit:
                    continue
                if target_unit.owner_id == self.player_id:
                    continue
                
                rng = game_state.get_effective_stats(attacker)["range_atk"]
                dist = max(abs(fx - tx), abs(fy - ty))
                if dist > rng:
                    continue

            # 3. FILTRO DE HECHIZOS
            elif act.type == ActionType.PLAY_SPELL:
                c_idx = act.payload.get('card_index')
                if c_idx in self.failed_spells_this_turn:
                    continue
                if c_idx < len(player.hand):
                    carta = player.hand[c_idx]
                    spell_type = self._get_spell_type(carta)
                    target = act.payload.get('target')

                    if spell_type in ('HEAL', 'BUFF'):
                        if target in ('B', 'G') or len(tropas_propias) == 0:
                            continue
                    elif spell_type in ('DAMAGE', 'DEBUFF'):
                        if target in ('B', 'G') and str(getattr(carta, 'id', '')) not in ('42',):
                            continue

            filtered_actions.append(act)

        return filtered_actions

    def _consult_gemma(self, game_state, legal_actions) -> Action:
        player = game_state.players[self.player_id]
        rival = game_state.players[1 - self.player_id]

        # 1. TABLERO
        unidades_tablero = []
        for (x, y), unit in game_state.board.grid.items():
            dueno = "Aliada" if unit.owner_id == self.player_id else "Enemiga"
            unidades_tablero.append(
                f"- ({x},{y}) [{dueno}] {unit.name} | ATK:{unit.attack} HP:{unit.health}/{unit.max_health}"
            )
        tablero_str = "\n".join(unidades_tablero) if unidades_tablero else "Tablero sin unidades."

        # 2. CARTAS EN MANO
        mano_txt = []
        for i, c in enumerate(player.hand):
            tipo = getattr(c, 'card_type', 'unit').upper()
            costo = getattr(c, 'cost', 0)
            desc = getattr(c, 'description', getattr(c, 'descripcion', 'Sin efecto')).replace('\n', ' ')
            mano_txt.append(f"[{i}] {c.name} ({tipo} - {costo}E) | Efecto: {desc}")
        mano_str = "\n".join(mano_txt) if mano_txt else "Mano vacía."

        # 3. OPCIONES CON ORIENTACIÓN Y SINTAXIS CONCISA
        opciones_txt = []
        for i, act in enumerate(legal_actions):
            desc = f"[{i}] {act.type.name}"
            if act.type in (ActionType.PLAY_CARD, ActionType.PLAY_SPELL):
                c_idx = act.payload.get('card_index', 0)
                if c_idx < len(player.hand):
                    carta = player.hand[c_idx]
                    desc += f" -> Jugar '{carta.name}' en {act.payload.get('to', act.payload.get('target'))}"
            
            elif act.type == ActionType.ATTACK:
                target = act.payload.get('target')
                if target == 'B':
                    desc += f" -> ¡ATACAR BASE RIVAL DIRECTAMENTE desde {act.payload.get('from')}!"
                else:
                    desc += f" -> Atacar unidad enemiga desde {act.payload.get('from')} a {target}"
            
            elif act.type == ActionType.MOVE:
                fx, fy = act.payload.get('from')
                tx, ty = act.payload.get('to')
                es_avance = (tx < fx) if self.player_id == 1 else (tx > fx)
                orientacion = "AVANZAR HACIA EL ENEMIGO" if es_avance else "Retroceder/Reubicar"
                desc += f" -> {orientacion} con tropa en ({fx},{fy}) hacia ({tx},{ty})"
            
            opciones_txt.append(desc)

        prompt = f"""Eres una IA jugando un TCG táctico.
Tu objetivo principal es AVANZAR tus tropas hacia las columnas del rival y ATACAR.

Tu Vida: {player.health} HP | Tu Energía: {player.current_energy}E
Vida Rival: {rival.health} HP

TUS CARTAS EN MANO:
{mano_str}

ESTADO DEL TABLERO:
{tablero_str}

OPCIONES LEGALES (ELIGE LA MEJOR):
{chr(10).join(opciones_txt)}

INSTRUCCIONES:
- Responde ÚNICAMENTE con un JSON: {{"choice": <numero_de_opcion>}}
"""

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "num_predict": 25,     # Límite estricto de generación (ultra rápido)
                "temperature": 0.1    # Respuestas deterministas y directas
            }
        }

        # Aumentamos el timeout a 20 segundos para que no vuelva a expirar
        response = requests.post(self.api_url, json=payload, timeout=20)
        if response.status_code == 200:
            res_json = json.loads(response.json().get("response", "{}"))
            choice_idx = int(res_json.get("choice", -1))

            if 0 <= choice_idx < len(legal_actions):
                return legal_actions[choice_idx]

        return None