import sys
import os

# Asegurar path
sys.path.insert(0, os.path.abspath("."))

from src.infrastructure.loaders.card_loader import CardLoader
from src.domain.player import Player
from src.domain.game_state import GameState
from src.domain.action import Action
from src.domain.action_type import ActionType
from src.domain.ability_manager import AbilityManager

def test_all():
    print("=== TEST 1: Verificar Carga de las 138 Cartas ===")
    units = CardLoader.load_units()
    assert len(units) == 138, f"Esperado 138 cartas, obtenido {len(units)}"
    for cid in range(1, 139):
        card = CardLoader.get_card_stats_by_id(cid)
        assert card is not None, f"Fallo al cargar carta ID {cid}"
    print(f">> Todas las {len(units)} cartas cargaron correctamente.")

    print("\n=== TEST 2: Escuadrón Conejo (123) y Energía Turno Siguiente ===")
    p0 = Player(0, "P0")
    p1 = Player(1, "P1")
    deck_cards = list(range(1, 40))
    gs = GameState([p0, p1], deck_cards, deck_cards, seed=42)
    # Colocar Rin (22)
    rin = CardLoader.get_card_stats_by_id(22)
    rin.owner_id = 0
    gs.board.set_unit_at(0, 0, rin)
    initial_hand_len = len(p0.hand)
    
    c123 = CardLoader.get_card_stats_by_id(123)
    p0.current_energy = 10
    AbilityManager._spell_123_effect(c123, None, gs)
    assert p0.bonus_energy_next_turn == 2, f"Bonus energía esperado 2, obtenido {p0.bonus_energy_next_turn}"
    assert len(p0.hand) == initial_hand_len + 1, "Debería haber robado 1 carta por controlar a Rin"
    
    # Simular refresh_energy
    p0.refresh_energy()
    assert p0.current_energy == p0.max_energy + 2, "current_energy debería incluir el bonus"
    assert p0.bonus_energy_next_turn == 0, "bonus_energy_next_turn debe resetearse a 0"
    print(">> Carta 123 OK.")

    print("\n=== TEST 3: Competencia Internacional (125) y Fichas Dermapatch (126-129) ===")
    # Colocar Richi común (17)
    richi_comun = CardLoader.get_card_stats_by_id(17)
    richi_comun.owner_id = 0
    richi_comun.health = 5 # herido
    gs.board.set_unit_at(1, 1, richi_comun)
    
    c125 = CardLoader.get_card_stats_by_id(125)
    AbilityManager._spell_125_effect(c125, (1, 1), gs)
    transformed = gs.board.get_unit_at(1, 1)
    assert int(transformed.id) == 126, f"Esperado ID 126, obtenido {transformed.id}"
    assert transformed.health == transformed.max_health == 31, f"Vida restaurada completa: {transformed.health}"
    print(">> Carta 125 y Transformación a 126 OK.")

    print("\n=== TEST 4: Richi Dermapatch (126) Pasiva Daño a Distancia y On-Kill ===")
    # Richi 126 recibe daño a distancia (range >= 2)
    attacker_dist = CardLoader.get_card_stats_by_id(61) # Quemadas, range 2
    attacker_dist.owner_id = 1
    attacker_dist.pos_x, attacker_dist.pos_y = 1, 3
    
    hp_before = transformed.health
    # Daño de 10 a distancia -> debe recibir 10 - 3 = 7
    transformed.take_damage(10, gs, source="attack", attacker=attacker_dist)
    assert transformed.health == hp_before - 7, f"Esperado vida {hp_before - 7}, obtenido {transformed.health}"
    print(">> Richi 126 mitigación distancia OK.")

    # Richi on-kill restaura 3 a la Base
    p0.health = 70
    enemy_target = CardLoader.get_card_stats_by_id(10)
    enemy_target.owner_id = 1
    enemy_target.health = 2
    gs.board.set_unit_at(1, 2, enemy_target)
    # Ejecutar acción de ataque de Richi a enemigo
    transformed.pos_x, transformed.pos_y = 1, 1
    act_atk = Action(ActionType.ATTACK, 0, {'from': (1, 1), 'target': (1, 2)})
    gs.current_player_id = 0
    gs.apply_action(act_atk)
    assert p0.health == 73, f"Esperado vida Base 73, obtenido {p0.health}"
    print(">> Richi 126 on-kill cura Base OK.")

    print("\n=== TEST 5: Emi Dermapatch (127) Inmunidad a Inmovilización y Mitigación Truco ===")
    emi = CardLoader.get_card_stats_by_id(127)
    emi.owner_id = 0
    emi.immobile_turns = 3
    assert emi.immobile_turns == 0, "Emi 127 debe ser inmune a inmovilización"
    
    emi_hp = emi.health
    emi.take_damage(5, gs, source="spell")
    # Mitiga 3 del truco: 5 - 3 = 2 de daño
    assert emi.health == emi_hp - 2, f"Esperado vida {emi_hp - 2}, obtenido {emi.health}"
    print(">> Emi 127 pasivas OK.")

    print("\n=== TEST 6: Sofi Dermapatch (128) Cura al más herido al inicio del turno ===")
    sofi = CardLoader.get_card_stats_by_id(128)
    sofi.owner_id = 0
    gs.board.set_unit_at(0, 1, sofi)
    ally_hurt = CardLoader.get_card_stats_by_id(2)
    ally_hurt.owner_id = 0
    ally_hurt.health = 5
    gs.board.set_unit_at(0, 2, ally_hurt)
    AbilityManager._sofi_dermapatch_on_turn_start(sofi, gs)
    assert ally_hurt.health == 10, f"Esperado vida 10, obtenido {ally_hurt.health}"
    print(">> Sofi 128 cura al inicio de turno OK.")

    print("\n=== TEST 7: Daniela Dermapatch (129) +3 ATK si Base rival > Base aliada ===")
    daniela = CardLoader.get_card_stats_by_id(129)
    daniela.owner_id = 0
    p0.health = 50
    p1.health = 60
    stats = gs.get_effective_stats(daniela)
    assert stats["attack"] == daniela.attack + 3, f"Esperado ATK {daniela.attack + 3}, obtenido {stats['attack']}"
    p0.health = 70
    stats2 = gs.get_effective_stats(daniela)
    assert stats2["attack"] == daniela.attack, f"Esperado ATK base {daniela.attack}, obtenido {stats2['attack']}"
    print(">> Daniela 129 condición de ataque OK.")

    print("\n=== TEST 8: Vicente Portero (130) Guardaespaldas Intercepta Daño ===")
    vicente_p = CardLoader.get_card_stats_by_id(130)
    vicente_p.owner_id = 0
    vicente_p.pos_x, vicente_p.pos_y = 0, 3
    gs.board.set_unit_at(0, 3, vicente_p)
    
    protected_ally = CardLoader.get_card_stats_by_id(2)
    protected_ally.owner_id = 0
    protected_ally.pos_x, protected_ally.pos_y = 0, 4 # adyacente a (0,3)
    gs.board.set_unit_at(0, 4, protected_ally)
    
    ally_hp_start = protected_ally.health
    vicente_hp_start = vicente_p.health
    
    # El aliado recibe 8 de daño
    protected_ally.take_damage(8, gs)
    assert protected_ally.health == ally_hp_start, "El aliado protegido no debió recibir daño"
    assert vicente_p.health == vicente_hp_start - 8, f"Vicente debió interceptar el daño. Vida: {vicente_p.health}"
    print(">> Vicente Portero 130 Guardaespaldas OK.")

    print("\n=== TEST 9: Vicente Conejo Malo (131) Evolución e Inmovilización Global ===")
    vicente_bm = CardLoader.get_card_stats_by_id(131)
    vicente_bm.owner_id = 0
    enemy1 = CardLoader.get_card_stats_by_id(3)
    enemy1.owner_id = 1
    gs.board.set_unit_at(4, 4, enemy1)
    AbilityManager._vicente_conejo_malo_on_evolve(vicente_bm, gs)
    assert enemy1.immobile_turns >= 1, "Enemigo debió ser inmovilizado por la evolución"
    print(">> Vicente Conejo Malo 131 Evolución OK.")

    print("\n=== TEST 10: Entorno 132 Laboratorio de Computación (+1 energía con Truco si Tecnológico) ===")
    from src.domain.environment import Environment
    c132 = CardLoader.get_card_stats_by_id(132)
    gs.active_environment = Environment(c132, 0)
    # Colocar unidad tecnológica aliada
    tec_unit = CardLoader.get_card_stats_by_id(58) # Dante economista: Tecnológico
    tec_unit.owner_id = 0
    gs.board.set_unit_at(2, 2, tec_unit)
    
    p0.current_energy = 5
    # Simular jugar truco exitoso
    c_truco = CardLoader.get_card_stats_by_id(44)
    p0.hand.append(c_truco)
    act_spell = Action(ActionType.PLAY_SPELL, 0, {'card_index': len(p0.hand)-1, 'target': None})
    gs.current_player_id = 0
    gs.apply_action(act_spell)
    # Costo 44 es 3 (base). Dante colocado con set_unit_at no activa on_enter,
    # así que d_economia_cost_reduction_active no está activo.
    # Flujo: 5 - 3 (coste base) + 1 (Laboratorio) = 3.
    assert p0.current_energy == 3, f"Esperado energía 3, obtenido {p0.current_energy}"
    print(">> Entorno 132 OK.")

    print("\n=== TEST 11: Entorno 133 Taller de Artes (+2 ATK, +2 PV al invocar Artista) ===")
    c133 = CardLoader.get_card_stats_by_id(133)
    gs.active_environment = Environment(c133, 0)
    artista = CardLoader.get_card_stats_by_id(56) # Margarita Vintage (Artista)
    orig_atk = artista.attack
    orig_hp = artista.max_health
    p0.current_energy = 10
    p0.hand.append(artista)
    act_summon = Action(ActionType.PLAY_CARD, 0, {'card_index': len(p0.hand)-1, 'to': (0, 0)})
    gs.board.remove_unit(0, 0) # asegurar vacío
    gs.apply_action(act_summon)
    summoned = gs.board.get_unit_at(0, 0)
    assert summoned.attack == orig_atk + 2, f"Esperado ATK {orig_atk + 2}, obtenido {summoned.attack}"
    assert summoned.max_health == orig_hp + 2, f"Esperado HP {orig_hp + 2}, obtenido {summoned.max_health}"
    print(">> Entorno 133 OK.")

    print("\n=== TEST 12: Entorno 134 Gimnasio (+2 PV Deportistas, Inmune a reducción vel) ===")
    c134 = CardLoader.get_card_stats_by_id(134)
    gs.active_environment = Environment(c134, 0)
    deportista = CardLoader.get_card_stats_by_id(60) # Melsizis DT (Deportistas)
    orig_hp = deportista.max_health
    p0.current_energy = 10
    p0.hand.append(deportista)
    gs.board.remove_unit(1, 0)
    act_summon_dep = Action(ActionType.PLAY_CARD, 0, {'card_index': len(p0.hand)-1, 'to': (1, 0)})
    gs.apply_action(act_summon_dep)
    dep_on_board = gs.board.get_unit_at(1, 0)
    assert dep_on_board.max_health == orig_hp + 2, f"Esperado HP {orig_hp + 2}, obtenido {dep_on_board.max_health}"
    # Debuff de velocidad
    dep_on_board.temporary_buffs.append({"type": "speed", "amount": -3, "duration": 1})
    eff_spd = gs.get_effective_stats(dep_on_board)["speed"]
    assert eff_spd == dep_on_board.speed, f"Esperado velocidad {dep_on_board.speed}, obtenido {eff_spd}"
    print(">> Entorno 134 OK.")

    print("\n=== TEST 13: Entorno 135 El Casino (Cura a Nuevo más herido o roba carta) ===")
    c135 = CardLoader.get_card_stats_by_id(135)
    gs.active_environment = Environment(c135, 0)
    # Limpiar el tablero para aislar este test de efectos residuales previos
    for rx in range(gs.board.width):
        for ry in range(gs.board.height):
            gs.board.remove_unit(rx, ry)
    nuevo_unit = CardLoader.get_card_stats_by_id(28) # Cristóbal (Nuevo)
    nuevo_unit.owner_id = 0
    nuevo_unit.health = 5
    gs.board.set_unit_at(0, 0, nuevo_unit)
    gs.current_player_id = 0
    # Iniciar turno
    gs._start_turn()
    assert nuevo_unit.health == 9, f"Esperado vida 9, obtenido {nuevo_unit.health}"
    print(">> Entorno 135 OK.")

    print("\n=== TEST 14: Crisby Caballo (136) Empuja al Enemigo e Inmoviliza ===")
    crisby_h = CardLoader.get_card_stats_by_id(136)
    crisby_h.owner_id = 0
    crisby_h.pos_x, crisby_h.pos_y = 2, 2
    gs.board.set_unit_at(2, 2, crisby_h)
    
    enemy_to_push = CardLoader.get_card_stats_by_id(10)
    enemy_to_push.owner_id = 1
    enemy_to_push.pos_x, enemy_to_push.pos_y = 3, 2
    gs.board.set_unit_at(3, 2, enemy_to_push)
    
    # Destino hacia atrás para jugador 1 es x=4
    gs.board.remove_unit(4, 2)
    
    act_move = Action(ActionType.MOVE, 0, {'from': (2, 2), 'to': (3, 2)})
    assert gs.validate_action(act_move), "Movimiento de Crisby debería ser válido con empuje"
    gs.apply_action(act_move)
    assert gs.board.get_unit_at(3, 2) == crisby_h, "Crisby debería estar ahora en (3, 2)"
    pushed = gs.board.get_unit_at(4, 2)
    assert pushed == enemy_to_push, "El enemigo debió ser empujado a (4, 2)"
    assert pushed.immobile_turns >= 1, "El enemigo empujado debe estar inmovilizado"
    print(">> Crisby Caballo 136 OK.")

    print("\n=== TEST 15: Prueba del Libro Complementario (137) ===")
    c137 = CardLoader.get_card_stats_by_id(137)
    # Añadir literatura para activar debuff de ataque
    lit_unit = CardLoader.get_card_stats_by_id(64) # Zander (Literatura)
    lit_unit.owner_id = 0
    gs.board.set_unit_at(0, 0, lit_unit)
    AbilityManager._spell_137_effect(c137, None, gs)
    assert pushed.immobile_turns >= 1, "Enemigo debió ser inmovilizado"
    has_atk_debuff = any(b['type'] == 'attack' and b['amount'] == -2 for b in pushed.temporary_buffs)
    assert has_atk_debuff, "Enemigo debió recibir debuff de -2 de Ataque"
    print(">> Carta 137 OK.")

    print("\n=== TEST 16: M. Ogrodnik (138) Roba carta si hay aliados de otro grupo ===")
    ogrodnik = CardLoader.get_card_stats_by_id(138)
    ogrodnik.owner_id = 0
    h_len = len(p0.hand)
    AbilityManager._m_ogrodnik_on_enter(ogrodnik, gs)
    assert len(p0.hand) == h_len + 1, "M. Ogrodnik debió robar 1 carta por haber un aliado que no es sólo Nuevo"
    print(">> Carta 138 OK.")

    print("\n=== TEST 17: Balance Cambios - Margarita Vampira (91) Cura a la Base ===")
    p0.health = 70
    vampira = CardLoader.get_card_stats_by_id(91)
    vampira.owner_id = 0
    gs.board.set_unit_at(0, 3, vampira)
    
    target_dummy = CardLoader.get_card_stats_by_id(2)
    target_dummy.owner_id = 1
    target_dummy.health = 20
    gs.board.set_unit_at(1, 3, target_dummy)
    
    vampira.pos_x, vampira.pos_y = 0, 3
    act_vamp = Action(ActionType.ATTACK, 0, {'from': (0, 3), 'target': (1, 3)})
    eff_atk = gs.get_effective_stats(vampira)["attack"]
    gs.current_player_id = 0
    gs.apply_action(act_vamp)
    # Cura 50% de daño infligido hacia la Base aliada (p0.health)
    import math
    expected_heal = math.ceil(eff_atk / 2)
    assert p0.health == 70 + expected_heal, f"Esperado vida Base {70 + expected_heal}, obtenido {p0.health}"
    print(">> Margarita Vampira 91 cura Base OK.")

    print("\n=== TEST 18: Balance Cambios - Sesión de Manicure (121) Cura a la Base ===")
    p0.health = 60
    c121 = CardLoader.get_card_stats_by_id(121)
    # Re-colocar tec_unit (Dante Economista) en (2,2) ya que el tablero fue limpiado en Test 13
    tec_unit.owner_id = 0
    gs.board.set_unit_at(2, 2, tec_unit)
    gs.current_player_id = 0
    AbilityManager._spell_121_effect(c121, (2, 2), gs)
    assert p0.health == 64, f"Base debió curarse 4 PV. Actual: {p0.health}"
    assert any(b['type'] == 'attack' and b['amount'] == 4 for b in tec_unit.temporary_buffs)
    print(">> Sesión de Manicure 121 OK.")

    print("\n=== ¡TODAS LAS PRUEBAS DE LAS 138 CARTAS PASARON CON ÉXITO! ===")

if __name__ == "__main__":
    test_all()
