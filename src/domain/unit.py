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
            self.static_abilities.append({"type": "buff_all_attack", "amount": 1})
        elif str(self.id) == "59" or self.name == 'Melsizis (DT)':
            self.static_abilities.append({"type": "buff_tag_attack", "tag": "fuerzas especiales valenzuela", "amount": 1})
            self.static_abilities.append({"type": "buff_tag_speed_if_tag_present", "target_tag": "fuerzas especiales valenzuela", "condition_tag": "cabezal de tren", "amount": 1})
        
        # Posición inicial (fuera del tablero)
        self.pos_x = -1
        self.pos_y = -1

    def take_damage(self, amount: int, game_state) -> bool:
        # """Resta vida y devuelve True si la unidad murió."""
        from domain.ability_manager import AbilityManager
        AbilityManager.trigger_on_damage_received(self, amount, game_state)
        if self.has_shield:
            damage_taken = amount // 2
            self.health -= damage_taken
            print(f">> {self.name} recibió {amount} de daño, pero su escudo lo redujo a {damage_taken}! (Vida restante: {self.health})")
            self.has_shield = False
        else:
            self.health -= amount
            print(f">> {self.name} recibió {amount} de daño! (Vida restante: {self.health})")
        return self.health <= 0

    def reset_turn_state(self):
        # """Limpia las banderas al inicio/fin del turno."""
        self.has_moved = False
        self.has_attacked = False

    def on_enter(self, game_state):
        from domain.ability_manager import AbilityManager
        AbilityManager.trigger_on_enter(self, game_state)

    def on_attack(self, game_state):
        from domain.ability_manager import AbilityManager
        AbilityManager.trigger_on_attack(self, game_state)

