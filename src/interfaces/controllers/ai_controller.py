import random
import time
from domain.action import Action
from domain.action_type import ActionType


class AIController:
    def __init__(self, player_id, difficulty="HARD", delay=1.5):
        self.player_id = player_id
        self.difficulty = difficulty.upper()
        self.delay = delay
        self.turn_energy_spent = 0
        self.turn_cards_played = 0
        self.abilitiestried = 0
        self.failed_abilities_this_turn = set()  # Guarda coordenadas (x, y) de habilidades fallidas en el turno

    def update_policy(self, result: str):
        """Stub para futura implementación de Reinforcement Learning."""
        pass

    def _log_and_return_action(self, action: Action, game_state) -> Action:
        if action.type != ActionType.END_TURN:
            if action.type == ActionType.PLAY_CARD:
                card_index = action.payload['card_index']
                card = game_state.players[self.player_id].hand[card_index]
                self.turn_cards_played += 1
                try:
                    cost = int(card.cost)
                except Exception:
                    cost = 0
                self.turn_energy_spent += cost
                detalle = f"Carta '{getattr(card, 'name', 'Desconocida')}' (Coste: {cost})"
            elif action.type == ActionType.PLAY_SPELL:
                card_index = action.payload['card_index']
                card = game_state.players[self.player_id].hand[card_index]
                self.turn_cards_played += 1
                try:
                    cost = int(card.cost)
                except Exception:
                    cost = 0
                self.turn_energy_spent += cost
                detalle = f"Hechizo '{getattr(card, 'name', 'Desconocido')}' -> {action.payload.get('target')}"
            elif action.type == ActionType.ATTACK:
                detalle = f"Ataque desde {action.payload.get('from')} a {action.payload.get('target')}"
            elif action.type == ActionType.MOVE:
                detalle = f"Movimiento de {action.payload.get('from')} a {action.payload.get('to')}"
            else:
                detalle = str(action.payload)
                
            print(f">> [IA] [{action.type.name}]: {detalle}")
        else:
            print(f">> [IA] [Resumen de Turno]: Energía gastada: {self.turn_energy_spent}, Cartas jugadas: {self.turn_cards_played}")
            # RESET DE ESTADOS DE TURNO
            self.turn_energy_spent = 0
            self.turn_cards_played = 0
            self.abilitiestried = 0
            self.failed_abilities_this_turn.clear()

        return action

    def get_action(self, game_state) -> Action:
        time.sleep(self.delay)

        try:
            # 1. INTERCEPTAR HABILIDADES PENDIENTES EN RESOLUCIÓN
            if getattr(game_state, 'pending_ability', None):
                action = self._resolve_pending_ability_ai(game_state)
                if action.type == ActionType.CANCEL_ABILITY:
                    self.abilitiestried += 1
                return self._log_and_return_action(action, game_state)

            # 2. OBTENER Y FILTRAR ACCIONES LEGALES
            legal_actions = self._get_all_legal_actions(game_state)
            
            if not legal_actions or len(legal_actions) == 0:
                return self._log_and_return_action(Action(ActionType.END_TURN, self.player_id, {}), game_state)

            if self.difficulty == "EASY":
                action = random.choice(legal_actions)
                return self._log_and_return_action(action, game_state)
                
            elif self.difficulty == "MEDIUM":
                action = self._get_medium_action(game_state, legal_actions)
                return self._log_and_return_action(action, game_state)
                
            elif self.difficulty == "HARD":
                action = self._get_hard_action(game_state, legal_actions)
                return self._log_and_return_action(action, game_state)
                
        except Exception as e:
            import traceback
            print(f">> [IA ERROR CRÍTICO] Excepción al decidir acción: {e}")
            traceback.print_exc()
            return self._log_and_return_action(Action(ActionType.END_TURN, self.player_id, {}), game_state)
            
        return self._log_and_return_action(Action(ActionType.END_TURN, self.player_id, {}), game_state)

    def _resolve_pending_ability_ai(self, game_state) -> Action:
        pending = game_state.pending_ability
        ability_name = pending.get('ability', '')
        
        # 1. encore: mover la unidad adyacente vacía
        if ability_name == 'encore':
            fx, fy = pending['unit_coords']
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                tx, ty = fx + dx, fy + dy
                if game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty):
                    return Action(ActionType.RESOLVE_ABILITY, self.player_id, {'target': (tx, ty)})
            return Action(ActionType.CANCEL_ABILITY, self.player_id, {})
            
        # 2. daiaodama: hacer daño a un enemigo a rango 3
        elif ability_name == 'daiaodama':
            fx, fy = pending['source_coords']
            enemy_id = 1 - self.player_id
            best_target = None
            max_value = -1
            for y in range(game_state.board.height):
                for x in range(game_state.board.width):
                    u = game_state.board.get_unit_at(x, y)
                    if u and u.owner_id == enemy_id:
                        dist = max(abs(fx - x), abs(fy - y))
                        if dist <= 3:
                            val = u.attack + u.health
                            if val > max_value:
                                max_value = val
                                best_target = (x, y)
            if best_target:
                return Action(ActionType.RESOLVE_ABILITY, self.player_id, {'target': best_target})
            return Action(ActionType.CANCEL_ABILITY, self.player_id, {})
            
        # 3. josefa_a: escudo a un aliado
        elif ability_name == 'josefa_a':
            best_target = None
            max_hp = -1
            for y in range(game_state.board.height):
                for x in range(game_state.board.width):
                    u = game_state.board.get_unit_at(x, y)
                    if u and u.owner_id == self.player_id:
                        if u.health > max_hp:
                            max_hp = u.health
                            best_target = (x, y)
            if best_target:
                return Action(ActionType.RESOLVE_ABILITY, self.player_id, {'target': best_target})
            return Action(ActionType.CANCEL_ABILITY, self.player_id, {})
            
        # 4. kapsi_retreat: Kapsi retrocede a una casilla vacía
        elif ability_name == 'kapsi_retreat':
            fx, fy = pending['unit_coords']
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    tx, ty = fx + dx, fy + dy
                    if game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty):
                        return Action(ActionType.RESOLVE_ABILITY, self.player_id, {'target': (tx, ty)})
            return Action(ActionType.CANCEL_ABILITY, self.player_id, {})
            
        # 5. cutino_summon: invocar a Gandan en una casilla adyacente vacía
        elif ability_name == 'cutino_summon':
            sx, sy = pending['source_coords']
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                tx, ty = sx + dx, sy + dy
                if game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty):
                    return Action(ActionType.RESOLVE_ABILITY, self.player_id, {'target': (tx, ty)})
            return Action(ActionType.CANCEL_ABILITY, self.player_id, {})
            
        # 6. zander_move_1: seleccionar un aliado
        elif ability_name == 'zander_move_1':
            sx, sy = pending['source_coords']
            best_target = None
            max_atk = -1
            for y in range(game_state.board.height):
                for x in range(game_state.board.width):
                    u = game_state.board.get_unit_at(x, y)
                    if u and u.owner_id == self.player_id and (x, y) != (sx, sy):
                        has_empty_adj = False
                        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                            nx, ny = x + dx, y + dy
                            if game_state.board.is_within_bounds(nx, ny) and not game_state.board.is_occupied(nx, ny):
                                has_empty_adj = True
                                break
                        if has_empty_adj and u.attack > max_atk:
                            max_atk = u.attack
                            best_target = (x, y)
            if best_target:
                return Action(ActionType.RESOLVE_ABILITY, self.player_id, {'target': best_target})
            return Action(ActionType.CANCEL_ABILITY, self.player_id, {})
            
        # 7. zander_move_2: mover el aliado seleccionado
        elif ability_name == 'zander_move_2':
            tux, tuy = pending['target_unit']
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                tx, ty = tux + dx, tuy + dy
                if game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty):
                    return Action(ActionType.RESOLVE_ABILITY, self.player_id, {'target': (tx, ty)})
            return Action(ActionType.CANCEL_ABILITY, self.player_id, {})
            
        # 8. dante_yukata_attack: atacar a un enemigo en rango + 1
        elif ability_name == 'dante_yukata_attack':
            sx, sy = pending['source_coords']
            unit = game_state.board.get_unit_at(sx, sy)
            if not unit:
                return Action(ActionType.CANCEL_ABILITY, self.player_id, {})
            
            eff_range = game_state.get_effective_stats(unit)["range_atk"]
            enemy_id = 1 - self.player_id
            best_target = None
            max_atk = -1
            
            for y in range(game_state.board.height):
                for x in range(game_state.board.width):
                    u = game_state.board.get_unit_at(x, y)
                    if u and u.owner_id == enemy_id:
                        dist = max(abs(sx - x), abs(sy - y))
                        if dist <= (eff_range + 1):
                            if u.attack > max_atk:
                                max_atk = u.attack
                                best_target = (x, y)
            if best_target:
                return Action(ActionType.RESOLVE_ABILITY, self.player_id, {'target': best_target})
            
            # Si no hay objetivo válido, cancelar sin congelarse
            return Action(ActionType.CANCEL_ABILITY, self.player_id, {})
            
        # 9. chino_quemadas: esquivar daño
        elif ability_name == 'chino_quemadas':
            fx, fy = pending['unit_coords']
            speed = pending.get('speed', 1)
            for dx in range(-speed, speed + 1):
                for dy in range(-speed, speed + 1):
                    dist = abs(dx) + abs(dy)
                    if 0 < dist <= speed:
                        tx, ty = fx + dx, fy + dy
                        if game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty):
                            return Action(ActionType.RESOLVE_ABILITY, self.player_id, {'target': (tx, ty)})
            return Action(ActionType.CANCEL_ABILITY, self.player_id, {})
            
        return Action(ActionType.CANCEL_ABILITY, self.player_id, {})

    # --- CLASIFICADOR DE HECHIZOS ---
    def _get_spell_type(self, card) -> str:
        if hasattr(card, 'effect_type') and card.effect_type:
            return card.effect_type.upper()

        card_id = str(getattr(card, 'id', ''))
        heals = {'33', '39', '41', '43', '50', '71', '77'}
        buffs = {'34', '36', '47', '48', '72', '76', '51'}
        damages = {'42', '46'}
        debuffs = {'35', '37'}
        draws = {'40', '44', '45'}
        
        if card_id in heals: return 'HEAL'
        if card_id in buffs: return 'BUFF'
        if card_id in damages: return 'DAMAGE'
        if card_id in debuffs: return 'DEBUFF'
        if card_id in draws: return 'DRAW'
        return 'UTILITY'

    # --- PRE-VALIDACIÓN DE REQUISITOS DE HABILIDAD ---
    def _can_unit_use_ability(self, unit, x, y, game_state) -> bool:
        """Verifica si la unidad cumple los requisitos tácticos reales antes de proponer ACTIVATE_ABILITY."""
        unit_id = int(unit.id)
        player = game_state.players[self.player_id]
        enemy_id = 1 - self.player_id

        # Si ya falló en este turno o se sobrepasó de intentos, ignorar
        if (x, y) in self.failed_abilities_this_turn or self.abilitiestried >= 3:
            return False

        # Dante Yukata (68): Requiere al menos UN enemigo en rango + 1
        if unit_id == 68:
            eff_range = game_state.get_effective_stats(unit)["range_atk"]
            for ey in range(game_state.board.height):
                for ex in range(game_state.board.width):
                    target = game_state.board.get_unit_at(ex, ey)
                    if target and target.owner_id == enemy_id:
                        if max(abs(x - ex), abs(y - ey)) <= (eff_range + 1):
                            return True
            return False

        # D. Cutiño (63): Requiere 3 de energía y espacio vacio adyacente
        elif unit_id == 63:
            if player.current_energy < 3:
                return False
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                tx, ty = x + dx, y + dy
                if game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty):
                    return True
            return False

        # Zander (64): Requiere otro aliado en tablero con espacio adyacente vacío
        elif unit_id == 64:
            for ey in range(game_state.board.height):
                for ex in range(game_state.board.width):
                    ally = game_state.board.get_unit_at(ex, ey)
                    if ally and ally.owner_id == self.player_id and (ex, ey) != (x, y):
                        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                            nx, ny = ex + dx, ey + dy
                            if game_state.board.is_within_bounds(nx, ny) and not game_state.board.is_occupied(nx, ny):
                                return True
            return False

        # Crisby Airsoft (59): Requiere enemigo adyacente
        elif unit_id == 59:
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                tx, ty = x + dx, y + dy
                if game_state.board.is_within_bounds(tx, ty):
                    target = game_state.board.get_unit_at(tx, ty)
                    if target and target.owner_id == enemy_id:
                        return True
            return False

        # Stefano (12) o Nico (25): Habilidades propias instantáneas
        elif unit_id in (12, 25):
            return True

        return False

    # --- GENERACIÓN DE ACCIONES LEGALES ---
    def _get_all_legal_actions(self, game_state) -> list:
        actions = []
        player = game_state.players[self.player_id]

        # 1. Cartas de la Mano
        for i, card in enumerate(player.hand):
            try:
                cost = int(card.cost)
            except Exception:
                cost = 0
                
            if player.current_energy < cost:
                continue

            card_type = card.card_type.lower()

            if card_type == 'unit':
                for x in range(game_state.board.width):
                    for y in range(game_state.board.height):
                        if not game_state.board.is_occupied(x, y) and game_state.validate_summon(self.player_id, x, y):
                            action = Action(ActionType.PLAY_CARD, self.player_id, {'card_index': i, 'to': (x, y)})
                            if game_state.validate_action(action):
                                actions.append(action)

            elif card_type in ('spell', 'trick'):
                if i in getattr(player, 'failed_spells_this_turn', set()):
                    continue
                
                spell_type = self._get_spell_type(card)

                for target_g in ['G', 'B']:
                    action = Action(ActionType.PLAY_SPELL, self.player_id, {'card_index': i, 'target': target_g})
                    if game_state.validate_action(action):
                        actions.append(action)

                for x in range(game_state.board.width):
                    for y in range(game_state.board.height):
                        unit = game_state.board.get_unit_at(x, y)
                        
                        if spell_type in ('DAMAGE', 'DEBUFF') and unit and unit.owner_id != self.player_id:
                            action = Action(ActionType.PLAY_SPELL, self.player_id, {'card_index': i, 'target': (x, y)})
                            if game_state.validate_action(action):
                                actions.append(action)

                        elif spell_type in ('HEAL', 'BUFF') and unit and unit.owner_id == self.player_id:
                            action = Action(ActionType.PLAY_SPELL, self.player_id, {'card_index': i, 'target': (x, y)})
                            if game_state.validate_action(action):
                                actions.append(action)
                        
                        elif spell_type == 'UTILITY' and unit:
                            action = Action(ActionType.PLAY_SPELL, self.player_id, {'card_index': i, 'target': (x, y)})
                            if game_state.validate_action(action):
                                actions.append(action)

            elif card_type in ('environment', 'building'):
                action = Action(ActionType.PLAY_CARD, self.player_id, {'card_index': i, 'to': (-1, -1)})
                if game_state.validate_action(action):
                    actions.append(action)

        # 2. Movimiento, Ataques y Habilidades en Tablero
        for x in range(game_state.board.width):
            for y in range(game_state.board.height):
                unit = game_state.board.get_unit_at(x, y)
                if unit and getattr(unit, 'owner_id', None) == self.player_id:
                    # Ataques
                    if not getattr(unit, 'has_attacked', False):
                        action_base = Action(ActionType.ATTACK, self.player_id, {'from': (x, y), 'target': 'B'})
                        if game_state.validate_action(action_base):
                            actions.append(action_base)

                        for tx in range(game_state.board.width):
                            for ty in range(game_state.board.height):
                                target = game_state.board.get_unit_at(tx, ty)
                                if target and target.owner_id != self.player_id:
                                    action_atk = Action(ActionType.ATTACK, self.player_id, {'from': (x, y), 'target': (tx, ty)})
                                    if game_state.validate_action(action_atk):
                                        actions.append(action_atk)

                    # Movimientos
                    if not getattr(unit, 'has_moved', False):
                        speed = getattr(unit, 'speed', 1)
                        for dx in range(-speed, speed + 1):
                            for dy in range(-speed, speed + 1):
                                if 0 < abs(dx) + abs(dy) <= speed:
                                    tx, ty = x + dx, y + dy
                                    if game_state.board.is_within_bounds(tx, ty):
                                        action_mv = Action(ActionType.MOVE, self.player_id, {'from': (x, y), 'to': (tx, ty)})
                                        if game_state.validate_action(action_mv):
                                            actions.append(action_mv)

                    # Habilidades Activas: Con pre-validación de objetivos
                    if not getattr(unit, 'ability_used_this_turn', False):
                        if self._can_unit_use_ability(unit, x, y, game_state):
                            action_act = Action(ActionType.ACTIVATE_ABILITY, self.player_id, {'from': (x, y)})
                            if game_state.validate_action(action_act):
                                actions.append(action_act)

        actions.append(Action(ActionType.END_TURN, self.player_id, {}))
        return actions

    def _get_medium_action(self, game_state, legal_actions) -> Action:
        # Invocaciones
        summons = [a for a in legal_actions if a.type == ActionType.PLAY_CARD]
        if summons:
            player = game_state.players[self.player_id]
            best_summon = None
            max_atk = -1
            for a in summons:
                card = player.hand[a.payload['card_index']]
                if card.card_type.lower() == 'unit' and getattr(card, 'attack', 0) > max_atk:
                    max_atk = getattr(card, 'attack', 0)
                    best_summon = a
            if best_summon:
                return best_summon

        # Hechizos
        spell_actions = [a for a in legal_actions if a.type == ActionType.PLAY_SPELL]
        if spell_actions:
            best_spell = max(spell_actions, key=lambda a: self._evaluate_spell_action(game_state, a))
            if self._evaluate_spell_action(game_state, best_spell) > 0:
                return best_spell

        # Habilidades Activas
        activations = [a for a in legal_actions if a.type == ActionType.ACTIVATE_ABILITY]
        if activations:
            return activations[0]

        # Entornos
        env_actions = [a for a in legal_actions if a.type == ActionType.PLAY_CARD and game_state.players[self.player_id].hand[a.payload['card_index']].card_type.lower() in ('environment', 'building')]
        if env_actions:
            return env_actions[0]

        # Movimientos
        moves = [a for a in legal_actions if a.type == ActionType.MOVE]
        if moves:
            best_move = None
            best_eval = float('inf') if self.player_id == 1 else -float('inf')
            for a in moves:
                tx, ty = a.payload['to']
                if self.player_id == 1:
                    if tx < best_eval:
                        best_eval = tx
                        best_move = a
                else:
                    if tx > best_eval:
                        best_eval = tx
                        best_move = a
            if best_move:
                return best_move

        # Ataques
        unit_attacks = [a for a in legal_actions if a.type == ActionType.ATTACK and a.payload['target'] != 'B']
        if unit_attacks:
            return unit_attacks[0]
        
        base_attacks = [a for a in legal_actions if a.type == ActionType.ATTACK and a.payload['target'] == 'B']
        if base_attacks:
            return base_attacks[0]

        return Action(ActionType.END_TURN, self.player_id, {})

    def _get_hard_action(self, game_state, legal_actions) -> Action:
        best_action = Action(ActionType.END_TURN, self.player_id, {})
        max_score = -float('inf')
        player = game_state.players[self.player_id]

        for action in legal_actions:
            score = 0.0

            if action.type == ActionType.END_TURN:
                score = 5.0

            elif action.type == ActionType.ATTACK:
                score = self._evaluate_attack_action(game_state, action)

            elif action.type == ActionType.PLAY_SPELL:
                score = self._evaluate_spell_action(game_state, action)

            elif action.type == ActionType.PLAY_CARD:
                idx = action.payload.get('card_index')
                if idx is not None and idx < len(player.hand):
                    card = player.hand[idx]
                    card_type = card.card_type.lower()

                    if card_type == 'unit':
                        base_score = 25.0 + (getattr(card, 'attack', 0) * 3) + (getattr(card, 'health', 0) * 2)
                        score = base_score
                    elif card_type in ('environment', 'building'):
                        score = 20.0

            elif action.type == ActionType.ACTIVATE_ABILITY:
                score = 45.0  # Alta prioridad si pasó la pre-validación

            elif action.type == ActionType.MOVE:
                fx, fy = action.payload['from']
                tx, ty = action.payload['to']
                progress = (fx - tx) if self.player_id == 1 else (tx - fx)
                score += progress * 8.0

            score += random.uniform(0.0, 0.5)

            if score > max_score:
                max_score = score
                best_action = action

        return best_action

    def _evaluate_spell_action(self, game_state, action) -> float:
        player = game_state.players[self.player_id]
        card = player.hand[action.payload['card_index']]
        spell_type = self._get_spell_type(card)
        target = action.payload.get('target')

        if target in ('G', 'B'):
            return 25.0

        if isinstance(target, tuple):
            unit = game_state.board.get_unit_at(*target)
            if not unit:
                return -50.0

            is_enemy = (unit.owner_id != self.player_id)

            if spell_type == 'DAMAGE':
                return 30.0 if is_enemy else -100.0
            elif spell_type == 'HEAL':
                return 25.0 if not is_enemy else -100.0
            elif spell_type == 'BUFF':
                return 25.0 if not is_enemy else -100.0
            elif spell_type == 'DEBUFF':
                return 25.0 if is_enemy else -100.0

        return 0.0

    def _evaluate_attack_action(self, game_state, action) -> float:
        target = action.payload['target']
        if target == 'B':
            return 60.0

        fx, fy = action.payload['from']
        tx, ty = action.payload['target']
        attacker = game_state.board.get_unit_at(fx, fy)
        defender = game_state.board.get_unit_at(tx, ty)

        if not attacker or not defender:
            return 0.0

        score = 20.0
        if defender.health <= attacker.attack:
            score += 40.0

        return score