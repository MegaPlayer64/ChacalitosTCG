from src.domain import unit
from src.domain.game_state import GameState
from src.domain.audio_manager import AudioManager

class AbilityManager:

    @staticmethod
    def trigger_on_enter(unit, game_state):
        uid = int(unit.id)
        if uid == 31:
            AbilityManager._martina_nueva_on_enter(unit, game_state)
        elif uid == 28:
            AbilityManager._cristobal_on_enter(unit, game_state)
        elif uid == 24:
            AbilityManager._josefa_g_on_enter(unit, game_state)
        elif uid == 29:
            AbilityManager._crisby_on_enter(unit, game_state)
        elif uid == 30:
            AbilityManager._josefa_a_on_enter(unit, game_state)
        elif uid == 17:
            AbilityManager._richi_on_enter(unit, game_state)
        elif uid == 70:
            unit.turns_alive = 0
        elif uid == 58:
            AbilityManager._dante_economista_main_ability(unit, game_state)

    @staticmethod
    def trigger_on_activate(unit, game_state):
        if int(unit.id) == 12:
            AbilityManager._stefano_on_activate(unit, game_state)
        elif int(unit.id) == 25:
            AbilityManager._nico_on_activate(unit, game_state)
        elif int(unit.id) == 59:
            AbilityManager._crisby_airsoft_on_activate(unit, game_state)
        elif int(unit.id) == 63:
            AbilityManager._cutino_on_activate(unit, game_state)
        elif int(unit.id) == 64:
            AbilityManager._zander_on_activate(unit, game_state)
        elif int(unit.id) == 68:
            AbilityManager._dante_yukata_on_activate(unit, game_state)
        

    @staticmethod
    def trigger_on_attack(unit, game_state):
        if int(unit.id) == 3:
            AbilityManager._kapsi_on_attack(unit, game_state)
        elif int(unit.id) == 15:
            AbilityManager._daniela_on_attack(unit, game_state)
        elif int(unit.id) == 57:
            AbilityManager._amira_presidenta_on_attack(unit, game_state)
        elif int(unit.id) == 81:
            AbilityManager._jose_enmascarado_on_attack(unit, game_state)
        elif int(unit.id) == 75:
            AbilityManager._rafa_on_attack(unit, game_state)

    @staticmethod
    def trigger_on_damage_received(unit, damage, game_state):
        if int(unit.id) == 61:
            AbilityManager._chino_quemadas_on_damage_received(unit, damage, game_state)
        elif int(unit.id) == 21:
            AbilityManager._iara_on_damage_received(unit, damage, game_state)
        elif int(unit.id) == 79:
            AbilityManager._axel_on_damage_receaved(unit, game_state)
        elif int(unit.id) == 31:
            AbilityManager._martina_nueva_on_damage_received(unit, damage, game_state)
  
    @staticmethod
    def trigger_on_turn_start(unit, game_state):
        active_env = getattr(game_state, 'active_environment', None)
        env_id = int(active_env.card.id) if active_env else None

        if int(unit.id) == 25:
            AbilityManager._nico_on_turn_start(unit, game_state)
        elif int(unit.id) == 14:
            AbilityManager._sofi_on_turn_start(unit, game_state)
        elif env_id == 55:
            AbilityManager._STEAM_on_turn_start(unit, game_state)
        elif int(unit.id) == 58:
            AbilityManager._dante_economista_main_ability(unit, game_state)
        elif int(unit.id) == 70:
            AbilityManager._dragon_menor_on_turn_start(unit, game_state)

    @staticmethod
    def trigger_on_death(unit, game_state):
        if int(unit.id) == 65:
            AbilityManager._gandan_on_death(unit, game_state)

    @staticmethod
    def resolve_pending_ability(game_state, payload):
        pending = game_state.pending_ability
        if not pending: return False
        
        target = payload.get('target')
        if not isinstance(target, tuple): return False
        tx, ty = target
        
        if pending['ability'] == 'encore':
            fx, fy = pending['unit_coords']
            unit = game_state.board.get_unit_at(fx, fy)
            if not unit: return False
            
            if game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty):
                dist = abs(fx - tx) + abs(fy - ty)
                if dist <= 1:
                    game_state.board.move_unit(fx, fy, tx, ty)
                    print(f">> {unit.name} se movió a ({tx}, {ty}).")
                    return True
                else:
                    print(">> [!] Distancia mayor a 1 para Encore.")
        elif pending['ability'] == 'daiaodama':
            fx, fy = pending['source_coords']
            unit = game_state.board.get_unit_at(fx, fy)
            if not unit: return False
            
            enemy_unit = game_state.board.get_unit_at(tx, ty)
            dist = max(abs(fx - tx), abs(fy - ty))
            if enemy_unit and enemy_unit.owner_id != unit.owner_id and dist <= 3:
                murio = enemy_unit.take_damage(7, game_state)
                if unit.owner_id == 0:
                    try:
                        from src.domain.mission_manager import MissionManager
                        MissionManager.track_damage(0, 7, getattr(unit, 'groups', ''))
                        if murio:
                            MissionManager.track_kill(0, getattr(unit, 'groups', ''), getattr(enemy_unit, 'groups', ''))
                    except Exception:
                        pass
                if murio:
                    print(f">> ¡{enemy_unit.name} ha sido destruido por Daiaodama!")
                    game_state.board.remove_unit(tx, ty)
                return True
            else:
                print(">> [!] Objetivo inválido o fuera de rango (Máximo 3).")
            return False
            
        elif pending['ability'] == 'josefa_a':
            target_unit = game_state.board.get_unit_at(tx, ty)
            if target_unit and target_unit.owner_id == pending['owner_id']:
                target_unit.has_shield = True
                print(f">> ¡{target_unit.name} recibió el Escudo de Josefa A!")
                return True
            else:
                print(">> No se seleccionó un aliado válido. Toca un aliado.")
            return False
            
        elif pending['ability'] == 'kapsi_retreat':
            fx, fy = pending['unit_coords']
            if game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty):
                # Permite moverse a casillas adyacentes (rango 1 en x y y)
                if abs(fx - tx) <= 1 and abs(fy - ty) <= 1:
                    game_state.board.move_unit(fx, fy, tx, ty)
                    print(f">> Kapsi se retiró a ({tx}, {ty})")
                    return True
            return False

        elif pending['ability'] == 'cutino_summon':
            sx, sy = pending['source_coords']
            unit = game_state.board.get_unit_at(sx, sy)
            if not unit: return False
            if max(abs(tx - sx), abs(ty - sy)) <= 1 and not game_state.board.is_occupied(tx, ty):
                player = game_state.players[unit.owner_id]
                player.current_energy -= 3
                from src.infrastructure.loaders.card_loader import CardLoader
                gandan_card = CardLoader.get_card_stats_by_id(65)
                gandan_card.owner_id = unit.owner_id
                game_state.board.set_unit_at(tx, ty, gandan_card)
                unit.ability_used_this_turn = True
                print(f">> [Cutiño] ¡Gandan fue invocado en ({tx}, {ty})!")
                return True
            else:
                print(">> [Cutiño] Debes invocar a Gandan en una casilla adyacente vacía.")
                return False

        elif pending['ability'] == 'zander_move_1':
            ally = game_state.board.get_unit_at(tx, ty)
            sx, sy = pending['source_coords']
            unit = game_state.board.get_unit_at(sx, sy)
            if ally and ally.owner_id == unit.owner_id:
                game_state.pending_ability = {
                    'ability': 'zander_move_2',
                    'source_coords': (sx, sy),
                    'target_unit': (tx, ty)
                }
                print(f">> [Zander] Ahora selecciona una casilla adyacente vacía para mover a {ally.name}.")
                return True
            else:
                print(">> [Zander] Selecciona un aliado válido.")
                return False

        elif pending['ability'] == 'zander_move_2':
            tux, tuy = pending['target_unit']
            ally = game_state.board.get_unit_at(tux, tuy)
            if ally and not game_state.board.is_occupied(tx, ty):
                if max(abs(tx - tux), abs(ty - tuy)) <= 1:
                    game_state.board.move_unit(tux, tuy, tx, ty)
                    
                    sx, sy = pending['source_coords']
                    unit = game_state.board.get_unit_at(sx, sy)
                    if unit:
                        unit.ability_used_this_turn = True
                        
                    print(f">> [Zander] ¡{ally.name} fue movido a ({tx}, {ty})!")
                    return True
            print(">> [Zander] Movimiento inválido.")
            return False

        elif pending['ability'] == 'dante_yukata_attack':
            sx, sy = pending['source_coords']
            unit = game_state.board.get_unit_at(sx, sy)
            if not unit: return False
            
            enemy_unit = game_state.board.get_unit_at(tx, ty)
            dist = max(abs(sx - tx), abs(sy - ty))
            eff_range = game_state.get_effective_stats(unit)["range_atk"]
            if enemy_unit and enemy_unit.owner_id != unit.owner_id and dist <= (eff_range + 1):
                murio = enemy_unit.take_damage(6, game_state)
                if unit.owner_id == 0:
                    try:
                        from src.domain.mission_manager import MissionManager
                        MissionManager.track_damage(0, 6, getattr(unit, 'groups', ''))
                        if murio:
                            MissionManager.track_kill(0, getattr(unit, 'groups', ''), getattr(enemy_unit, 'groups', ''))
                    except Exception:
                        pass
                if murio:
                    print(f">> ¡{enemy_unit.name} ha sido destruido por el Miku Peluche!")
                    game_state.board.remove_unit(tx, ty)
                unit.ability_used_this_turn = True
                return True
            else:
                print(">> [Dante Yukata] Objetivo inválido o fuera de rango.")
                return False
            

        elif pending['ability'] == 'chino_quemadas':
            fx, fy = pending['unit_coords']
            effective_speed = pending['speed']
            dist = abs(fx - tx) + abs(fy - ty)
            
            if game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty) and dist <= effective_speed:
                game_state.board.move_unit(fx, fy, tx, ty)
                print(f">> ¡ESQUIVA! Chino se movió a ({tx}, {ty}) y anuló el daño.")
                return True
            else:
                print(">> [!] Casilla de escape inválida.")
            return False
        
        return False
        
        return False

    @staticmethod
    def execute_spell(card, target, game_state):
        print(f">> [Hechizo]: Ejecutando efecto de {card.name}")
        
        # Inmunidad de Feña (ID 66) a hechizos enemigos
        if target != 'G' and isinstance(target, tuple):
            target_unit = game_state.board.get_unit_at(*target)
            if target_unit and int(target_unit.id) == 66 and int(target_unit.owner_id) != int(game_state.current_player_id):
                aliados = [u for u in game_state.board.get_all_units() if u.owner_id == target_unit.owner_id and u is not target_unit]
                if aliados:
                    print(f">> [Feña] ¡Es inmune a hechizos enemigos mientras tenga aliados vivos!")
                    return False

        effect_methods = {
            32: AbilityManager._spell_32_effect,
            33: AbilityManager._spell_33_effect,
            34: AbilityManager._spell_34_effect,
            35: AbilityManager._spell_35_effect,
            36: AbilityManager._spell_36_effect,
            37: AbilityManager._spell_37_effect,
            38: AbilityManager._spell_38_effect,
            39: AbilityManager._spell_39_effect,
            40: AbilityManager._spell_40_effect,
            41: AbilityManager._spell_41_effect,
            42: AbilityManager._spell_42_effect,
            43: AbilityManager._spell_43_effect,
            44: AbilityManager._spell_44_effect,
            45: AbilityManager._spell_45_effect,
            46: AbilityManager._spell_46_effect,
            47: AbilityManager._spell_47_effect,
            48: AbilityManager._spell_48_effect,
            49: AbilityManager._spell_49_effect,
            50: AbilityManager._spell_50_effect,
            51: AbilityManager._spell_51_effect,
            71: AbilityManager._spell_71_effect,
            72: AbilityManager._spell_72_effect,
            76: AbilityManager._spell_76_effect,
            77: AbilityManager._spell_77_effect,
        }
        
        method = effect_methods.get(int(card.id))
        if method:
            return method(card, target, game_state)
        else:
            print(f">> [Hechizo]: Efecto para ID {card.id} no implementado.")
            return False

    @staticmethod
    def _spell_32_effect(card, target, game_state):
        # Ida al Casino / Llamado de otro punto:
        # Atrae una unidad en el tablero (aliada o enemiga) hasta 2 casillas hacia tu unidad aliada más cercana.
        
        # 1. Normalizar target (Aceptar tanto tuplas como listas [x, y])
        if isinstance(target, list):
            target = tuple(target)
        if not isinstance(target, tuple) or len(target) < 2: 
            return False
            
        tx, ty = target
        target_unit = game_state.board.get_unit_at(tx, ty)
        
        # 2. Debe ser una unidad válida en el tablero
        if not target_unit:
            print(">> [Llamado de otro punto] Debes seleccionar una unidad en el tablero.")
            return False
        
        # 3. Buscar unidades aliadas en el tablero
        todos_los_aliados = game_state.board.get_all_units(game_state.current_player_id)
        
        # Si el objetivo es una unidad aliada propia, la excluimos para no atraerla hacia sí misma
        aliados_destino = [u for u in todos_los_aliados if u is not target_unit]
        
        if not aliados_destino:
            print(">> [Llamado de otro punto] No tienes otra unidad aliada en el tablero hacia la cual atraer el objetivo.")
            return False
            
        # Buscar la unidad aliada de destino más cercana (Manhattan distance)
        aliado_cercano = min(aliados_destino, key=lambda u: abs(u.pos_x - target_unit.pos_x) + abs(u.pos_y - target_unit.pos_y))
        
        # 4. Calcular vector de dirección
        dx = aliado_cercano.pos_x - target_unit.pos_x
        dy = aliado_cercano.pos_y - target_unit.pos_y
        
        step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
        step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
        
        # Priorizar el eje principal si no están alineados
        if step_x != 0 and step_y != 0:
            if abs(dx) >= abs(dy):
                step_y = 0
            else:
                step_x = 0
        
        # 5. Mover hasta 2 casillas hacia el destino mientras las casillas estén vacías
        board = game_state.board
        casillas_movidas = 0
        current_x, current_y = target_unit.pos_x, target_unit.pos_y
        
        for _ in range(2):
            next_x = current_x + step_x
            next_y = current_y + step_y
            
            # Verificar límites de tablero y que la casilla esté libre
            if board.is_within_bounds(next_x, next_y) and not board.is_occupied(next_x, next_y):
                current_x, current_y = next_x, next_y
                casillas_movidas += 1
            else:
                break
        
        # 6. Actualizar posición si se movió
        if casillas_movidas > 0:
            board.remove_unit(target_unit.pos_x, target_unit.pos_y)
            board.set_unit_at(current_x, current_y, target_unit)
            print(f">> [Ida al casino] ¡{target_unit.name} fue atraído a ({current_x}, {current_y})!")
        else:
            print(f">> [Ida al casino] {target_unit.name} no se pudo desplazar (bloqueado o adyacente).")
        
        # 7. Condición de robo: Si la unidad objetivo tiene la etiqueta/tag "Nuevo"
        if hasattr(target_unit, 'groups') and target_unit.groups:
            groups_str = str(target_unit.groups).lower()
            if 'nuevo' in groups_str:
                player = game_state.get_current_player()
                if len(player.hand) < 10 and player.deck:
                    drawn_card = player.deck.pop(0)
                    player.hand.append(drawn_card)
                    print(f">> [Ida al casino] ¡Objetivo con etiqueta 'Nuevo'! Robaste: {drawn_card.name}")
        
        return True

    @staticmethod
    def _spell_33_effect(card, target, game_state):
        if not isinstance(target, tuple): 
            return False
            
        tx, ty = target
        target_unit = game_state.board.get_unit_at(tx, ty)
        player = game_state.players[target_unit.owner_id]
        if not target_unit or target_unit.owner_id != player.id: return False
        
        
        tags = str(getattr(target_unit, 'groups', '')).lower()
        heal_amount = 12 if 'Fuerzas Especiales Valenzuela' in tags or 'Cabezal de Tren' in tags else 10
        
        player = game_state.players[target_unit.owner_id]
        if getattr(player, 'cant_heal_turns', 0) > 0:
            print(f">> [!] {player.name} está bajo un efecto que impide la curación.")
        else:
            target_unit.health = min(target_unit.max_health, target_unit.health + heal_amount)
            print(f">> ¡{target_unit.name} ha sido curado por {heal_amount} PV! (Vida actual: {target_unit.health})")
            if target_unit.owner_id == 0:
                try:
                    from src.domain.mission_manager import MissionManager
                    MissionManager.track_heal(0, heal_amount, getattr(target_unit, 'groups', ''))
                except Exception:
                    pass
        return True

    @staticmethod
    def _spell_34_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        target_unit.temporary_buffs.append({"type": "attack", "amount": 3, "duration": 2})
        print(f">> ¡{target_unit.name} obtiene +3 de daño por 2 turnos!")
        return True

    @staticmethod
    def _spell_35_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        tags = str(getattr(target_unit, 'groups', '')).lower()
        amount = -2 if 'Tecnológicos' in tags or 'Tecnológicos' in tags else -4
        
        target_unit.temporary_buffs.append({"type": "attack", "amount": amount, "duration": 1})
        print(f">> ¡{target_unit.name} pierde {abs(amount)} de daño este turno!")
        return True

    @staticmethod
    def _spell_36_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        target_unit.temporary_buffs.append({"type": "attack", "amount": 3, "duration": 1})
        tags = str(getattr(target_unit, 'groups', '')).lower()
        if 'futbolero' in tags:
            target_unit.temporary_buffs.append({"type": "draw_on_kill", "duration": 1})
        print(f">> ¡{target_unit.name} obtiene +3 de daño este turno! (Si elimina una unidad, robas 1 carta).")
        return True

    @staticmethod
    def _spell_37_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        target_unit.temporary_buffs.append({"type": "speed_set", "value": 0, "duration": 2})
        print(f">> ¡La velocidad de {target_unit.name} se redujo a 0 por un turno!")
        return True

    @staticmethod
    def _spell_38_effect(card, target, game_state):
        # Curar 4, si es Danza o Músico, mueve 1 casilla
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        heal_amount = 4
        player = game_state.players[target_unit.owner_id]
        if getattr(player, 'cant_heal_turns', 0) > 0:
            print(f">> [!] {player.name} está bajo un efecto que impide la curación.")
        else:
            target_unit.health = min(target_unit.max_health, target_unit.health + heal_amount)
            print(f">> ¡{target_unit.name} ha sido curado por {heal_amount} PV! (Vida actual: {target_unit.health})")
            if target_unit.owner_id == 0:
                try:
                    from src.domain.mission_manager import MissionManager
                    MissionManager.track_heal(0, heal_amount, getattr(target_unit, 'groups', ''))
                except Exception:
                    pass
        
        tags = str(getattr(target_unit, 'groups', ''))
        if 'Danza' in tags or 'Música' in tags:
            fx, fy = target
            
            player = game_state.players[target_unit.owner_id]
            if getattr(player, 'is_ai', False):
                dx = 1 if target_unit.owner_id == 0 else -1
                if game_state.board.is_within_bounds(fx + dx, fy) and not game_state.board.is_occupied(fx + dx, fy):
                    tx, ty = fx + dx, fy
                    game_state.board.move_unit(fx, fy, tx, ty)
                    print(f">> {target_unit.name} se movió a ({tx}, {ty}).")
                    return True
                return False
            else:
                game_state.pending_ability = {
                    'ability': 'encore',
                    'unit_coords': (fx, fy),
                    'unit_name': target_unit.name
                }
                print(f">> [Farmeo de aura!] Selecciona la casilla a la que moverás a {target_unit.name} (Distancia máx 1).")
                return True
        else:
            print(">> [!] La unidad seleccionada no es Danza ni Música.")
        return False

    @staticmethod
    def _spell_39_effect(card, target, game_state):
        # Cura 1 por cada 3_NAI o Derma-patch a la base.
        count = 0
        player_id = game_state.current_player_id
        for y in range(game_state.board.height):
            for x in range(game_state.board.width):
                ally = game_state.board.get_unit_at(x, y)
                if ally and ally.owner_id == player_id:
                    tags = str(getattr(ally, 'groups', '')).lower()
                    
                    # CORRECCIÓN: Buscamos todo en minúsculas
                    if '3_nai' in tags or 'derma-patch' in tags:
                        count += 1
        
        if count > 0:
            player = game_state.get_current_player()
            if getattr(player, 'cant_heal_turns', 0) > 0:
                print(f">> [!] {player.name} está bajo un efecto que impide la curación. No se curó la base.")
            else:
                player.health += count
                print(f">> [Tik-Toks] Curó {count} PV a tu Base. Vida de la base: {player.health}")
        else:
            print(">> [Tik-Toks] No tienes aliados 3_NAI o Dermapatch en el tablero. No curó nada.")
        return True

    @staticmethod
    def _spell_40_effect(card, target, game_state):
        # Mira las 3 primeras cartas del mazo. Puedes poner una unidad de coste 3 o menos en tu mano.
        player = game_state.get_current_player()
        if not player.deck:
            print(">> Tu mazo está vacío.")
            return False
            
        top_cards = player.deck[:3]
        valid_indices = []
        
        print(">> Cartas en el tope del mazo:")
        for i, c in enumerate(top_cards):
            print(f"[{i}] {c.name} (Tipo: {c.card_type}, Coste: {c.cost})")
            if c.card_type.lower() == 'unit' and int(c.cost) <= 3:
                valid_indices.append(i)
                
        if not valid_indices:
            print(">> No hay unidades de coste 3 o menos entre las opciones.")
            return False # Efecto falló: no hay cartas válidas
            
        if getattr(player, 'is_ai', False):
            # AI logic: take the first valid one
            chosen = valid_indices[0]
        else:
            print(">> [UI Móvil] TODO: Mostrar popup con estas opciones para que el jugador elija.")
            print(">> [Auto-resolución por ahora] Seleccionando la primera opción automáticamente.")
            chosen = valid_indices[0]
                
        drawn_card = top_cards[chosen]
        player.deck.remove(drawn_card)
        player.hand.append(drawn_card)
        print(f">> Has añadido {drawn_card.name} a tu mano.")
        return True

    @staticmethod
    def _spell_41_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        player = game_state.players[target_unit.owner_id]
        if getattr(player, 'cant_heal_turns', 0) == 0:
            target_unit.health = min(target_unit.max_health, target_unit.health + 12)
            print(f">> ¡{target_unit.name} ha sido curado por 12 PV! (Vida actual: {target_unit.health})")
            if target_unit.owner_id == 0:
                try:
                    from src.domain.mission_manager import MissionManager
                    MissionManager.track_heal(0, 12, getattr(target_unit, 'groups', ''))
                except Exception:
                    pass
        else:
            print(f">> [!] {player.name} está bajo un efecto que impide la curación.")
        
        tags = str(getattr(target_unit, 'groups', '')).lower()
        if 'Derma-patch' in tags or 'Derma-patch' in tags:
            target_unit.temporary_buffs.append({"type": "attack", "amount": 2, "duration": 1})
            print(f">> ¡Al ser Derma-patch, gana +2 de daño este turno!")
            
        return True

    @staticmethod
    def _spell_42_effect(card, target, game_state):
        # Todos enemigos pierden 2 PV. Si son 3 o más enemigos, pierden 3.
        enemy_id = 1 - game_state.current_player_id
        enemies_on_board = []
        for y in range(game_state.board.height):
            for x in range(game_state.board.width):
                u = game_state.board.get_unit_at(x, y)
                if u and u.owner_id == enemy_id:
                    enemies_on_board.append((x, y, u))
        
        damage = 3 if len(enemies_on_board) >= 3 else 2
        print(f">> [Reacción Explosiva] Hay {len(enemies_on_board)} enemigos. Todos recibirán {damage} de daño.")
        
        for x, y, u in enemies_on_board:
            murio = u.take_damage(damage, game_state)
            if game_state.current_player_id == 0:
                try:
                    from src.domain.mission_manager import MissionManager
                    MissionManager.track_damage(0, damage, getattr(card, 'groups', ''))
                    if murio:
                        MissionManager.track_kill(0, getattr(card, 'groups', ''), getattr(u, 'groups', ''))
                except Exception:
                    pass
            if murio:
                print(f">> ¡{u.name} ha sido destruido por la explosión!")
                game_state.board.remove_unit(x, y)
        return True

    @staticmethod
    def _spell_43_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        player = game_state.players[target_unit.owner_id]
        if getattr(player, 'cant_heal_turns', 0) == 0:
            target_unit.health = min(target_unit.max_health, target_unit.health + 4)
            print(f">> ¡{target_unit.name} ha sido curado por 4 PV! (Vida actual: {target_unit.health})")
            if target_unit.owner_id == 0:
                try:
                    from src.domain.mission_manager import MissionManager
                    MissionManager.track_heal(0, 4, getattr(target_unit, 'groups', ''))
                except Exception:
                    pass
        else:
            print(f">> [!] {player.name} está bajo un efecto que impide la curación.")
        
        target_unit.temporary_buffs.append({"type": "attack", "amount": -3, "duration": 1})
        print(f">> [Chapuline] ¡{target_unit.name} pierde 3 de daño este turno!")
        return True

    @staticmethod
    def _spell_44_effect(card, target, game_state):
        # Roba 2 cartas. Si tienes 7 o más en mano, roba 1.
        player = game_state.get_current_player()
        print(f">> DIAGNÓSTICO: Cartas en mazo={len(player.deck)}, Cartas en mano={len(player.hand)}") # <-- AGREGA ESTO
        
        cards_to_draw = 1 if len(player.hand) >= 7 else 2
        drawn_count = 0
        
        for _ in range(cards_to_draw):
            if player.deck and len(player.hand) < 10:
                drawn_card = player.deck.pop(0)
                player.hand.append(drawn_card)
                drawn_count += 1
                print(f">> [Robo Disimulado] Robaste: {drawn_card.name}")
        
        if drawn_count == 0:
            print(">> No pudiste robar cartas (mazo vacío o mano llena).")
            
        return True


    @staticmethod
    def _spell_45_effect(card, target, game_state):
        # Roba 2 cartas. Si controlas 2 o más Futboleros, roba 1 carta adicional.
        player = game_state.get_current_player()
        
        futbolero_count = 0
        for y in range(game_state.board.height):
            for x in range(game_state.board.width):
                ally = game_state.board.get_unit_at(x, y)
                if ally and ally.owner_id == player.id:
                    tags = str(getattr(ally, 'groups', '')).lower()
                    if 'Futboleros' in tags:
                        futbolero_count += 1
                        
        cards_to_draw = 3 if futbolero_count >= 2 else 2
        drawn_count = 0
        
        for _ in range(cards_to_draw):
            if player.deck and len(player.hand) < 10:
                drawn_card = player.deck.pop(0)
                player.hand.append(drawn_card)
                drawn_count += 1
                print(f">> [Combo de cartas] Robaste: {drawn_card.name}")
                
        return True

    @staticmethod
    def _spell_46_effect(card, target, game_state):
        # Normalizar target (soporta tuplas y listas [x, y])
        if isinstance(target, list):
            target = tuple(target)
        if not isinstance(target, tuple) or len(target) < 2:
            return False

        tx, ty = target
        target_unit = game_state.board.get_unit_at(tx, ty)

        # 1. Validar que la casilla no esté vacía PRIMERO
        if not target_unit:
            print(">> [Expulsión de clase] Debes seleccionar una unidad en el tablero.")
            return False

        # 2. Impedir seleccionar unidades propias
        if target_unit.owner_id == game_state.current_player_id:
            print(">> [Expulsión de clase] No puedes destruir una unidad aliada.")
            return False

        effective_attack = game_state.get_effective_stats(target_unit)["attack"]

        # 3. Validar tope de ataque (12 o 9 según corresponda)
        if effective_attack <= 12:
            print(f">> [Expulsión de clase] ¡{target_unit.name} (ATK: {effective_attack}) ha sido destruida!")
            
            # Guardar tags para las Misiones Diarias
            victim_tags = str(getattr(target_unit, 'groups', '')).lower()
            
            game_state.board.remove_unit(tx, ty)

            # Notificar la baja al tracker
            from domain.mission_manager import MissionManager
            MissionManager.track_kill(
                killer_player_id=game_state.current_player_id,
                killer_tags="hechizo",
                victim_tags=victim_tags
            )
            return True
        else:
            print(f">> [Expulsión de clase] {target_unit.name} tiene más de 12 de ataque ({effective_attack}). Inmune.")
            return False

    @staticmethod
    def _spell_47_effect(card, target, game_state):
        # Todos los aliados ganan +2 daño este turno.
        player_id = game_state.current_player_id
        count = 0
        for y in range(game_state.board.height):
            for x in range(game_state.board.width):
                ally = game_state.board.get_unit_at(x, y)
                if ally and ally.owner_id == player_id:
                    ally.temporary_buffs.append({"type": "attack", "amount": 2, "duration": 1})
                    count += 1
                    
        print(f">> [Charla Vocacional] {count} aliados ganaron +2 de daño este turno.")
        return True

    @staticmethod
    def _spell_48_effect(card, target, game_state):
        # Cafe Frio: +1 velocidad este turno. Si no es Tralaleros, debuff de -1 velocidad el siguiente turno.
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        target_unit.temporary_buffs.append({"type": "speed", "amount": 1, "duration": 1})
        print(f">> [Cafe Frio] {target_unit.name} gana +1 de velocidad este turno.")
        
        tags = str(getattr(target_unit, 'groups', '')).lower()
        if 'Tralaleros' not in tags:
            # Debuff para el siguiente turno
            target_unit.temporary_buffs.append({"type": "speed", "amount": -1, "duration": 1, "delay": 1})
            print(f">> [Cafe Frio] Al no ser Tralaleros, {target_unit.name} perderá 1 de velocidad el próximo turno (Subidón de azúcar).")
            
        return True

    @staticmethod
    def _spell_49_effect(card, target, game_state):
        # Almuerzo Pesado: El rival no puede curar durante 2 turnos.
        enemy_id = 1 - game_state.current_player_id
        enemy = game_state.players[enemy_id]
        enemy.cant_heal_turns = 2
        print(f">> [Almuerzo Pesado] El jugador {enemy.name} no podrá curar a sus unidades ni a su base por los próximos 2 turnos.")
        return True

    @staticmethod
    def _spell_50_effect(card, target, game_state):
        # Escuadrón Paramédico: Si tiene 2 aliados adyacentes, cura 15 PV.
        if not isinstance(target, tuple): return False
        tx, ty = target
        target_unit = game_state.board.get_unit_at(tx, ty)
        if not target_unit: return False
        
        adj_count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                nx, ny = tx + dx, ty + dy
                if game_state.board.is_within_bounds(nx, ny):
                    u = game_state.board.get_unit_at(nx, ny)
                    if u and u.owner_id == target_unit.owner_id:
                        adj_count += 1
                        
        if adj_count >= 2:
            player = game_state.players[target_unit.owner_id]
            if getattr(player, 'cant_heal_turns', 0) == 0:
                target_unit.health = min(target_unit.max_health, target_unit.health + 15)
                print(f">> [Escuadrón Paramédico] {target_unit.name} ha sido curado por 15 PV por tener {adj_count} aliados cerca. Vida actual: {target_unit.health}")
                if target_unit.owner_id == 0:
                    try:
                        from src.domain.mission_manager import MissionManager
                        MissionManager.track_heal(0, 15, getattr(target_unit, 'groups', ''))
                    except Exception:
                        pass
            else:
                print(f">> [!] {player.name} está bajo un efecto que impide la curación.")
        else:
            print(f">> [Escuadrón Paramédico] {target_unit.name} solo tiene {adj_count} aliados cerca. El efecto falla.")
        return True

    @staticmethod
    def _spell_51_effect(card, target, game_state):
        # Daiaodama: Selecciona unidad, ataque de 7 daño a enemigo en rango 3.
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        fx, fy = target
        print(f">> [Daiaodama] {target_unit.name} se prepara para lanzar un gran ataque (Rango 3, Daño 7).")
        
        game_state.pending_ability = {
            'ability': 'daiaodama',
            'source_coords': (fx, fy)
        }
        print(">> [Daiaodama] Selecciona una unidad enemiga a 3 casillas o menos.")
        return True

    @staticmethod
    def _cristobal_on_enter(unit, game_state):
        # Robar carta. Si es truco, cura 4 a un aliado.
        player = game_state.players[unit.owner_id]
        if player.deck:
            drawn_card = player.deck.pop(0)
            player.hand.append(drawn_card)
            print(f">> [Habilidad Cristobal]: Robaste {drawn_card.name}")
            if drawn_card.card_type.lower() in ('spell', 'trick'):
                # Curación de 4 a un aliado. Por simplicidad, se cura a sí mismo por ahora.
                if getattr(player, 'cant_heal_turns', 0) == 0:
                    unit.health += 4
                    print(f">> ¡La carta es un truco! Cristobal se curó 4 HP. Vida actual: {unit.health}")
                else:
                    print(">> [!] El jugador no puede ser curado.")
        else:
            print(">> [Habilidad Cristobal]: Mazo vacío, no se puede robar.")

    @staticmethod
    def _josefa_g_on_enter(unit, game_state):
        # Mirar 3 cartas del mazo enemigo, poner 1 al fondo.
        enemy_id = 1 - unit.owner_id
        enemy = game_state.players[enemy_id]
        if len(enemy.deck) > 0:
            top_cards = enemy.deck[:3]
            print(">> [Habilidad Najib]: Cartas en el tope del mazo enemigo:")
            for i, c in enumerate(top_cards):
                print(f"[{i}] {c.name}")
            
            player = game_state.players[unit.owner_id]
            if getattr(player, 'is_ai', False):
                card_to_bottom = top_cards.pop(0)
                enemy.deck.remove(card_to_bottom)
                enemy.deck.append(card_to_bottom)
                print(f">> {card_to_bottom.name} enviada al fondo del mazo enemigo.")    
            else:
                print(">> [UI Móvil] TODO: Mostrar popup con las 3 cartas y elegir 1.")
                print(">> [Auto-resolución por ahora] Eligiendo la primera carta automáticamente.")
                card_to_bottom = top_cards.pop(0)
                enemy.deck.remove(card_to_bottom)
                enemy.deck.append(card_to_bottom)
                print(f">> {card_to_bottom.name} enviada al fondo del mazo enemigo.")
        
    @staticmethod
    def _crisby_on_enter(unit, game_state):
        # Crisby enciende la bandera de descuento para su jugador
        player = game_state.players[unit.owner_id]
        player.crisby_cost_reduction_active = True 
        print(f">> [Habilidad Crisby]: Tu próxima carta de coste 4 o menos costará 1 menos este turno.")

    @staticmethod
    def _josefa_a_on_enter(unit, game_state):
        print(">> [Habilidad Josefa A]: Buscando aliado para proteger...")
        game_state.pending_ability = {
            'ability': 'josefa_a',
            'owner_id': unit.owner_id
        }
        print(">> [Josefa A] Selecciona un aliado para darle Escudo.")

    @staticmethod
    def _richi_on_enter(unit, game_state):
        # Escudo a si mismo
        unit.has_shield = True
        print(f">> ¡{unit.name} ha recibido un Escudo (mitad de daño en el próximo ataque)!")

    @staticmethod
    def _kapsi_on_attack(unit, game_state):
        print(f">> [Habilidad Kapsi]: Reubicación táctica activada.")
        pos = None
        for y in range(5):
            for x in range(6):
                if game_state.board.get_unit_at(x, y) is unit:
                    pos = (x, y)
                    break
            if pos: break
            
        if not pos: return
        fx, fy = pos
        game_state.pending_ability = {
            'ability': 'kapsi_retreat',
            'unit_coords': (fx, fy)
        }
        print(">> [Kapsi] Selecciona una casilla adyacente para retirarte.")

    @staticmethod
    def _amira_presidenta_on_attack(unit, game_state):
        # Da +1 de daño a todas las unidades aliadas
        unit.static_abilities.append({"type": "buff_all_attack", "amount": 1})

    @staticmethod
    def _stefano_on_activate(unit, game_state):
        if getattr(unit, 'ability_used_this_turn', False):
            print(">> [Habilidad Stefano]: Stefano ya usó su habilidad este turno.")
            return

        if unit.health > 1:
            unit.health -= 1
            unit.attack += 1
            unit.ability_used_this_turn = True
            print(f">> [Habilidad Stefano]: Stefano sacrificó 1 HP. ATK actual: {unit.attack}, HP actual: {unit.health}")
        else:
            print(">> [Habilidad Stefano]: Stefano no tiene suficiente vida para sacrificar.")

    @staticmethod
    def _jose_enmascarado_on_attack(unit, game_state):
        unit.attack = max(1, unit.attack // 2) # Reduce el daño base a la mitad, mínimo 1
        
        # Después de su primer ataque, su rango de ataque vuelve a 1
        if getattr(unit, 'range_atk', 1) > 1:
            unit.range_atk = 1
        
        print(f">> [Habilidad Jose Enmascarado]: Efecto post-ataque. Daño reducido a {unit.attack}. Rango ajustado a {unit.range_atk}.")

    @staticmethod
    def _chino_quemadas_on_damage_received(unit, damage, game_state):
        if getattr(unit, 'ability_used_this_turn', False):
            return damage
        
        # Definimos el origen (donde está Chino ahora) 
        pos = None
        for y in range(5):
            for x in range(6):
                if game_state.board.get_unit_at(x, y) is unit:
                    pos = (x, y)
                    break
            if pos: break

        if not pos:
            return damage # Por si acaso no se encuentra
            
        fx, fy = pos # ¡Ahora sí tenemos fx y fy!
        effective_speed = game_state.get_effective_stats(unit)["speed"]

        # --- Lógica de Decisión ---
        tx, ty = None, None

        player = game_state.players[unit.owner_id]
        if getattr(player, 'is_ai', False):
            # LA IA BUSCA ESCAPAR: Busca la primera casilla válida en su rango de velocidad
            print(f">> [IA] Chino Quemadas está calculando una ruta de escape...")
            for dx in range(-effective_speed, effective_speed + 1):
                for dy in range(-effective_speed, effective_speed + 1):
                    temp_tx, temp_ty = fx + dx, fy + dy
                    dist = abs(fx - temp_tx) + abs(fy - temp_ty)
                    
                    if dist <= effective_speed and dist > 0:
                        if game_state.board.is_within_bounds(temp_tx, temp_ty) and not game_state.board.is_occupied(temp_tx, temp_ty):
                            tx, ty = temp_tx, temp_ty
                            break # Encontró un lugar y se escapa
                if tx is not None: break
                
            if tx is not None and ty is not None:
                game_state.board.move_unit(fx, fy, tx, ty)
                print(f">> ¡ESQUIVA! Chino se movió a ({tx}, {ty}) y anuló los {damage} de daño.")
                unit.ability_used_this_turn = True
                return 0
        else:
            # JUGADOR HUMANO
            game_state.pending_ability = {
                'ability': 'chino_quemadas',
                'unit_coords': (fx, fy),
                'speed': effective_speed
            }
            print(f">> [Habilidad Chino Quemadas]: ¡Recibiste daño! Selecciona una casilla para esquivar (anula daño).")
            AudioManager.play_sfx('quemadasdodge')
            unit.ability_used_this_turn = True
            return 0
        
        return damage
    @staticmethod
    def _STEAM_on_turn_start(unit, game_state):
        for unit in game_state.board.get_all_units(unit.owner_id):
            if "Derma-patch" in unit.groups and unit.health < unit.max_health: 
                unit.health = min(unit.max_health, unit.health + 2)
                print(f">> [Habilidad STEAM]: {unit.name} ha recibido 2 HP de curación.")
                if unit.owner_id == 0:
                    try:
                        from src.domain.mission_manager import MissionManager
                        MissionManager.track_heal(0, 2, getattr(unit, 'groups', ''))
                    except Exception:
                        pass
    
    @staticmethod
    def _nico_on_turn_start(unit, game_state):
        if getattr(unit, 'immobile_turns', 0) > 0:
            print(f">> [Habilidad Nico]: {unit.name} tiene {unit.immobile_turns} turnos de parálisis restantes.")
            if unit.immobile_turns == 0:
                print(f">> [Habilidad Nico]: {unit.name} se ha recuperado de la parálisis.")
    
    @staticmethod
    def _sofi_on_turn_start(unit, game_state):
        for nx, ny in game_state.board.get_neighbors(unit.pos_x, unit.pos_y):
            target = game_state.board.get_unit_at(nx, ny)
            if target and target.owner_id == unit.owner_id and target.health < target.max_health:
                target.health = min(target.max_health, target.health + 1)
                print(f">> [Habilidad Sofi]: {target.name} ha recibido 1 HP de curación.")
                if unit.owner_id == 0:
                    try:
                        from src.domain.mission_manager import MissionManager
                        MissionManager.track_heal(0, 1, getattr(target, 'groups', ''))
                    except Exception:
                        pass
                break
                
    @staticmethod
    def _iara_on_damage_received(unit, damage, game_state):
        count = sum(1 for u in game_state.board.get_all_units() if "Tralaleros" in u.groups)
        if count >= 2:
            return max(0, damage - 2)
        return damage
    
    @staticmethod
    def _daniela_on_attack(unit, game_state):
        # Habilidad: Si el objetivo tiene más vida que ella, gana +2 de daño
        # Como no tenemos el objetivo específico aquí, verificamos si hay enemigos más fuertes cerca
        enemy_id = 1 - unit.owner_id
        enemies = game_state.board.get_all_units(enemy_id)
        stronger_enemies = [e for e in enemies if e.health > unit.health]
        if stronger_enemies:
            unit.attack += 2
            print(f">> [Habilidad Daniela]: {unit.name} ha ganado +2 de daño (objetivo más fuerte detectado).") 

    @staticmethod
    def _dante_economista_main_ability(unit, game_state):
        player = game_state.get_current_player()
        player.d_economia_cost_reduction_active = True
    
    @staticmethod
    def _martina_nueva_on_enter(unit, game_state):
        # Da +3 de vida máxima a TODAS las unidades aliadas
        for u in game_state.board.get_all_units():
            if u.id != unit.id and u.owner_id == unit.owner_id: # No modificarse a sí misma y no curar a enemigos
                u.max_health += 3
                u.health = min(u.max_health, u.health + 3) # Si ya tenía vida, se la aumenta
                print(f">> [Habilidad Martina Nueva]: {u.name} ha ganado +3 de vida máxima.")
                
    @staticmethod
    def _martina_nueva_on_damage_received(unit, damage, game_state):
        # Mientras tenga al menos un aliado adyacente, reduce en 2 todo el daño recibido.
        has_adj = False
        for nx, ny in game_state.board.get_neighbors(unit.pos_x, unit.pos_y):
            adj = game_state.board.get_unit_at(nx, ny)
            if adj and adj.owner_id == unit.owner_id:
                has_adj = True
                break
        if has_adj:
            print(f">> [Habilidad Martina Nueva]: {unit.name} ha reducido el daño recibido en 2.")
            return max(0, damage - 2)
        return damage

    @staticmethod
    def _nico_on_activate(unit, game_state):
        if unit.immobile_turns == 0:
            unit.immobile_turns = 2
            unit.attack += 3
            print(f">> [Habilidad Nico]: {unit.name} no puede moverse por 2 turnos y ha ganado +3 de daño.")
        else:
            print(f">> [Habilidad Nico]: {unit.name} no puede moverse. Ya tiene {unit.immobile_turns} turnos inmovil restantes.")
    
    @staticmethod
    def _crisby_airsoft_on_activate(unit, game_state):
        if getattr(unit, 'has_moved', False):
            print(f">> [Habilidad Crisby Airsoft]: No se puede activar debido a que ya se ha movido esta unidad.")
            return
            
        pos = None
        for y in range(game_state.board.height):
            for x in range(game_state.board.width):
                if game_state.board.get_unit_at(x, y) is unit:
                    pos = (x, y)
                    break
            if pos: break
            
        if not pos: return
        fx, fy = pos
        
        for nx, ny in game_state.board.get_neighbors(fx, fy):
            target = game_state.board.get_unit_at(nx, ny)
            if target and target.owner_id != unit.owner_id:
                target.immobile_turns = 1 
                print(f">> [Habilidad Crisby Airsoft]: {target.name} no puede moverse por 1 turno.")
                break

    @staticmethod
    def _cutino_on_activate(unit, game_state):
        player = game_state.players[unit.owner_id]
        if player.current_energy < 3: return False
        
        game_state.pending_ability = {
            'ability': 'cutino_summon',
            'source_coords': (unit.pos_x, unit.pos_y)
        }
        AudioManager.play_sfx('gundam1')
        print(">> [Cutiño] Selecciona una casilla adyacente vacía para invocar a Gandan.")
        return True

    @staticmethod
    def _zander_on_activate(unit, game_state):
        game_state.pending_ability = {
            'ability': 'zander_move_1',
            'source_coords': (unit.pos_x, unit.pos_y)
        }
        print(">> [Zander] Selecciona al aliado que quieres mover (Paso 1/2).")
        if game_state.pending_ability:
            unit.ability_used_this_turn = True
        return True

    @staticmethod
    def _dante_yukata_on_activate(unit, game_state):
        game_state.pending_ability = {
            'ability': 'dante_yukata_attack',
            'source_coords': (unit.pos_x, unit.pos_y)
        }
        eff_range = game_state.get_effective_stats(unit)["range_atk"]
        print(f">> [Dante Yukata] Selecciona a un enemigo a rango {eff_range + 1} para atacar con Miku Peluche.")
        if game_state.pending_ability:
            AudioManager().play_sfx("yukatamiku")
            unit.ability_used_this_turn = True
        return True

    @staticmethod
    def _dragon_menor_on_turn_start(unit, game_state):
        unit.turns_alive = getattr(unit, 'turns_alive', 0) + 1
        
        if unit.turns_alive == 3:
            cx, cy = unit.pos_x, unit.pos_y
            target_x = 5 if unit.owner_id == 0 else 0
            
            if target_x != cx:
                occupant = game_state.board.get_unit_at(target_x, cy)
                se_puede_mover = True
                
                if occupant:
                    dx = 1 if unit.owner_id == 0 else -1
                    new_occ_x = target_x + dx
                    
                    # 1. Intentar empujar a la casilla trasera
                    if game_state.board.is_within_bounds(new_occ_x, cy) and not game_state.board.is_occupied(new_occ_x, cy):
                        game_state.board.move_unit(target_x, cy, new_occ_x, cy)
                        print(f">> [Dragón] ¡Empujó a {occupant.name} a ({new_occ_x}, {cy})!")
                    
                    # 2. Si no hay espacio, colisión y daño por aplastamiento
                    else:
                        print(f">> [Dragón] ¡Aplastó a {occupant.name} contra el límite!")
                        murio = occupant.take_damage(10, game_state)
                        
                        if murio:
                            game_state.board.remove_unit(target_x, cy)
                        else:
                            # 🛡️ BLOQUEO: Si sobrevivió, la casilla sigue ocupada. El Dragón frena.
                            se_puede_mover = False
                            print(f">> [Dragón] {occupant.name} resistió el impacto y bloqueó el avance.")
                
                # 3. Solo avanza si la casilla destino está vacía
                if se_puede_mover:
                    game_state.board.move_unit(cx, cy, target_x, cy)
                    print(">> [Dragón] ¡Se abalanzó a la fila opuesta!")

    @staticmethod
    def _gandan_on_death(unit, game_state):
        print(f">> [Gandan] ¡Gandan explotó en ({unit.pos_x}, {unit.pos_y})!")
        for nx, ny in list(game_state.board.get_neighbors(unit.pos_x, unit.pos_y)):
            target = game_state.board.get_unit_at(nx, ny)
            if target:
                murio = target.take_damage(3, game_state)
                if murio:
                    game_state.board.remove_unit(nx, ny)

    @staticmethod
    def _spell_71_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        _, ty = target
        
        has_3nai = False
        allies = []
        for x in range(game_state.board.width):
            u = game_state.board.get_unit_at(x, ty)
            if u and u.owner_id == game_state.current_player_id:
                allies.append(u)
                if '3_nai' in str(getattr(u, 'groups', '')).lower():
                    has_3nai = True
                    
        heal_amt = 7 if has_3nai else 5
        for u in allies:
            u.health = min(u.max_health, u.health + heal_amt)
            print(f">> [Tren] {u.name} se curó {heal_amt} PV.")
            if game_state.current_player_id == 0:
                try:
                    from src.domain.mission_manager import MissionManager
                    MissionManager.track_heal(0, heal_amt, getattr(u, 'groups', ''))
                except Exception:
                    pass
        return True

    @staticmethod
    def _spell_72_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        tx, ty = target
        target_unit = game_state.board.get_unit_at(tx, ty)
        if not target_unit: return False
        
        musico_count = 0
        for y in range(game_state.board.height):
            for x in range(game_state.board.width):
                u = game_state.board.get_unit_at(x, y)
                if u and u.owner_id == game_state.current_player_id:
                    if 'músico' in str(getattr(u, 'groups', '')).lower() or 'musico' in str(getattr(u, 'groups', '')).lower():
                        musico_count += 1
                        
        if musico_count > 0:
            target_unit.temporary_buffs.append({"type": "attack", "amount": musico_count, "duration": 1})
            print(f">> [Trombón] {target_unit.name} gana +{musico_count} de Ataque este turno.")
        return True

    @staticmethod
    def _rafa_on_attack(unit, game_state):
        unit.immobile_turns = 2
        print(f">> [Rafa] Debe recargar, estará inmovilizado por 1 turno.")

    @staticmethod
    def _spell_76_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        tx, ty = target
        target_unit = game_state.board.get_unit_at(tx, ty)
        if not target_unit: return False
        
        target_unit.temporary_buffs.append({"type": "attack", "amount": 2, "duration": 1})
        tags = str(getattr(target_unit, 'groups', '')).lower()
        if 'artista' in tags:
            target_unit.temporary_buffs.append({"type": "range_atk", "amount": 1, "duration": 1})
            print(f">> [Lienzo de Arte] {target_unit.name} gana +2 Ataque y +1 Rango este turno.")
        else:
            print(f">> [Lienzo de Arte] {target_unit.name} gana +2 Ataque este turno.")
        return True

    @staticmethod
    def _spell_77_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        tx, ty = target
        target_unit = game_state.board.get_unit_at(tx, ty)
        if not target_unit or target_unit.owner_id != game_state.current_player_id: 
            return False
        
        target_unit.health = min(target_unit.max_health, target_unit.health + 6)
        print(f">> [Ensayo PAES] {target_unit.name} recuperó 6 PV.")
        if target_unit.owner_id == 0:
            try:
                from src.domain.mission_manager import MissionManager
                MissionManager.track_heal(0, 6, getattr(target_unit, 'groups', ''))
            except Exception:
                pass
        
        tags = str(getattr(target_unit, 'groups', '')).lower()
        if 'literatura' in tags or 'tecnológico' in tags or 'tecnologico' in tags or 'nuevo' in tags:
            player = game_state.players[game_state.current_player_id]
            if player.deck and len(player.hand) < 10:
                drawn = player.deck.pop(0)
                player.hand.append(drawn)
                print(f">> [Ensayo PAES] ¡Robaste a {drawn.name}!")
        return True

    @staticmethod
    def _axel_on_damage_receaved(unit, game_state):
        # Gana +1 de daño al recibir daño lol
        unit.attack += 1
        print(f">> [Habilidad Axel]: {unit.name} ha ganado +1 de daño (recibió daño).")


