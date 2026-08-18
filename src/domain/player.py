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
