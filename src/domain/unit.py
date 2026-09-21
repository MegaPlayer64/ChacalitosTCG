from .card import Card

class Unit(Card):
    def __init__(self, id, name, cost, health, attack, speed, range_atk, groups, rarity, description):
        # Pasamos los datos a la clase madre Card
        super().__init__(
            id=id, 
            name=name, 
            card_type="unit", 
            cost=cost, 
            groups=groups, 
            rarity=rarity, 
            description=description
        )
        # Atributos específicos de la unidad en el tablero 5x6
        self.max_health = health
        self.health = health
        self.attack = attack
        self.speed = speed
        self.range_atk = range_atk
        self.has_shield = False
        
        # Habilidades estáticas
        self.static_abilities = []
        if str(self.id) == "56" or self.name == 'Margarita (Vintage)':
            self.static_abilities.append({"type": "buff_tag_attack", "tag": ["tralaleros", "artista"], "amount": 1})
        elif str(self.id) == "60" or self.name == 'Melsizis (DT)':
            self.static_abilities.append({"type": "buff_tag_attack", "tag": "fuerzas especiales valenzuela", "amount": 1})
            self.static_abilities.append({"type": "buff_tag_speed_if_tag_present", "target_tag": "fuerzas especiales valenzuela", "condition_tag": "cabezal de tren", "amount": 1})
        elif str(self.id) == "84" or self.name == 'Stefano (Viejo)':
            self.static_abilities.append({"type": "buff_tag_speed", "tag": "cabezal de tren", "amount": 1})
        elif str(self.id) == "106":
            self.static_abilities.append({"type": "buff_adj_attack", "amount": 2})
        self.immobile_turns = 0
        self.evolution = False
        self.has_first_move_buff = False

        self.ability_used_this_turn = False
        # Buffs temporales (Hechizos y estados por turnos)
        self.temporary_buffs = []
        
        # Posición inicial (fuera del tablero)
        self.pos_x = -1
        self.pos_y = -1

    def take_damage(self, amount: int, game_state) -> bool:
        # """Resta vida y devuelve True si la unidad murió."""
        from src.domain.ability_manager import AbilityManager
        AbilityManager.trigger_on_damage_received(self, amount, game_state)
        
        # Entorno ID 73: Escenario de Baile
        active_env = getattr(game_state, 'active_environment', None)
        if active_env and int(active_env.card.id) == 73:
            tags = str(getattr(self, 'groups', '')).lower()
            if '3_nai' in tags or 'músico' in tags or 'musico' in tags or 'danza' in tags or int(self.id) == 22:
                amount = max(0, amount - 1)

        # Entorno ID 54: La Fundación (-1 de daño recibido a Tralaleros)
        if active_env and int(active_env.card.id) == 54:
            tags = str(getattr(self, 'groups', '')).lower()
            if 'tralaleros' in tags or int(self.id) == 22:
                amount = max(0, amount - 1)
                
        if self.has_shield:
            damage_taken = amount // 2
            self.health -= damage_taken
            print(f">> {self.name} recibió {amount} de daño, pero su escudo lo redujo a {damage_taken}! (Vida restante: {self.health})")
            self.has_shield = False
        elif self.id == 61 and not self.ability_used_this_turn:
            print(f">> {self.name} recibió {amount} de daño, pero su inmunidad lo protegió! (Vida restante: {self.health})")
            self.ability_used_this_turn = True
        else:
            self.health -= amount
            print(f">> {self.name} recibió {amount} de daño! (Vida restante: {self.health})")
        if self.health <= 0:
            AbilityManager.trigger_on_death(self, game_state)
            return True
        return False

    def heal(self, amount: int, game_state=None) -> int:
        """Cura vida respetando efectos anti-curación y devuelve la cantidad efectivamente curada."""
        if hasattr(self, 'temporary_buffs'):
            for buff in self.temporary_buffs:
                if buff.get('type') == 'cant_heal' and buff.get('duration', 0) > 0:
                    print(f">> [!] {self.name} no puede curarse (efecto anti-curación activo).")
                    return 0
        if game_state and getattr(self, 'owner_id', None) is not None:
            player = game_state.players[self.owner_id]
            if getattr(player, 'cant_heal_turns', 0) > 0:
                print(f">> [!] {self.name} no puede curarse (efecto anti-curación del jugador).")
                return 0
        old_hp = self.health
        self.health = min(self.max_health, self.health + amount)
        healed = self.health - old_hp
        return healed

    def reset_turn_state(self):
        # """Limpia las banderas al inicio/fin del turno."""
        self.has_moved = False
        self.has_attacked = False
        self.ability_used_this_turn = False
        self.attacks_made = 0
        if getattr(self, 'immobile_turns', 0) > 0:
            self.immobile_turns -= 1

    def on_enter(self, game_state):
        from src.domain.ability_manager import AbilityManager
        AbilityManager.trigger_on_enter(self, game_state)

    def on_attack(self, game_state):
        from src.domain.ability_manager import AbilityManager
        AbilityManager.trigger_on_attack(self, game_state)

    def on_activate(self, game_state):
        from src.domain.ability_manager import AbilityManager
        AbilityManager.trigger_on_activate(self, game_state)

