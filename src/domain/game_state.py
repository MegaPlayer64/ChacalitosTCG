# src/domain/game_state.py
from typing import List
# Imports directos ya que están en la misma carpeta domain/
from src.domain.player import Player
from src.domain.action import Action
from src.domain.action_type import ActionType
from src.domain.board import Board
from src.infrastructure.loaders.card_loader import CardLoader

class GameState:
    def __init__(self, players: List[Player]):
        self.players = players
        self.board = Board(width=6, height=5) # El tablero se inicia limpio (vacío)
        self.current_player_id = 0
        self.turn_number = 1
        self.game_over = False
        self.active_environment = None

        # --- Inicialización de la Partida ---
        for p in self.players:
            # Verificar vida inicial en 80 HP
            p.health = 80
            
            # Cargar mazos
            if p == self.players[0]:
                p.deck = CardLoader.load_deck("src/data/ct_basic_deck.json")
            elif p == self.players[1]:
                p.deck = CardLoader.load_deck("src/data/fev_basic_deck.json")
            
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

        if action.type.name == "END_TURN":
            return True

        if action.type.name == "PLAY_CARD":
            card_index = action.payload.get('card_index')
            tx, ty = action.payload.get('to', (-1, -1))
            
            player = self.get_current_player()
            if not (0 <= card_index < len(player.hand)):
                print(">> [!] Índice de carta inválido.")
                return False
                
            card = player.hand[card_index]
            
            if player.current_energy < int(card.cost):
                print(f">> [!] Energía insuficiente. Necesitas {card.cost}, tienes {player.current_energy}.")
                return False
                
            if card.card_type.lower() == 'unit':
                if self.board.is_occupied(tx, ty):
                    print(f">> [!] La casilla ({tx}, {ty}) ya está ocupada.")
                    return False
                if not self.validate_summon(action.player_id, tx, ty):
                    print(f">> [!] Zona de invocación inválida para el jugador {action.player_id}.")
                    return False
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

            # 4. ¿Está en rango (Chebyshev - Maxima diferencia)?
            dist = max(abs(fx - tx), abs(fy - ty))
            if dist > attacker.range_atk:
                print(f">> [!] Objetivo fuera de rango. Distancia: {dist}, Rango: {attacker.range_atk}")
                return False

            return True
        
        return False
    
    def apply_action(self, action: Action) -> bool:
        if not self.validate_action(action):
            return False

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
            else:
                print(f">> ¡{player.name} jugó la carta {card.name}!")
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
                attacker.on_attack(self)
                if murió:
                    print(f">>> ¡{target.name} ha sido derrotado! <<<")
                    self.board.remove_unit(tx, ty)
            
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
    


    def _end_turn(self):
        # 1. Resetear el estado de todas las unidades antes de cambiar de jugador
        for y in range(self.board.height):
            for x in range(self.board.width):
                unit = self.board.get_unit_at(x, y)
                if unit:
                    unit.has_moved = False
                    unit.has_attacked = False
                    unit.ability_used_this_turn = False

        # 2. Cambiar de jugador
        self.current_player_id = 1 - self.current_player_id
        if self.current_player_id == 0:
            self.turn_number += 1
            
        self.get_current_player().refresh_energy()
        print(f"\n--- Turno finalizado. Ahora es el turno de {self.get_current_player().name} ---")