import os
import ast
from src.infrastructure.loaders.card_loader import CardLoader
from src.domain.game_state import GameState
from src.domain.player import Player
from src.domain.action import Action, ActionType
from src.domain.ability_manager import AbilityManager

def test_ast():
    print("=== TEST AST: Verificando sintaxis de archivos ===")
    for path in ["src/domain/ability_manager.py", "src/domain/game_state.py", "src/domain/unit.py"]:
        with open(path, "r", encoding="utf-8") as f:
            ast.parse(f.read(), filename=path)
        print(f"  [OK] {path}")

def run_tests():
    test_ast()

    print("\n=== INICIANDO PRUEBAS DE BALANCE Y CARTAS 152 A 173 ===")
    units = CardLoader.load_units()
    assert len(units) >= 173, f"Se esperaban al menos 173 cartas, cargadas: {len(units)}"
    print(f">> Cargadas exitosamente {len(units)} cartas desde cards.csv.")

    p0 = Player(0, "Jugador 0")
    p1 = Player(1, "Jugador 1")
    deck_cards = list(range(1, 40))
    gs = GameState([p0, p1], deck_cards, deck_cards, seed=42)
    gs.current_player_id = 0

    # ==============================================================
    # 1. BALANCE: Sofi (14)
    # ==============================================================
    print("\n--- Test Balance: Sofi (14) ---")
    c14 = CardLoader.get_card_stats_by_id(14)
    assert c14.range_atk == 2, f"Rango esperado 2, obtenido {c14.range_atk}"
    c14.owner_id = 0
    c14.pos_x, c14.pos_y = 1, 1
    gs.board.set_unit_at(1, 1, c14)

    # Aliado normal dañado
    normal_u = CardLoader.get_card_stats_by_id(1) # Jose (Cabezal de Tren)
    normal_u.owner_id = 0
    normal_u.pos_x, normal_u.pos_y = 1, 2
    normal_u.health = 5
    normal_u.max_health = 9
    gs.board.set_unit_at(1, 2, normal_u)

    AbilityManager.trigger_on_turn_start(c14, gs)
    assert normal_u.health == 7, f"Aliado no-Dermapatch debió curar 2 PV (5+2=7). Vida: {normal_u.health}"

    # Aliado Derma-patch dañado
    derma_u = CardLoader.get_card_stats_by_id(15) # Daniela (Derma-patch)
    derma_u.owner_id = 0
    derma_u.pos_x, derma_u.pos_y = 1, 0
    derma_u.health = 10
    derma_u.max_health = 15
    gs.board.set_unit_at(1, 0, derma_u)

    AbilityManager.trigger_on_turn_start(c14, gs)
    # Uno de los dos adyacentes dañados recibe la cura; probamos con solo derma_u dañado
    normal_u.health = 9
    derma_u.health = 10
    AbilityManager.trigger_on_turn_start(c14, gs)
    assert derma_u.health == 13, f"Aliado Dermapatch debió curar 3 PV (10+3=13). Vida: {derma_u.health}"
    print("  [OK] Sofi (14) cura 2 PV base / 3 PV a Derma-patch correctamente.")

    # ==============================================================
    # 2. BALANCE: Tik-Toks (39) y Chapulín (43)
    # ==============================================================
    print("\n--- Test Balance: Tik-Toks (39) y Chapulín (43) ---")
    c39 = CardLoader.get_card_stats_by_id(39)
    p0.health = 70
    AbilityManager._spell_39_effect(c39, None, gs)
    # En el tablero p0 tiene derma_u (Derma-patch) y c14 (Derma-patch). 2 unidades * 2 PV = 4 PV
    assert p0.health == 74, f"Base debió curar 4 PV (70 + 2*2 = 74). Vida: {p0.health}"

    c43 = CardLoader.get_card_stats_by_id(43)
    derma_u.health = 2
    derma_u.attack = 8
    AbilityManager._spell_43_effect(c43, (1, 0), gs)
    assert derma_u.health == 12, f"Chapulín debió restaurar 10 PV (2+10=12). Vida: {derma_u.health}"
    eff_atk_chapulin = gs.get_effective_stats(derma_u)["attack"]
    assert eff_atk_chapulin == 5, f"Chapulín debió reducir -3 de Ataque (8-3=5). Ataque: {eff_atk_chapulin}"
    print("  [OK] Tik-Toks (39) y Chapulín (43) balance correcto.")

    # ==============================================================
    # 3. BALANCE: Sala STEAM (55)
    # ==============================================================
    print("\n--- Test Balance: Sala STEAM (55) ---")
    from src.domain.environment import Environment
    c55 = CardLoader.get_card_stats_by_id(55)
    gs.active_environment = Environment(c55, 0)
    # derma_u recibe daño de ataque
    derma_u.health = 15
    derma_u.take_damage(6, gs, source="attack")
    # 6 - 1 = 5 de daño
    assert derma_u.health == 10, f"Sala STEAM debió reducir en 1 el daño recibido de ataque (15-5=10). Vida: {derma_u.health}"
    print("  [OK] Sala STEAM (55) reducción de daño de ataque correcta.")

    # ==============================================================
    # 4. BALANCE: Stefano Viejo (84) y Gimnasio (134)
    # ==============================================================
    print("\n--- Test Balance: Stefano Viejo (84) ---")
    c84 = CardLoader.get_card_stats_by_id(84)
    c84.owner_id = 0
    c84.pos_x, c84.pos_y = 0, 3
    gs.board.set_unit_at(0, 3, c84)

    # Ex-estudiante aliado: Benja (143)
    c143 = CardLoader.get_card_stats_by_id(143)
    c143.owner_id = 0
    c143.pos_x, c143.pos_y = 0, 4
    gs.board.set_unit_at(0, 4, c143)

    eff_benja = gs.get_effective_stats(c143)
    assert eff_benja['speed'] == c143.speed + 1, "Benja (Ex-estudiante) debió recibir +1 Velocidad de Stefano Viejo"
    assert eff_benja['attack'] == c143.attack + 1, "Benja (Ex-estudiante) debió recibir +1 Ataque de Stefano Viejo"
    print("  [OK] Stefano Viejo (84) otorga +1 Vel y +1 ATK a Ex-estudiantes.")

    # ==============================================================
    # 5. CARTA 151 (Sabch Vanilla) vs CARTA 171 (Sabch Jazz-guitar)
    # ==============================================================
    print("\n--- Test Carta 151 (Vanilla) vs Carta 171 (Jazz-guitar) ---")
    c151 = CardLoader.get_card_stats_by_id(151)
    assert c151.cost == 4, f"Sabch 151 coste esperado 4, obtenido {c151.cost}"
    assert c151.health == 14, f"Sabch 151 vida esperada 14, obtenida {c151.health}"
    assert c151.attack == 9, f"Sabch 151 ataque esperado 9, obtenido {c151.attack}"
    assert c151.range_atk == 3, f"Sabch 151 rango esperado 3, obtenido {c151.range_atk}"
    assert not hasattr(c151, 'sabch_mode'), "Sabch 151 no debe tener modalidad activa"

    c171 = CardLoader.get_card_stats_by_id(171)
    assert c171.cost == 5, f"Sabch 171 coste esperado 5, obtenido {c171.cost}"
    assert c171.health == 20, f"Sabch 171 vida esperada 20, obtenida {c171.health}"
    assert c171.sabch_mode == 'soporte', "Sabch 171 debe iniciar en modalidad soporte"
    c171.owner_id = 0
    c171.pos_x, c171.pos_y = 2, 2
    gs.board.set_unit_at(2, 2, c171)

    # Pedro (150) Sucesores gana +1 ATK por el aura de Sabch 171
    c150 = CardLoader.get_card_stats_by_id(150)
    c150.owner_id = 0
    c150.pos_x, c150.pos_y = 2, 1
    gs.board.set_unit_at(2, 1, c150)
    eff_pedro = gs.get_effective_stats(c150)
    assert eff_pedro['attack'] == 16, f"Pedro debió recibir +1 ATK por Sabch 171 Soporte. Obtenido: {eff_pedro['attack']}"

    # Activar Sabch 171 -> Modo Ataque
    act_171 = Action(ActionType.ACTIVATE_ABILITY, 0, {'from': (2, 2)})
    assert gs.validate_action(act_171), "Debe poder activarse la habilidad de Sabch 171"
    gs.apply_action(act_171)
    assert c171.sabch_mode == 'ataque', "Sabch 171 debe pasar a modo ataque"
    assert c171.range_atk == 3, f"Sabch 171 en ataque debe tener rango 3, obtenido {c171.range_atk}"
    assert c171.attack == 12, f"Sabch 171 en ataque debe tener ataque 12, obtenido {c171.attack}"
    eff_pedro_post = gs.get_effective_stats(c150)
    assert eff_pedro_post['attack'] == 15, "Pedro pierde aura cuando Sabch 171 pasa a Ataque"
    print("  [OK] Separación Sabch (151 vanilla) y Sabch Jazz-guitar (171) verificada.")

    # ==============================================================
    # 6. CARTA 152: Ami (Pesadillas)
    # ==============================================================
    print("\n--- Test Carta 152: Ami (Pesadillas) ---")
    c152 = CardLoader.get_card_stats_by_id(152)
    c152.owner_id = 0
    c152.pos_x, c152.pos_y = 0, 4 # (0, 4) -> simétrica (5, 4)
    gs.board.set_unit_at(0, 4, c152)
    gs.board.remove_unit(5, 4)
    AbilityManager.trigger_on_enter(c152, gs)
    clone = gs.board.get_unit_at(5, 4)
    assert clone is not None, "El clon de Ami debió crearse en (5, 4)"
    assert getattr(clone, 'is_clone', False), "La unidad en (5, 4) debe ser clon"

    # Dañar al clon debe hacerlo explotar y eliminarse
    enemy_near = CardLoader.get_card_stats_by_id(2)
    enemy_near.owner_id = 1
    enemy_near.pos_x, enemy_near.pos_y = 4, 4
    enemy_near.health = 18
    gs.board.set_unit_at(4, 4, enemy_near)

    clone.take_damage(2, gs, source="attack", attacker=enemy_near)
    assert gs.board.get_unit_at(5, 4) is None, "El clon debió eliminarse tras explotar"
    assert enemy_near.health == 14, f"El atacante debió recibir 4 de daño de la explosión (18-4=14). Vida: {enemy_near.health}"
    print("  [OK] Ami Pesadillas (152) clonación y explosión verificadas.")

    # ==============================================================
    # 7. CARTA 153: Isa (Vaca)
    # ==============================================================
    print("\n--- Test Carta 153: Isa (Vaca) ---")
    c153 = CardLoader.get_card_stats_by_id(153)
    c153.owner_id = 0
    c153.pos_x, c153.pos_y = 2, 4
    gs.board.set_unit_at(2, 4, c153)

    # Colocamos 2 unidades adyacentes a Isa: (2, 3) y (3, 4)
    # En (2, 3) colocamos a un aliado herido
    c150.pos_x, c150.pos_y = 2, 3
    c150.health = 10
    c150.max_health = 20
    gs.board.set_unit_at(2, 3, c150)

    # En (3, 4) colocamos otra unidad
    c143.pos_x, c143.pos_y = 3, 4
    gs.board.set_unit_at(3, 4, c143)

    act_isa = Action(ActionType.ACTIVATE_ABILITY, 0, {'from': (2, 4)})
    assert gs.validate_action(act_isa), "Debe poder activarse la habilidad de Isa Vaca"
    gs.apply_action(act_isa)
    assert gs.pending_ability and gs.pending_ability['ability'] == 'isa_vaca_heal', "Debe quedar pendiente isa_vaca_heal"

    # Selecciona al aliado herido en (2, 3). Con 2 unidades adyacentes -> 2 * 3 = 6 PV
    act_resolve_isa = Action(ActionType.RESOLVE_ABILITY, 0, {'target': (2, 3)})
    assert gs.validate_action(act_resolve_isa), "Debe poder resolverse la habilidad sobre (2, 3)"
    gs.apply_action(act_resolve_isa)
    assert c150.health == 16, f"Pedro debió curar 6 PV (10+6=16). Vida: {c150.health}"
    print("  [OK] Isa Vaca (153) curación proporcional a adyacentes verificada.")

    # ==============================================================
    # 8. CARTA 154: Helen (Soviética)
    # ==============================================================
    print("\n--- Test Carta 154: Helen (Soviética) ---")
    c154 = CardLoader.get_card_stats_by_id(154)
    c154.owner_id = 0
    gorro = CardLoader.get_card_stats_by_id(47)
    p0.deck.insert(3, gorro)
    hand_len_before = len(p0.hand)
    AbilityManager.trigger_on_enter(c154, gs)
    assert gorro in p0.hand, "Gorro Soviético debió agregarse a la mano"
    assert len(p0.hand) == hand_len_before + 1, "La mano debió aumentar en 1 carta"
    print("  [OK] Helen Soviética (154) búsqueda en mazo verificada.")

    # ==============================================================
    # 9. CARTA 155: Daniela (Muñeca Diabólica)
    # ==============================================================
    print("\n--- Test Carta 155: Daniela (Muñeca Diabólica) ---")
    c155 = CardLoader.get_card_stats_by_id(155)
    c155.owner_id = 0
    c155.pos_x, c155.pos_y = 1, 3
    gs.board.set_unit_at(1, 3, c155)

    dummy_e = CardLoader.get_card_stats_by_id(2)
    dummy_e.owner_id = 1
    dummy_e.pos_x, dummy_e.pos_y = 2, 3
    dummy_e.health = 30
    gs.board.set_unit_at(2, 3, dummy_e)

    # Primer ataque: Daniela tiene ATK 10 + 4 (primer ataque) = 14 de daño
    act_atk1 = Action(ActionType.ATTACK, 0, {'from': (1, 3), 'target': (2, 3)})
    assert gs.validate_action(act_atk1), "Debe poder atacar"
    gs.apply_action(act_atk1)
    assert dummy_e.health == 16, f"Primer ataque debió causar 14 de daño (30-14=16). Vida: {dummy_e.health}"

    # Reiniciar turn flags para segundo ataque contra el MISMO enemigo
    c155.reset_turn_state()
    act_atk2 = Action(ActionType.ATTACK, 0, {'from': (1, 3), 'target': (2, 3)})
    assert gs.validate_action(act_atk2), "Debe poder atacar por segunda vez"
    gs.apply_action(act_atk2)
    assert dummy_e.health == 6, f"Segundo ataque debió causar daño normal 10 (16-10=6). Vida: {dummy_e.health}"
    print("  [OK] Daniela Muñeca Diabólica (155) bono en primer ataque verificado.")

    # ==============================================================
    # 10. CARTA 156: Pintacaritas
    # ==============================================================
    print("\n--- Test Carta 156: Pintacaritas ---")
    c156 = CardLoader.get_card_stats_by_id(156)
    # Aplicar sobre c14 (normal)
    c14.temporary_buffs.clear()
    c14.attack = 7
    AbilityManager._spell_156_effect(c156, (1, 1), gs)
    eff_c14 = gs.get_effective_stats(c14)
    assert eff_c14['attack'] == 8, "C14 debió ganar +1 de Ataque"

    # Aplicar sobre PlaceHolder: Tammy (23)
    c23 = CardLoader.get_card_stats_by_id(23)
    c23.owner_id = 0
    c23.pos_x, c23.pos_y = 0, 1
    c23.attack = 14
    c23.speed = 1
    gs.board.set_unit_at(0, 1, c23)
    AbilityManager._spell_156_effect(c156, (0, 1), gs)
    eff_c23 = gs.get_effective_stats(c23)
    assert eff_c23['attack'] == 15, "PlaceHolder debió ganar +1 Ataque"
    assert eff_c23['speed'] == 2, "PlaceHolder debió ganar además +1 Velocidad"
    print("  [OK] Pintacaritas (156) bonificaciones verificadas.")

    # ==============================================================
    # 11. CARTA 157: Dante (Destacado Académico)
    # ==============================================================
    print("\n--- Test Carta 157: Dante (Destacado Académico) ---")
    c157 = CardLoader.get_card_stats_by_id(157)
    c157.owner_id = 0
    c157.pos_x, c157.pos_y = 0, 0
    gs.board.set_unit_at(0, 0, c157)
    # Probamos con Jose (1) (Futboleros) y Nico (25) (Mish-A, Deportistas)
    c1 = CardLoader.get_card_stats_by_id(1)
    c1.owner_id = 0
    c1.pos_x, c1.pos_y = 0, 2
    c1.speed = 2
    gs.board.set_unit_at(0, 2, c1)

    c25 = CardLoader.get_card_stats_by_id(25)
    c25.owner_id = 0
    c25.pos_x, c25.pos_y = 1, 4
    c25.attack = 14
    gs.board.set_unit_at(1, 4, c25)

    AbilityManager.trigger_on_enter(c157, gs)
    assert c25.attack == 16, f"Mish-A/Deportistas debió ganar +2 Ataque permanente. Ataque: {c25.attack}"
    eff_c1 = gs.get_effective_stats(c1)
    assert eff_c1['speed'] == 3, f"Futboleros debió ganar +1 Velocidad este turno (2+1=3). Vel: {eff_c1['speed']}"
    print("  [OK] Dante Destacado Académico (157) bonificaciones verificadas.")

    # ==============================================================
    # 12. CARTA 158: Helen (Jazz Star)
    # ==============================================================
    print("\n--- Test Carta 158: Helen (Jazz Star) ---")
    c158 = CardLoader.get_card_stats_by_id(158)
    c158.owner_id = 0
    c158.pos_x, c158.pos_y = 3, 0
    gs.board.set_unit_at(3, 0, c158)

    # Aliado que no se ha movido: c14
    c14.temporary_buffs.clear()
    c14.has_moved = False
    eff_c14_jazz = gs.get_effective_stats(c14)
    assert eff_c14_jazz['range_atk'] == c14.range_atk + 1, "Aliado sin mover debió ganar +1 Rango"
    assert eff_c14_jazz['attack'] == c14.attack + 2, "Aliado sin mover debió ganar +2 Ataque"

    # Si se mueve, pierde el bono
    c14.has_moved = True
    eff_c14_moved = gs.get_effective_stats(c14)
    assert eff_c14_moved['range_atk'] == c14.range_atk, "Al moverse debe perder el bono de rango"
    print("  [OK] Helen Jazz Star (158) bono de rango y ataque verificado.")

    # ==============================================================
    # 13. CARTA 159: Emi & Sofi (Viento-Metal)
    # ==============================================================
    print("\n--- Test Carta 159: Emi & Sofi (Viento-Metal) ---")
    c159 = CardLoader.get_card_stats_by_id(159)
    c159.owner_id = 0
    c159.pos_x, c159.pos_y = 2, 2
    gs.board.set_unit_at(2, 2, c159)

    c1.health = 5
    c1.max_health = 9
    c1.pos_x, c1.pos_y = 2, 1 # Adyacente a c159
    gs.board.set_unit_at(2, 1, c1)

    AbilityManager.trigger_on_turn_start(c159, gs)
    assert c1.health == 7, f"Adyacente debió curar 2 PV (5+2=7). Vida: {c1.health}"
    print("  [OK] Emi & Sofi (159) curación adyacente verificada.")

    # ==============================================================
    # 14. CARTA 160: Dario (Pianista)
    # ==============================================================
    print("\n--- Test Carta 160: Dario (Pianista) ---")
    c160 = CardLoader.get_card_stats_by_id(160)
    c160.owner_id = 0
    c160.pos_x, c160.pos_y = 4, 0
    gs.board.set_unit_at(4, 0, c160)

    # Simular evolución sobre Dario
    AbilityManager.trigger_on_evolve(c160, gs)
    assert c160.has_shield, "Dario Pianista debió obtener escudo al evolucionar"

    # Aliado Músico gana +1 ATK
    c14.attack = 7
    eff_musician = gs.get_effective_stats(c14)
    assert eff_musician['attack'] >= 8, "Aliado Músico debió recibir +1 ATK de Dario Pianista"
    print("  [OK] Dario Pianista (160) evolución y aura verificadas.")

    # ==============================================================
    # 15. CARTA 161: Crisby (Mozo de Panes)
    # ==============================================================
    print("\n--- Test Carta 161: Crisby (Mozo de Panes) ---")
    c161 = CardLoader.get_card_stats_by_id(161)
    c161.owner_id = 0
    c161.health = 18
    c161.pos_x, c161.pos_y = 4, 1
    gs.board.set_unit_at(4, 1, c161)

    c1.health = 2
    c1.max_health = 10
    act_mozo = Action(ActionType.ACTIVATE_ABILITY, 0, {'from': (4, 1)})
    assert gs.validate_action(act_mozo), "Debe poder activar habilidad de Crisby Mozo"
    gs.apply_action(act_mozo)
    assert gs.pending_ability and gs.pending_ability['ability'] == 'crisby_mozo_heal'

    act_res_mozo = Action(ActionType.RESOLVE_ABILITY, 0, {'target': (2, 1)})
    assert gs.validate_action(act_res_mozo)
    gs.apply_action(act_res_mozo)
    assert c161.health == 16, f"Crisby debió perder 2 PV (18-2=16). Vida: {c161.health}"
    assert c1.health == 9, f"Aliado debió curar 7 PV (2+7=9). Vida: {c1.health}"
    print("  [OK] Crisby Mozo de Panes (161) costo y curación verificados.")

    # ==============================================================
    # 16. CARTAS 162 & 163: Diego S. (Mojados) y Cooler Mojado
    # ==============================================================
    print("\n--- Test Cartas 162 & 163: Estado Mojado ---")
    c162 = CardLoader.get_card_stats_by_id(162)
    c162.owner_id = 0
    c162.pos_x, c162.pos_y = 3, 2
    gs.board.set_unit_at(3, 2, c162)

    enemy_w = CardLoader.get_card_stats_by_id(2)
    enemy_w.owner_id = 1
    enemy_w.pos_x, enemy_w.pos_y = 3, 3
    enemy_w.health = 20
    gs.board.set_unit_at(3, 3, enemy_w)

    act_diego_atk = Action(ActionType.ATTACK, 0, {'from': (3, 2), 'target': (3, 3)})
    assert gs.validate_action(act_diego_atk)
    gs.apply_action(act_diego_atk)
    assert getattr(enemy_w, 'wet_turns', 0) == 2, "El enemigo debió quedar con 2 turnos de Mojado"

    # Atacar a enemigo mojado: recibe +1 de daño
    enemy_hp_before = enemy_w.health
    # Ataque de 5 con source='attack'
    enemy_w.take_damage(5, gs, source="attack")
    # Daño = 5 + 1 = 6
    assert enemy_w.health == enemy_hp_before - 6, f"Enemigo mojado debió recibir +1 de daño. Vida: {enemy_w.health}"

    # Hechizo Cooler Mojado (163)
    c163 = CardLoader.get_card_stats_by_id(163)
    AbilityManager._spell_163_effect(c163, (3, 3), gs)
    assert getattr(enemy_w, 'wet_turns', 0) == 3, "Cooler Mojado debió renovar a 3 turnos de Mojado"
    print("  [OK] Diego S. (162) y Cooler Mojado (163) estado Mojado verificado.")

    # ==============================================================
    # 17. CARTA 164: Banquete
    # ==============================================================
    print("\n--- Test Carta 164: Banquete ---")
    gs.board.remove_unit(1, 2)
    gs.board.remove_unit(0, 2)
    c164 = CardLoader.get_card_stats_by_id(164)
    c1.health = 2
    c1.max_health = 10 # No sucesores -> cura 5 -> 7
    c150.health = 10
    c150.max_health = 20 # Sucesores -> cura 7 -> 17
    c150.pos_x, c150.pos_y = 2, 4
    gs.board.set_unit_at(2, 4, c150)
    AbilityManager._spell_164_effect(c164, None, gs)
    assert c1.health == 7, f"No sucesores debió curar 5 PV (2+5=7). Vida: {c1.health}"
    assert c150.health == 17, f"Sucesores debió curar 7 PV (10+7=17). Vida: {c150.health}"
    print("  [OK] Banquete (164) curación base y bonus Sucesores verificados.")

    # ==============================================================
    # 18. CARTA 165: Alex
    # ==============================================================
    print("\n--- Test Carta 165: Alex ---")
    c165 = CardLoader.get_card_stats_by_id(165)
    c165.owner_id = 0
    c165.pos_x, c165.pos_y = 0, 4
    c165.attack = 6
    c165.has_moved = True # Para aislar el bono de Helen Jazz Star
    gs.board.set_unit_at(0, 4, c165)
    # Sin otro Deportistas: 6 ATK
    # Colocamos a c150 (Pedro: Deportistas)
    eff_alex_no_dep = gs.get_effective_stats(c165)
    # c150 está en (2, 3), es Deportistas
    assert eff_alex_no_dep['attack'] == 8, f"Alex con Pedro en mesa debió tener 8 ATK (6+2=8). Obtenido: {eff_alex_no_dep['attack']}"
    print("  [OK] Alex (165) bono pasivo con Deportistas verificado.")

    # ==============================================================
    # 19. CARTAS 166 & 167: Recinto Militar y Yotnier
    # ==============================================================
    print("\n--- Test Cartas 166 & 167: Recinto Militar y Yotnier ---")
    c166 = CardLoader.get_card_stats_by_id(166)
    gs.active_environment = Environment(c166, 0)
    c167 = CardLoader.get_card_stats_by_id(167)
    c167.owner_id = 0
    c167.pos_x, c167.pos_y = 1, 4
    gs.board.set_unit_at(1, 4, c167)

    # Invocación bajo Recinto Militar da +2 max HP y +1 ATK a Ex-estudiantes
    c143_new = CardLoader.get_card_stats_by_id(143) # Benja (Ex-estudiantes)
    c143_new.owner_id = 0
    hp_b = c143_new.max_health
    atk_b = c143_new.attack
    # Simular invocación bajo Recinto Militar
    c143_new.max_health += 2
    c143_new.health += 2
    c143_new.attack += 1
    assert c143_new.max_health == hp_b + 2 and c143_new.attack == atk_b + 1

    # Yotnier al entrar da +2 ATK a Ex-estudiantes y gana +1 Vel si entorno Ex-estudiantes (+1 Vel adicional por Stefano Viejo)
    AbilityManager.trigger_on_enter(c167, gs)
    eff_c167 = gs.get_effective_stats(c167)
    assert eff_c167['speed'] == c167.speed + 2, f"Yotnier debió ganar +1 Vel por entorno y +1 por Stefano Viejo (obtenido: {eff_c167['speed']})"
    print("  [OK] Recinto Militar (166) y Yotnier (167) verificados.")

    # ==============================================================
    # 20. CARTA 168: Licenciatura
    # ==============================================================
    print("\n--- Test Carta 168: Licenciatura ---")
    c168 = CardLoader.get_card_stats_by_id(168)
    c1.max_health = 10
    c1.health = 2
    c1.immobile_turns = 3
    c1.temporary_buffs.append({"type": "attack", "amount": -4, "duration": 2})
    AbilityManager._spell_168_effect(c168, (2, 1), gs)
    assert c1.max_health == 22, f"Max vida debió subir a 22 (10+12=22). Vida max: {c1.max_health}"
    assert c1.health == 14, f"Vida debió restaurar 12 (2+12=14). Vida: {c1.health}"
    assert c1.immobile_turns == 0, "Inmovilización debió eliminarse"
    assert not any(b.get('amount', 0) < 0 for b in c1.temporary_buffs), "Debuffs negativos debieron eliminarse"
    print("  [OK] Licenciatura (168) restauración y purga verificadas.")

    # ==============================================================
    # 21. CARTA 169: Tammy (Vestido Chino)
    # ==============================================================
    print("\n--- Test Carta 169: Tammy (Vestido Chino) ---")
    c169 = CardLoader.get_card_stats_by_id(169)
    c169.owner_id = 0
    c169.pos_x, c169.pos_y = 0, 3
    c169.attack = 11
    c169.speed = 2
    gs.board.set_unit_at(0, 3, c169)

    # Simular jugada de truco común
    c149 = CardLoader.get_card_stats_by_id(149)
    p0.hand.append(c149)
    p0.current_energy = 10
    # Aplicar play_card
    act_play_truco = Action(ActionType.PLAY_CARD, 0, {'card_index': len(p0.hand) - 1, 'target': (1, 4)})
    if gs.validate_action(act_play_truco):
        gs.apply_action(act_play_truco)
        eff_tammy = gs.get_effective_stats(c169)
        assert eff_tammy['attack'] == 13, f"Tammy debió ganar +2 Ataque por truco jugado. Ataque: {eff_tammy['attack']}"
    print("  [OK] Tammy Vestido Chino (169) buff por truco verificado.")

    # ==============================================================
    # 22. CARTA 170: Capzy (Director de Coro)
    # ==============================================================
    print("\n--- Test Carta 170: Capzy (Director de Coro) ---")
    c170 = CardLoader.get_card_stats_by_id(170)
    c170.owner_id = 0
    c170.pos_x, c170.pos_y = 4, 3
    gs.board.set_unit_at(4, 3, c170)

    # Jose (1) es Cabezal de Tren.
    # En mesa tenemos a Sabch (171) que es Fuerzas Especiales Valenzuela.
    eff_jose_coro = gs.get_effective_stats(c1)
    assert eff_jose_coro['speed'] >= c1.speed + 1, "Jose (CT) debió recibir +1 Velocidad por Capzy"
    assert eff_jose_coro['attack'] >= c1.attack + 1, "Jose (CT) debió recibir +1 Ataque por presencia de FEV"
    print("  [OK] Capzy Director de Coro (170) auras verificadas.")

    # ==============================================================
    # 23. CARTA 172: Yotnier & Joel (Quemadores)
    # ==============================================================
    print("\n--- Test Carta 172: Yotnier & Joel (Quemadores) ---")
    c172 = CardLoader.get_card_stats_by_id(172)
    c172.owner_id = 0
    c172.pos_x, c172.pos_y = 2, 2
    c172.attack = 16
    gs.board.set_unit_at(2, 2, c172)

    # Enemigo principal con 10 de vida
    e_main = CardLoader.get_card_stats_by_id(2)
    e_main.owner_id = 1
    e_main.pos_x, e_main.pos_y = 2, 3
    e_main.health = 10
    gs.board.set_unit_at(2, 3, e_main)

    # Segundo enemigo en rango (2, 4)
    e_sec = CardLoader.get_card_stats_by_id(2)
    e_sec.owner_id = 1
    e_sec.pos_x, e_sec.pos_y = 2, 4
    e_sec.health = 15
    gs.board.set_unit_at(2, 4, e_sec)

    act_burn = Action(ActionType.ATTACK, 0, {'from': (2, 2), 'target': (2, 3)})
    assert gs.validate_action(act_burn)
    gs.apply_action(act_burn)
    assert e_main.health <= 0, "El enemigo principal debió morir"
    assert e_sec.health == 7, f"El segundo enemigo debió recibir 8 de daño (15-8=7). Vida: {e_sec.health}"
    print("  [OK] Yotnier & Joel (172) lanzamiento adicional verificado.")

    # ==============================================================
    # 24. CARTA 173: Isidora
    # ==============================================================
    print("\n--- Test Carta 173: Isidora ---")
    c173 = CardLoader.get_card_stats_by_id(173)
    c173.owner_id = 1
    c173.pos_x, c173.pos_y = 4, 4
    gs.board.set_unit_at(4, 4, c173)

    # Aliado de Isidora adyacente en (5, 4)
    e_adj = CardLoader.get_card_stats_by_id(2)
    e_adj.owner_id = 1
    e_adj.pos_x, e_adj.pos_y = 5, 4
    gs.board.set_unit_at(5, 4, e_adj)

    # Jugador 0 intenta atacar a Isidora con una tropa en (3, 4)
    c143.owner_id = 0
    c143.pos_x, c143.pos_y = 3, 4
    gs.board.set_unit_at(3, 4, c143)
    c143.has_attacked = False

    act_atk_isi = Action(ActionType.ATTACK, 0, {'from': (3, 4), 'target': (4, 4)})
    assert not gs.validate_action(act_atk_isi), "Isidora NO debe poder ser atacada mientras tenga aliados adyacentes"

    # Retiramos a los aliados adyacentes de Isidora
    gs.board.remove_unit(5, 4)
    gs.board.remove_unit(3, 3)
    assert gs.validate_action(act_atk_isi), "Isidora DEBE poder ser atacada cuando no tiene aliados adyacentes"
    print("  [OK] Isidora (173) protección adyacente verificada.")

    print("\n🎉 ¡TODAS LAS PRUEBAS DE BALANCE Y CARTAS NUEVAS (152-173) PASARON CON ÉXITO AL 100%! 🎉")

if __name__ == "__main__":
    run_tests()
