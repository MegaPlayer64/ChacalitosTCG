# src/domain/game_state.py
from typing import List
# Imports directos ya que están en la misma carpeta domain/
from src.domain.player import Player
from src.domain.action import Action
from src.domain.action_type import ActionType
from src.domain.board import Board
from src.infrastructure.loaders.card_loader import CardLoader

class GameState:
    def __init__(self, players: List[Player], deck1, deck2):
        self.players = players
        self.board = Board(width=6, height=5) # El tablero se inicia limpio (vacío)
        self.current_player_id = 0
        self.turn_number = 1
        self.game_over = False
        self.active_environment = None
        self.pending_ability = None

        # --- Inicialización de la Partida ---
        for p in self.players:
            # Verificar vida inicial en 80 HP
            p.health = 80
            p.max_energy = getattr(p, 'max_energy', 1)
            p.current_energy = getattr(p, 'current_energy', 1)
            
            # Cargar mazos
            if p == self.players[0]:
                p.deck = CardLoader.load_deck(deck1)
            elif p == self.players[1]:
                p.deck = CardLoader.load_deck(deck2)
            
            # Mezclar mazo
            p.shuffle_deck()
            
            # Robar 4 cartas (Mano Inicial)
            p.hand = [] # Limpiar por si acaso
            for _ in range(4):
                if p.deck and len(p.hand) < 10:
                    p.hand.append(p.deck.pop(0))

    def get_current_player(self) -> Player:
        return self.players[self.current_player_id]

    def get_effective_stats(self, unit) -> dict:
        """Calcula el ataque y velocidad efectivos basándose en las habilidades estáticas de los aliados."""
        effective_attack = unit.attack
        effective_speed = unit.speed
        
        unit_tags = []
        if getattr(unit, 'groups', None):
            if isinstance(unit.groups, str):
                unit_tags = [g.strip().lower() for g in unit.groups.split(',') if g.strip()]
            elif isinstance(unit.groups, list):
                unit_tags = [g.lower() for g in unit.groups if g]
            
        board_ally_tags = set()
        for y in range(self.board.height):
            for x in range(self.board.width):
                ally = self.board.get_unit_at(x, y)
                if ally and getattr(ally, 'owner_id', None) == getattr(unit, 'owner_id', None):
                    if getattr(ally, 'groups', None):
                        if isinstance(ally.groups, str):
                            board_ally_tags.update([g.strip().lower() for g in ally.groups.split(',') if g.strip()])
                        elif isinstance(ally.groups, list):
                            board_ally_tags.update([g.lower() for g in ally.groups if g])

        for y in range(self.board.height):
            for x in range(self.board.width):
                ally = self.board.get_unit_at(x, y)
                if ally and getattr(ally, 'owner_id', None) == getattr(unit, 'owner_id', None):
                    static_abilities = getattr(ally, 'static_abilities', [])
                    for ability in static_abilities:
                        if ability['type'] == 'buff_all_attack':
                            effective_attack += ability['amount']
                        elif ability['type'] == 'buff_tag_attack':
                            if ability['tag'] in unit_tags:
                                effective_attack += ability['amount']
                        elif ability['type'] == 'buff_tag_speed_if_tag_present':
                            if ability['target_tag'] in unit_tags and ability['condition_tag'] in board_ally_tags:
                                effective_speed += ability['amount']

        # Procesar buffs temporales (Hechizos)
        if hasattr(unit, 'temporary_buffs'):
            for buff in unit.temporary_buffs:
                if buff.get('delay', 0) > 0:
                    continue
                if buff['type'] == 'attack':
                    effective_attack += buff['amount']
                elif buff['type'] == 'speed':
                    effective_speed += buff['amount']
                elif buff['type'] == 'speed_set':
                    effective_speed = buff['value']
                elif buff['type'] == 'attack_set':
                    effective_attack = buff['value']

        # Efectos estáticos de Entorno Activo
        if getattr(self, 'active_environment', None):
            env_id = int(self.active_environment.card.id)
            if env_id == 53: # Cancha de Futbol
                if 'futbolero' in unit_tags and not getattr(unit, 'has_attacked', False):
                    effective_speed += 1
                elif unit.id == 22:
                    effective_speed += 1
            elif env_id == 54: # La Fundación
                if 'tralalero tralala' in unit_tags or unit.id == 22:
                    effective_attack -= 1
                
                # Los enemigos no pueden recibir buffs de ataque
                if getattr(unit, 'owner_id', None) is not None and unit.owner_id != self.active_environment.owner_id:
                    # Limitar el ataque máximo a su ataque base si es mayor
                    if effective_attack > unit.attack:
                        effective_attack = unit.attack

        # Evitar valores negativos
        effective_attack = max(0, effective_attack)
        effective_speed = max(0, effective_speed)

        return {"attack": effective_attack, "speed": effective_speed}

    def validate_summon(self, player_id, x, y):
        if not self.board.is_within_bounds(x, y):
            return False
        if int(player_id) == 0:
            return x < 2
        elif int(player_id) == 1:
            return x > 3
        return False

    def validate_action(self, action: Action) -> bool:
        if self.game_over: return False
        if int(action.player_id) != int(self.current_player_id): return False

        if getattr(self, 'pending_ability', None):
            if action.type.name not in ("RESOLVE_ABILITY", "CANCEL_ABILITY"):
                print(">> [!] Tienes una habilidad pendiente. Selecciona el objetivo o cancela.")
                return False

        if action.type.name in ("END_TURN", "CANCEL_ABILITY", "RESOLVE_ABILITY"):
            return True

        if action.type.name == "PLAY_CARD":
            card_index = action.payload.get('card_index')
            tx, ty = action.payload.get('to', (-1, -1))
            
            player = self.get_current_player()
            if not (0 <= card_index < len(player.hand)):
                print(">> [!] Índice de carta inválido.")
                return False
                
            card = player.hand[card_index]

            # Forzamos que solo busque el descuento de Crisby si la tropa es 4 o menos, si no, deje la carta sin descuento
            crisby_active = getattr(player, 'crisby_cost_reduction_active', False)

            if crisby_active and card.cost <= 4:
                final_cost = max(1, int(card.cost) - 1)
            else:
                final_cost = int(card.cost)

            if player.current_energy < final_cost:
                print(f">> [!] Energía insuficiente. Necesitas {card.cost}, tienes {player.current_energy}.")
                return False
                
            if card.card_type.lower() == 'unit':
                if self.board.is_occupied(tx, ty):
                    print(f">> [!] La casilla ({tx}, {ty}) ya está ocupada.")
                    return False
                if not self.validate_summon(action.player_id, tx, ty):
                    print(f">> [!] Zona de invocación inválida para el jugador {action.player_id}.")
                    return False
            
            if final_cost <= 4:
                player.crisby_cost_reduction_active = False
            return True

        if action.type.name == "PLAY_SPELL":
            card_index = action.payload.get('card_index')
            target = action.payload.get('target')
            
            player = self.get_current_player()
            if not (0 <= card_index < len(player.hand)):
                print(">> [!] Índice de carta inválido.")
                return False
                
            card = player.hand[card_index]
            
            # Busca primero los descuentos activos, posteriormente aplica el descuento de Crisby y luego el descuento de Dante Economista, aplicando la propiedad de coste 4 o menor de Crisby y solo para trucos de Dante Economista
            crisby_active = getattr(player, 'crisby_cost_reduction_active', False)
            d_economia_active = getattr(player, 'd_economia_cost_reduction_active', False)
            
            final_cost = int(card.cost)

            if crisby_active and card.cost <= 4: 
                final_cost = max(1, int(final_cost) - 1)

            if d_economia_active:
                final_cost = max(1, int(final_cost) - 1)
                
            if player.current_energy < final_cost:
                print(f">> [!] Energía insuficiente. Necesitas {card.cost}, tienes {player.current_energy}.")
                return False
            
            if target != 'G' and isinstance(target, tuple):
                tx, ty = target
                if not self.board.is_within_bounds(tx, ty):
                    print(">> [!] Objetivo fuera del tablero.")
                    return False

            if final_cost <= 4:
                player.crisby_cost_reduction_active = False
            player.d_economia_cost_reduction_active = False

            return True

        if action.type.name == "MOVE":
            fx, fy = action.payload['from']
            tx, ty = action.payload['to']

            # 1. ¿Está dentro del mapa (0-4)?
            if not self.board.is_within_bounds(tx, ty):
                print(f">> [!] Fuera del tablero: ({tx}, {ty})")
                return False

            # 2. ¿Hay alguien en el origen?
            unit = self.board.get_unit_at(fx, fy)
            if not unit:
                print(f">> [!] No hay unidad en ({fx}, {fy})")
                return False

            # 3. ¿La unidad ya se movió este turno?
            if getattr(unit, 'has_moved', False):
                print(f">> [!] {unit.name} ya se movió en este turno.")
                return False

            # 4. ¿La casilla de destino está ocupada?
            if self.board.is_occupied(tx, ty):
                print(f">> [!] Casilla ({tx}, {ty}) ya está ocupada.")
                return False

            # 5. ¿Tiene suficiente velocidad (Manhattan Distance)?
            dist = abs(fx - tx) + abs(fy - ty)
            effective_speed = self.get_effective_stats(unit)["speed"]
            if dist > effective_speed:
                print(f">> [!] {unit.name} no llega. Distancia: {dist}, Velocidad: {effective_speed}")
                return False

            if unit.id == 25 and getattr(unit, 'immobile_turns', 0) > 0:
                return False 

            return True
        elif action.type.name == "END_TURN":
            self._end_turn()
            return True
        
        if action.type.name == "ATTACK":
            fx, fy = action.payload['from']
            attacker = self.board.get_unit_at(fx, fy)
            
            if action.payload['target'] == 'B':
                tx = 'B'
                ty = None
                target = None
            else:
                tx, ty = action.payload['target']
                target = self.board.get_unit_at(tx, ty)

            # 1. ¿Existe el atacante?
            if not attacker:
                print(">> [!] Atacante inexistente.")
                return False

            if getattr(attacker, 'card_type', '') != 'unit' or not hasattr(attacker, 'health'):
                print(f">> [!] {attacker.name} no es una unidad que pueda atacar.")
                return False

            if attacker.owner_id != action.player_id:
                print(">> [!] No puedes ordenar atacar a una unidad que no es tuya.")
                return False

            # 3. ¿Ya atacó?
            if getattr(attacker, 'has_attacked', False):
                print(f">> [!] {attacker.name} ya agotó su ataque este turno.")
                return False

            if tx == 'B':
                # Ataque a la base enemiga
                if action.player_id == 0:
                    if fx not in [4, 5]:
                        print(">> [!] Debes estar en la columna 4 o 5 para atacar la Base Enemiga.")
                        return False
                    dist = max(abs(fx - 6), 0)
                    if dist > attacker.range_atk:
                        print(f">> [!] La base está fuera de rango. Rango: {attacker.range_atk}")
                        return False
                elif action.player_id == 1:
                    if fx not in [0, 1]:
                        print(">> [!] Debes estar en la columna 0 o 1 para atacar la Base Enemiga.")
                        return False
                    dist = max(abs(fx - (-1)), 0)
                    if dist > attacker.range_atk:
                        print(f">> [!] La base está fuera de rango. Rango: {attacker.range_atk}")
                        return False
                return True

            target = self.board.get_unit_at(tx, ty)
            if not target:
                print(">> [!] Blanco inexistente.")
                return False

            if getattr(target, 'card_type', '') != 'unit' or not hasattr(target, 'health'):
                print(f">> [!] {target.name} no puede ser objetivo de ataques.")
                return False

            if target.owner_id == action.player_id:
                print(">> [!] ¡Fuego amigo! No puedes atacar a tus aliados.")
                return False

            # 4. ¿Está en rango (Manhattan)?
            dist = abs(fx - tx) + abs(fy - ty)
            if dist > attacker.range_atk:
                print(f">> [!] Objetivo fuera de rango. Distancia: {dist}, Rango: {attacker.range_atk}")
                return False

            # ID 32: Isidora (Inmune si tiene aliados adyacentes)
            if target.id == 59:
                if any(self.board.get_unit_at(nx, ny) for nx, ny in self.board.get_neighbors(tx, ty)):
                    return False 

            if dist > 1 and "Danza" in target.groups:
                # Buscar si Ale está adyacente al defensor
                for nx, ny in self.board.get_neighbors(tx, ty):
                    vecino = self.board.get_unit_at(nx, ny)
                    if vecino and vecino.id == 11:
                        return False 
            return True
        
        return False
    
    def apply_action(self, action: Action) -> bool:
        if not self.validate_action(action):
            return False

        if action.type.name == "CANCEL_ABILITY":
            self.pending_ability = None
            print(">> [!] Habilidad cancelada.")
            return True
            
        if action.type.name == "RESOLVE_ABILITY":
            from src.domain.ability_manager import AbilityManager
            result = AbilityManager.resolve_pending_ability(self, action.payload)
            if result:
                self.pending_ability = None
            return result

        if action.type.name == "PLAY_CARD":
            card_index = action.payload['card_index']
            tx, ty = action.payload.get('to', (-1, -1))
            
            player = self.get_current_player()
            card = player.hand.pop(card_index)
            player.current_energy -= int(card.cost)
            
            if card.card_type.lower() == 'unit':
                card.owner_id = int(player.id)
                self.board.set_unit_at(tx, ty, card)
                print(f">> ¡{player.name} invocó a {card.name} en ({tx}, {ty})!")
                
                # Efecto pasivo 52 (Zona de Juegos)
                if getattr(self, 'active_environment', None) and int(self.active_environment.card.id) == 52:
                    if 'fuerzas especiales valenzuela' in str(getattr(card, 'groups', '')).lower():
                        card.max_health += 2
                        card.health += 2
                        print(f">> [Zona de Juegos] ¡{card.name} obtiene +2 de Vida Máxima al invocarse! (Vida actual: {card.health})")
                        
            elif card.card_type.lower() in ('environment', 'building'):
                from domain.environment import Environment
                self.active_environment = Environment(card, player.id)
                print(f">> ¡El entorno ha cambiado a {card.name}!")
            else:
                print(f">> ¡{player.name} jugó la carta {card.name}!")
        
        if action.type.name == "PLAY_SPELL":
            # 1. Recuperar índices y datos
            card_index = action.payload['card_index']
            target = action.payload.get('target') 
            player = self.get_current_player()
            
            # 2. VALIDACIÓN (Para evitar que la IA juegue cartas que no tiene)
            if card_index < 0 or card_index >= len(player.hand):
                print(f">> [!] ERROR: Índice de carta inválido: {card_index}")
                return False

            # 3. Consumir carta y energía
            card = player.hand.pop(card_index)
            player.current_energy -= int(card.cost)
            print(f">> ¡{player.name} lanzó el hechizo {card.name}!")

            # 4. EJECUTAR EL EFECTO (Aquí estaba el hueco)
            from src.domain.ability_manager import AbilityManager
            success = AbilityManager.execute_spell(card, target, self)
            
            if success:
                print(f">> [Hechizo]: Efecto de {card.name} aplicado.")
            else:
                print(f">> [!] El hechizo {card.name} falló.")
            
            return True

        if action.type.name == "MOVE":
            fx, fy = action.payload['from']
            tx, ty = action.payload['to']
            
            # Realizamos el movimiento en el tablero
            unit = self.board.get_unit_at(fx, fy)
            self.board.move_unit(fx, fy, tx, ty)
            
            # Marcamos la unidad como "ya movida"
            unit.has_moved = True
            print(f">> {unit.name} se movió a ({tx}, {ty})")

        elif action.type.name == "ATTACK":
            fx, fy = action.payload['from']
            attacker = self.board.get_unit_at(fx, fy)
            attacker.has_attacked = True
            
            effective_attack = self.get_effective_stats(attacker)["attack"]
            
            if action.payload['target'] == 'B':
                tx = 'B'
                ty = None
            else:
                tx, ty = action.payload['target']
            
            if tx == 'B':
                enemy_id = 1 - action.player_id
                enemy = self.players[enemy_id]
                enemy.health -= effective_attack
                print(f">>> ¡{attacker.name} ataca la Base Enemiga y causa {effective_attack} de daño! (Vida enemiga: {enemy.health}) <<<")
            else:
                target = self.board.get_unit_at(tx, ty)
                # Aplicar daño
                murió = target.take_damage(effective_attack, self)
                if murió:
                    print(f">>> ¡{target.name} ha sido derrotado! <<<")
                    self.board.remove_unit(tx, ty)
                    
                    # Chequeo de buff "draw_on_kill"
                    if hasattr(attacker, 'temporary_buffs'):
                        for buff in attacker.temporary_buffs:
                            if buff.get('type') == 'draw_on_kill':
                                player = self.players[attacker.owner_id]
                                if player.deck and len(player.hand) < 10:
                                    drawn_card = player.deck.pop(0)
                                    player.hand.append(drawn_card)
                                    print(f">>> ¡Habilidad activada! Robaste: {drawn_card.name}")
                                break
            attacker.on_attack(self)
        
        elif action.type.name == "ACTIVATE_ABILITY":
            fx, fy = action.payload['from']
            unit = self.board.get_unit_at(fx, fy)
            unit.on_activate(self)

        elif action.type.name == "END_TURN":
            self._end_turn()
            
        # Check Win Condition after any action
        for p in self.players:
            if p.health <= 0:
                self.game_over = True
                winner = self.players[1 - p.id]
                print("\n" + "="*40)
                print(f" ¡VICTORIA PARA {winner.name.upper()}! ")
                print(f" La base de {p.name} ha sido destruida.")
                print("="*40 + "\n")
                break
                
        return True
    
    def _start_turn(self):
        current_player = self.get_current_player()
        
        # Robar carta al inicio del turno
        if current_player.deck and len(current_player.hand) < 10:
            drawn_card = current_player.deck.pop(0)
            current_player.hand.append(drawn_card)
            print(f">> {current_player.name} ha robado: {drawn_card.name}")
            
        # Llamar trigger_on_turn_start de AbilityManager
        try:
            from src.domain.ability_manager import AbilityManager
            for unit in self.board.get_all_units(self.current_player_id):
                AbilityManager.trigger_on_turn_start(unit, self)
        except ImportError:
            pass
        
    def _end_turn(self):
        # 1. Resetear el estado de todas las unidades antes de cambiar de jugador
        for y in range(self.board.height):
            for x in range(self.board.width):
                unit = self.board.get_unit_at(x, y)
                if unit:
                    unit.has_moved = False
                    unit.has_attacked = False
                    unit.ability_used_this_turn = False
                    
                    # 1.5. Decrementar duración de buffs temporales si la unidad pertenece al jugador que termina su turno
                    if unit.owner_id == self.current_player_id and hasattr(unit, 'temporary_buffs'):
                        buffs_to_keep = []
                        for buff in unit.temporary_buffs:
                            if buff.get('delay', 0) > 0:
                                buff['delay'] -= 1
                                buffs_to_keep.append(buff)
                            else:
                                buff['duration'] -= 1
                                if buff['duration'] > 0:
                                    buffs_to_keep.append(buff)
                        unit.temporary_buffs = buffs_to_keep

        # Decrementar penalización de curación
        current_p = self.get_current_player()
        if hasattr(current_p, 'cant_heal_turns') and current_p.cant_heal_turns > 0:
            current_p.cant_heal_turns -= 1

        for unit in self.board.get_all_units(current_p.id):
            if hasattr(unit, 'immobile_turns') and unit.immobile_turns > 0:
                unit.immobile_turns -= 1
        
        current_p.crisby_cost_reduction_active = False
        current_p.d_economia_cost_reduction_active = False
        
        # 2. Cambiar de jugador
        self.current_player_id = 1 - self.current_player_id
        if self.current_player_id == 0:
            self.turn_number += 1
        
        next_player = self.get_current_player()
        next_player.failed_spells_this_turn.clear()
            
        next_player.refresh_energy()
        print(f"\n--- Turno finalizado. Ahora es el turno de {next_player.name} ---")
        self._start_turn()

# Actualiza Git