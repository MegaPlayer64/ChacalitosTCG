import random

class Player:

    def __init__(self, player_id, name):
        self.id = player_id
        self.name = name

        self.health = 80

        self.deck = []
        self.hand = [] # max 10
        self.discard_pile = []

        self.max_energy = 0
        self.current_energy = 0

        self.cant_heal_turns = 0
        self.failed_spells_this_turn = set()

        self.crisby_cost_reduction_active = False
        self.d_economia_cost_reduction_active = False

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def refresh_energy(self):
        self.max_energy += 1
        self.current_energy = self.max_energy

    def calcular_costo_efectivo(self, carta) -> tuple[int, bool]:
        """
        Calcula el costo final de energía de una carta aplicando pasivas de descuento.
        Retorna: (costo_final, tiene_descuento)
        """
        costo_base = carta.cost
        descuento = 0
        es_hechizo = getattr(carta, 'card_type', 'unit').lower() == 'spell'

        # 1. Pasiva de Crisby: reduce costo en 1 a cartas con costo base entre 2 y 3
        if self.crisby_cost_reduction_active and 1 <= costo_base <= 4:
            descuento += 1

        # 2. Pasiva de Dante Economista: reduce costo en 1 al primer truco/hechizo
        if self.d_economia_cost_reduction_active and es_hechizo:
            descuento += 1

        costo_final = max(0, costo_base - descuento)
        tiene_descuento = (costo_final < costo_base)
        
        return costo_final, tiene_descuento
