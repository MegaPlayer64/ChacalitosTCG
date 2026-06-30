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

    def update_policy(self, result: str):
        """
        Stub para futura implementación de Reinforcement Learning.
        Recibe 'WIN' o 'LOSS' al final de la partida para ajustar pesos.
        """
        pass

    def _log_and_return_action(self, action: Action, game_state) -> Action:
        if action.type != ActionType.END_TURN:
            if action.type == ActionType.PLAY_CARD:
                card_index = action.payload['card_index']
                card = game_state.players[self.player_id].hand[card_index]
                self.turn_cards_played += 1
                try:
                    cost = int(card.cost)
                except:
                    cost = 0
                self.turn_energy_spent += cost
                detalle = f"Carta '{getattr(card, 'name', 'Desconocida')}' (Coste: {cost})"
            elif action.type == ActionType.PLAY_SPELL:
                card_index = action.payload['card_index']
                card = game_state.players[self.player_id].hand[card_index]
                self.turn_cards_played += 1
                try:
                    cost = int(card.cost)
                except:
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
            self.turn_energy_spent = 0
            self.turn_cards_played = 0

        return action

    def get_action(self, game_state) -> Action:
        time.sleep(self.delay)
        # print(f">> [IA {self.difficulty}] Analizando el campo...")

        try:
            legal_actions = self._get_all_legal_actions(game_state)
            
            if not legal_actions:
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

    def _get_all_legal_actions(self, game_state) -> list:
        actions = []
        player = game_state.players[self.player_id]

        # 1. Cartas (Unidades, etc)
        for i, card in enumerate(player.hand):
            try:
                cost = int(card.cost)
            except:
                cost = 0
                
            if cost > 0 and player.current_energy <= 0:
                continue
                
            if player.current_energy >= cost:
                card_type = card.card_type.lower()
                if card_type == 'unit':
                    for x in range(game_state.board.width):
                        for y in range(game_state.board.height):
                            try:
                                if not game_state.board.is_occupied(x, y) and game_state.validate_summon(self.player_id, x, y):
                                    action = Action(ActionType.PLAY_CARD, self.player_id, {'card_index': i, 'to': (x, y)})
                                    if game_state.validate_action(action):
                                        actions.append(action)
                            except Exception:
                                pass
                elif card_type in ('spell', 'trick'):
                    # Saltar si este hechizo ya falló este turno
                    if i in player.failed_spells_this_turn:
                        continue
                    
                    # Intentar objetivo global
                    try:
                        action = Action(ActionType.PLAY_SPELL, self.player_id, {'card_index': i, 'target': 'G'})
                        if game_state.validate_action(action):
                            actions.append(action)
                    except Exception:
                        pass

                    # Intentar objetivos sobre el tablero
                    for x in range(game_state.board.width):
                        for y in range(game_state.board.height):
                            try:
                                action = Action(ActionType.PLAY_SPELL, self.player_id, {'card_index': i, 'target': (x, y)})
                                if game_state.validate_action(action):
                                    actions.append(action)
                            except Exception:
                                pass
                elif card_type in ('environment', 'building'):
                    try:
                        action = Action(ActionType.PLAY_CARD, self.player_id, {'card_index': i, 'to': (-1, -1)})
                        if game_state.validate_action(action):
                            actions.append(action)
                    except Exception:
                        pass
                else:
                    try:
                        action = Action(ActionType.PLAY_CARD, self.player_id, {'card_index': i})
                        if game_state.validate_action(action):
                            actions.append(action)
                    except Exception:
                        pass

        # 2. Movimiento y Ataque
        for x in range(game_state.board.width):
            for y in range(game_state.board.height):
                unit = game_state.board.get_unit_at(x, y)
                if unit and getattr(unit, 'owner_id', None) == self.player_id:
                    # Ataques
                    if not getattr(unit, 'has_attacked', False):
                        # Ataque Base
                        try:
                            action = Action(ActionType.ATTACK, self.player_id, {'from': (x, y), 'target': 'B'})
                            if game_state.validate_action(action):
                                actions.append(action)
                        except Exception:
                            pass
                            
                        # Ataque Unidades
                        for tx in range(game_state.board.width):
                            for ty in range(game_state.board.height):
                                try:
                                    target = game_state.board.get_unit_at(tx, ty)
                                    if target and getattr(target, 'owner_id', None) != self.player_id:
                                        action = Action(ActionType.ATTACK, self.player_id, {'from': (x, y), 'target': (tx, ty)})
                                        if game_state.validate_action(action):
                                            actions.append(action)
                                except Exception:
                                    pass

                    # Movimientos
                    if not getattr(unit, 'has_moved', False):
                        speed = getattr(unit, 'speed', 1)
                        for dx in range(-speed, speed + 1):
                            for dy in range(-speed, speed + 1):
                                if abs(dx) + abs(dy) <= speed:
                                    tx, ty = x + dx, y + dy
                                    try:
                                        if game_state.board.is_within_bounds(tx, ty):
                                            action = Action(ActionType.MOVE, self.player_id, {'from': (x, y), 'to': (tx, ty)})
                                            if game_state.validate_action(action):
                                                actions.append(action)
                                    except Exception:
                                        pass

        actions.append(Action(ActionType.END_TURN, self.player_id, {}))
        return actions

    def _is_enemy_unit_target(self, game_state, target):
        if isinstance(target, tuple):
            unit = game_state.board.get_unit_at(*target)
            return unit and getattr(unit, 'owner_id', None) != self.player_id
        return False

    def _is_friendly_unit_target(self, game_state, target):
        if isinstance(target, tuple):
            unit = game_state.board.get_unit_at(*target)
            return unit and getattr(unit, 'owner_id', None) == self.player_id
        return False

    def _evaluate_spell_action(self, game_state, action) -> float:
        player = game_state.players[self.player_id]
        card = player.hand[action.payload['card_index']]
        score = 0

        target = action.payload.get('target')
        if target == 'G':
            score += 20
        elif target == 'B':
            score += 35
        elif isinstance(target, tuple):
            if self._is_enemy_unit_target(game_state, target):
                target_unit = game_state.board.get_unit_at(*target)
                if target_unit:
                    score += 30
                    score += max(0, 10 - target_unit.health)
            elif self._is_friendly_unit_target(game_state, target):
                score += 15
            else:
                score += 5

        # Los hechizos de coste mayor son más valiosos si pueden usarse
        try:
            score += int(card.cost) * 2
        except Exception:
            pass

        return score

    def _evaluate_environment_action(self, game_state, action) -> float:
        score = 15
        if getattr(game_state, 'active_environment', None) is None:
            score += 15
        else:
            score += 5
        return score

    def _get_medium_action(self, game_state, legal_actions) -> Action:

        # 1. Fase de Invocación (Mayor Ataque)
        summons = [a for a in legal_actions if a.type == ActionType.PLAY_CARD]
        if summons:
            player = game_state.players[self.player_id]
            best_summon = None
            max_atk = -1
            for a in summons:
                card = player.hand[a.payload['card_index']]
                if card.card_type.lower() == 'unit' and card.attack > max_atk:
                    max_atk = card.attack
                    best_summon = a
            if best_summon:
                return best_summon


        # 2. Fase de Hechizo/Entorno
        spell_actions = [a for a in legal_actions if a.type == ActionType.PLAY_SPELL]
        if spell_actions:
            best_spell = max(spell_actions, key=lambda a: self._evaluate_spell_action(game_state, a))
            if self._evaluate_spell_action(game_state, best_spell) > 0:
                return best_spell

        env_actions = [a for a in legal_actions if a.type == ActionType.PLAY_CARD and game_state.players[self.player_id].hand[a.payload['card_index']].card_type.lower() in ('environment', 'building')]
        if env_actions:
            best_env = max(env_actions, key=lambda a: self._evaluate_environment_action(game_state, a))
            if self._evaluate_environment_action(game_state, best_env) > 10:
                return best_env


        # 3. Fase de Movimiento (Hacia la Base Enemiga)
        moves = [a for a in legal_actions if a.type == ActionType.MOVE]
        if moves:
            best_move = None
            best_eval = float('inf') if self.player_id == 1 else -float('inf')
            
            for a in moves:
                tx, ty = a.payload['to']
                if self.player_id == 1:
                    # Mover hacia izquierda (x menor)
                    if tx < best_eval:
                        best_eval = tx
                        best_move = a
                else:
                    # Mover hacia derecha (x mayor)
                    if tx > best_eval:
                        best_eval = tx
                        best_move = a
            if best_move:
                return best_move

        # 4. Fase de Ataque (Unidad con menor vida)
        unit_attacks = [a for a in legal_actions if a.type == ActionType.ATTACK and a.payload['target'] != 'B']
        if unit_attacks:
            best_attack = None
            lowest_hp = float('inf')
            for a in unit_attacks:
                tx, ty = a.payload['target']
                target = game_state.board.get_unit_at(tx, ty)
                if target and target.health < lowest_hp:
                    lowest_hp = target.health
                    best_attack = a
            if best_attack:
                return best_attack
        
        # 5. Prioridad Absoluta: Ataque a Base
        base_attacks = [a for a in legal_actions if a.type == ActionType.ATTACK and a.payload['target'] == 'B']
        if base_attacks:
            return base_attacks[0]

        return Action(ActionType.END_TURN, self.player_id, {})

    def _get_groups_lower(self, card):
        groups = getattr(card, 'groups', [])
        if not groups:
            return []
        if isinstance(groups, str):
            return [g.strip().lower() for g in groups.replace('\n', ',').split(',')]
        elif isinstance(groups, list):
            return [g.lower() for g in groups if g and len(str(g).strip()) > 0]
        return []

    def _calculate_synergy_score(self, card, game_state) -> int:
        card_tags = set(self._get_groups_lower(card))
        if not card_tags or card_tags == {''}:
            return 0
            
        score = 0
        for x in range(game_state.board.width):
            for y in range(game_state.board.height):
                unit = game_state.board.get_unit_at(x, y)
                if unit and getattr(unit, 'owner_id', None) == self.player_id:
                    unit_tags = set(self._get_groups_lower(unit))
                    intersection = card_tags.intersection(unit_tags)
                    score += len(intersection) * 20 # +20 por Sinergia (como pedido)
        return score

    def _calculate_lethal_risk(self, game_state, unit, target_x, target_y, ignored_enemy_pos=None) -> bool:
        for x in range(game_state.board.width):
            for y in range(game_state.board.height):
                if ignored_enemy_pos and (x, y) == ignored_enemy_pos:
                    continue
                enemy = game_state.board.get_unit_at(x, y)
                if enemy and getattr(enemy, 'owner_id', None) != self.player_id:
                    dist = max(abs(x - target_x), abs(y - target_y))
                    if dist <= getattr(enemy, 'range_atk', 1):
                        if getattr(enemy, 'attack', 0) >= unit.health:
                            return True
        return False

    def _get_hard_action(self, game_state, legal_actions) -> Action:
        best_action = Action(ActionType.END_TURN, self.player_id, {})
        max_score = -float('inf')

        player = game_state.players[self.player_id]
        
        for action in legal_actions:
            score = 0

            if action.type in [ActionType.PLAY_CARD, ActionType.PLAY_SPELL]:
                idx = action.payload.get('card_index')
                if idx is None or idx >= len(player.hand):
                    continue
            
            if action.type == ActionType.END_TURN:
                score = 0 

            elif action.type == ActionType.ATTACK:
                if action.payload['target'] == 'B':
                    score += 50
                else:
                    tx, ty = action.payload['target']
                    target = game_state.board.get_unit_at(tx, ty)
                    fx, fy = action.payload['from']
                    attacker = game_state.board.get_unit_at(fx, fy)
                    
                    ignored = None
                    if target and attacker:
                        if target.health <= attacker.attack:
                            score += 30 # Destruir Unidad Enemiga
                            ignored = (tx, ty)
                        else:
                            score += 10 # Daño normal
                    
                    # Conservación 'Excelencia'
                    if attacker and 'excelencia' in self._get_groups_lower(attacker):
                        if self._calculate_lethal_risk(game_state, attacker, fx, fy, ignored_enemy_pos=ignored):
                            score -= 100

            elif action.type == ActionType.PLAY_SPELL:
                card = player.hand[action.payload['card_index']]
                score += self._evaluate_spell_action(game_state, action)

                target = action.payload.get('target')
                if isinstance(target, tuple):
                    if self._is_enemy_unit_target(game_state, target):
                        target_unit = game_state.board.get_unit_at(*target)
                        if target_unit and target_unit.health <= 5:
                            score += 15
                    elif self._is_friendly_unit_target(game_state, target):
                        score += 10

            elif action.type == ActionType.PLAY_CARD:
                card = player.hand[action.payload['card_index']]
                if card.card_type.lower() == 'unit':
                    base_score = 20 + int(getattr(card, 'attack', 0)) * 3 + int(getattr(card, 'health', 0)) * 2
                    synergy = self._calculate_synergy_score(card, game_state)
                    score += base_score + synergy
                        
                    tx, ty = action.payload['to']
                    if 'excelencia' in self._get_groups_lower(card):
                        if self._calculate_lethal_risk(game_state, card, tx, ty):
                            score -= 100
                elif card.card_type.lower() in ('environment', 'building'):
                    score += self._evaluate_environment_action(game_state, action)

            elif action.type == ActionType.MOVE:
                fx, fy = action.payload['from']
                tx, ty = action.payload['to']
                unit = game_state.board.get_unit_at(fx, fy)
                
                # Bonus por acercarse a base
                if self.player_id == 1:
                    score += (fx - tx) * 5 
                else:
                    score += (tx - fx) * 5 
                    
                if unit and 'excelencia' in self._get_groups_lower(unit):
                    if self._calculate_lethal_risk(game_state, unit, tx, ty):
                        score -= 100

            # Añadir un pequeñisimo factor de aleatoriedad para desempatar acciones iguales
            score += random.uniform(0, 0.1)

            if score > max_score:
                max_score = score
                best_action = action

        return best_action
