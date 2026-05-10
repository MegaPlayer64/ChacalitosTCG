from src.domain import unit
class AbilityManager:
    @staticmethod
    def trigger_on_enter(unit, game_state):
        if int(unit.id) == 28:
            AbilityManager._cristobal_on_enter(unit, game_state)
        elif int(unit.id) == 29:
            AbilityManager._najib_on_enter(unit, game_state)
        elif int(unit.id) == 30:
            AbilityManager._crisby_on_enter(unit, game_state)
        elif int(unit.id) == 31:
            AbilityManager._josefa_a_on_enter(unit, game_state)
        elif int(unit.id) == 17:
            AbilityManager._richi_on_enter(unit, game_state)

    @staticmethod
    def trigger_on_activate(unit, game_state):
        if int(unit.id) == 62:
            AbilityManager._stefano_on_activate(unit, game_state)

    @staticmethod
    def trigger_on_attack(unit, game_state):
        if int(unit.id) == 3:
            AbilityManager._kapsi_on_attack(unit, game_state)
        elif int(unit.id) == 57:
            AbilityManager._amira_presidenta_on_attack(unit, game_state)
        elif int(unit.id) == 63:
            AbilityManager._jose_enmascarado_on_attack(unit, game_state)

    @staticmethod
    def trigger_on_damage_received(unit, damage, game_state):
        if int(unit.id) == 61:
            AbilityManager._chino_quemadas_on_damage_received(unit, damage, game_state)

    @staticmethod
    def execute_spell(card, target, game_state):
        print(f">> [Hechizo]: Ejecutando efecto de {card.name}")
        
        effect_methods = {
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
        }
        
        method = effect_methods.get(int(card.id))
        if method:
            return method(card, target, game_state)
        else:
            print(f">> [Hechizo]: Efecto para ID {card.id} no implementado.")
            return False

    @staticmethod
    def _spell_33_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        tags = str(getattr(target_unit, 'groups', '')).lower()
        heal_amount = 12 if 'fuerzas especiales valenzuela' in tags or 'cabezal de tren' in tags else 10
        
        player = game_state.players[target_unit.owner_id]
        if getattr(player, 'cant_heal_turns', 0) > 0:
            print(f">> [!] {player.name} está bajo un efecto que impide la curación.")
        else:
            target_unit.health = min(target_unit.max_health, target_unit.health + heal_amount)
            print(f">> ¡{target_unit.name} ha sido curado por {heal_amount} PV! (Vida actual: {target_unit.health})")
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
        amount = -2 if 'tecnológico' in tags or 'tecnologico' in tags else -4
        
        target_unit.temporary_buffs.append({"type": "attack", "amount": amount, "duration": 1})
        print(f">> ¡{target_unit.name} pierde {abs(amount)} de daño este turno!")
        return True

    @staticmethod
    def _spell_36_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        target_unit.temporary_buffs.append({"type": "attack", "amount": 3, "duration": 1})
        target_unit.temporary_buffs.append({"type": "draw_on_kill", "duration": 1})
        print(f">> ¡{target_unit.name} obtiene +3 de daño este turno! (Si elimina una unidad, robas 1 carta).")
        return True

    @staticmethod
    def _spell_37_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        target_unit.temporary_buffs.append({"type": "speed_set", "value": 0, "duration": 1})
        print(f">> ¡La velocidad de {target_unit.name} se redujo a 0 por un turno!")
        return True

    @staticmethod
    def _spell_38_effect(card, target, game_state):
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        tags = str(getattr(target_unit, 'groups', '')).lower()
        if 'danza' in tags or 'musica' in tags or 'música' in tags:
            fx, fy = target
            tx, ty = None, None
            
            player = game_state.players[target_unit.owner_id]
            if getattr(player, 'is_ai', False):
                dx = 1 if target_unit.owner_id == 0 else -1
                if game_state.board.is_within_bounds(fx + dx, fy) and not game_state.board.is_occupied(fx + dx, fy):
                    tx, ty = fx + dx, fy
            else:
                print(f">> [Encore!] Mueve a {target_unit.name} 1 casilla extra.")
                try:
                    tx = int(input("Nueva posición X: "))
                    ty = int(input("Nueva posición Y: "))
                except ValueError: return False

            if tx is not None and game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty):
                dist = abs(fx - tx) + abs(fy - ty)
                if dist <= 1:
                    game_state.board.move_unit(fx, fy, tx, ty)
                    print(f">> {target_unit.name} se movió a ({tx}, {ty}).")
                    return True
                else:
                    print(">> [!] Distancia mayor a 1.")
        else:
            print(">> [!] La unidad seleccionada no es Danza ni Música.")
        return False

    @staticmethod
    def _spell_39_effect(card, target, game_state):
        # Cura 1 por cada 3_NAI o Dermapatch a la base.
        count = 0
        player_id = game_state.current_player_id
        for y in range(game_state.board.height):
            for x in range(game_state.board.width):
                ally = game_state.board.get_unit_at(x, y)
                if ally and ally.owner_id == player_id:
                    tags = str(getattr(ally, 'groups', '')).lower()
                    if '3_nai' in tags or 'dermapatch' in tags or 'derma-patch' in tags:
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
            return True # Efecto jugado pero sin éxito
            
        if getattr(player, 'is_ai', False):
            # AI logic: take the first valid one
            chosen = valid_indices[0]
        else:
            try:
                choice = input("Selecciona el índice de la unidad a robar (o presiona Enter para omitir): ")
                if not choice.strip():
                    return True
                chosen = int(choice)
                if chosen not in valid_indices:
                    print(">> Selección inválida. Omite el robo.")
                    return True
            except ValueError:
                return True
                
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
        else:
            print(f">> [!] {player.name} está bajo un efecto que impide la curación.")
        
        tags = str(getattr(target_unit, 'groups', '')).lower()
        if 'dermapatch' in tags or 'derma-patch' in tags:
            target_unit.temporary_buffs.append({"type": "attack", "amount": 2, "duration": 1})
            print(f">> ¡Al ser Dermapatch, gana +2 de daño este turno!")
            
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
        else:
            print(f">> [!] {player.name} está bajo un efecto que impide la curación.")
        
        target_unit.temporary_buffs.append({"type": "attack", "amount": -3, "duration": 1})
        print(f">> [Chapuline] ¡{target_unit.name} pierde 3 de daño este turno!")
        return True

    @staticmethod
    def _spell_44_effect(card, target, game_state):
        # Roba 2 cartas. Si tienes 7 o más en mano, roba 1.
        player = game_state.get_current_player()
        
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
                    if 'futbolero' in tags:
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
        # Destruye una unidad con 12 o menos de ataque.
        if not isinstance(target, tuple): return False
        tx, ty = target
        target_unit = game_state.board.get_unit_at(tx, ty)
        if not target_unit: return False
        
        effective_attack = game_state.get_effective_stats(target_unit)["attack"]
        
        if effective_attack <= 12:
            print(f">> [Expulsión de clase] ¡{target_unit.name} (ATK: {effective_attack}) ha sido destruida!")
            game_state.board.remove_unit(tx, ty)
        else:
            print(f">> [Expulsión de clase] {target_unit.name} tiene más de 12 de ataque ({effective_attack}). Inmune al efecto.")
        return True

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
        # Cafe Frio: +1 velocidad este turno. Si no es Tralalero Tralala, debuff de -1 velocidad el siguiente turno.
        if not isinstance(target, tuple): return False
        target_unit = game_state.board.get_unit_at(*target)
        if not target_unit: return False
        
        target_unit.temporary_buffs.append({"type": "speed", "amount": 1, "duration": 1})
        print(f">> [Cafe Frio] {target_unit.name} gana +1 de velocidad este turno.")
        
        tags = str(getattr(target_unit, 'groups', '')).lower()
        if 'tralalero tralala' not in tags:
            # Debuff para el siguiente turno
            target_unit.temporary_buffs.append({"type": "speed", "amount": -1, "duration": 1, "delay": 1})
            print(f">> [Cafe Frio] Al no ser Tralalero Tralala, {target_unit.name} perderá 1 de velocidad el próximo turno (Subidón de azúcar).")
            
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
        
        ex, ey = None, None
        player = game_state.players[target_unit.owner_id]
        if getattr(player, 'is_ai', False):
            # Buscar enemigo en rango 3
            enemy_id = 1 - target_unit.owner_id
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    nx, ny = fx + dx, fy + dy
                    if max(abs(dx), abs(dy)) <= 3 and game_state.board.is_within_bounds(nx, ny):
                        u = game_state.board.get_unit_at(nx, ny)
                        if u and u.owner_id == enemy_id:
                            ex, ey = nx, ny
                            break
                if ex is not None: break
        else:
            try:
                ex = int(input("Enemigo Objetivo X: "))
                ey = int(input("Enemigo Objetivo Y: "))
            except ValueError:
                print(">> Coordenadas inválidas. Falla el hechizo.")
                return False
                
        if ex is not None and game_state.board.is_within_bounds(ex, ey):
            enemy_unit = game_state.board.get_unit_at(ex, ey)
            dist = max(abs(fx - ex), abs(fy - ey))
            if enemy_unit and enemy_unit.owner_id != target_unit.owner_id and dist <= 3:
                murio = enemy_unit.take_damage(7, game_state)
                if murio:
                    print(f">> ¡{enemy_unit.name} ha sido destruido por Daiaodama!")
                    game_state.board.remove_unit(ex, ey)
                return True
            else:
                print(">> [!] Objetivo inválido o fuera de rango (Máximo 3).")
        return False

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
    def _najib_on_enter(unit, game_state):
        # Mirar 3 cartas del mazo enemigo, poner 1 al fondo.
        enemy_id = 1 - unit.owner_id
        enemy = game_state.players[enemy_id]
        if len(enemy.deck) > 0:
            top_cards = enemy.deck[:3]
            print(">> [Habilidad Najib]: Cartas en el tope del mazo enemigo:")
            for i, c in enumerate(top_cards):
                print(f"[{i}] {c.name}")
            
            try:
                choice = int(input("Selecciona el índice de la carta a poner al fondo: "))
                if 0 <= choice < len(top_cards):
                    card_to_bottom = top_cards.pop(choice)
                    enemy.deck.remove(card_to_bottom)
                    enemy.deck.append(card_to_bottom)
                    print(f">> {card_to_bottom.name} enviada al fondo del mazo enemigo.")
                else:
                    print(">> Selección inválida, se omite el efecto.")
            except ValueError:
                print(">> Entrada inválida, se omite el efecto.")
    
    @staticmethod
    def _crisby_on_enter(unit, game_state):
        # Próxima carta coste 4 o menos cuesta 1 menos este turno
        player = game_state.players[unit.owner_id]
        # Dejamos la variable lista para ser leída por el sistema de maná
        player.cost_reduction_active = True 
        print(f">> [Habilidad Crisby]: Tu próxima carta de coste 4 o menos costará 1 menos este turno.")

    @staticmethod
    def _josefa_a_on_enter(unit, game_state):
        print(">> [Habilidad Josefa A]: Buscando aliado para proteger...")
        target = None

        player = game_state.players[unit.owner_id]
        if getattr(player, 'is_ai', False):
            # La IA busca al aliado con más vida para hacerlo un "tanque"
            aliados = [u for u in game_state.board.get_all_units() if u.owner_id == unit.owner_id and u != unit]
            if aliados:
                target = max(aliados, key=lambda u: u.health)
        else:
            try:
                tx = int(input("Aliado X: "))
                ty = int(input("Aliado Y: "))
                target = game_state.board.get_unit_at(tx, ty)
            except ValueError: return

        if target and target.owner_id == unit.owner_id:
            target.has_shield = True
            print(f">> ¡{target.name} recibió el Escudo de Josefa A!")
        else:
            print(">> No se encontró un aliado válido. El escudo se desperdició.")

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
                if game_state.board.get_unit_at(x, y) == unit:
                    pos = (x, y)
                    break
            if pos: break
            
        fx, fy = pos
        tx, ty = None, None

        player = game_state.players[unit.owner_id]
        if getattr(player, 'is_ai', False):
            # La IA de Kapsi busca una casilla vacía cerca para retroceder
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = fx + dx, fy + dy
                    if game_state.board.is_within_bounds(nx, ny) and not game_state.board.is_occupied(nx, ny):
                        tx, ty = nx, ny
                        break
        else:
            try:
                tx = int(input("Nueva posición X: "))
                ty = int(input("Nueva posición Y: "))
            except ValueError: return

        if tx is not None and game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty):
            game_state.board.move_unit(fx, fy, tx, ty)
            print(f">> Kapsi se retiró a ({tx}, {ty})")

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
                if game_state.board.get_unit_at(x, y) == unit:
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
                    
                    # Usamos tus validaciones del board
                    if dist <= effective_speed and dist > 0:
                        if game_state.board.is_within_bounds(temp_tx, temp_ty) and not game_state.board.is_occupied(temp_tx, temp_ty):
                            tx, ty = temp_tx, temp_ty
                            break # Encontró un lugar y se escapa
                if tx is not None: break
        else:
            # JUGADOR HUMANO
            print(f">> [Habilidad Chino Quemadas]: ¡Recibiste daño! ¿Quieres moverte para anularlo?")
            try:
                if input("¿Moverse? (y/n): ").lower() == 'y':
                    tx = int(input("Nueva posición X: "))
                    ty = int(input("Nueva posición Y: "))
                else:
                    return damage
            except ValueError:
                return damage

        # --- Validación Final y Ejecución ---
        if tx is not None and ty is not None:
            dist = abs(fx - tx) + abs(fy - ty)
            
            # Aquí es donde usas la lógica que ya tienes en validate_action (pero manual)
            if game_state.board.is_within_bounds(tx, ty) and not game_state.board.is_occupied(tx, ty) and dist <= effective_speed:
                game_state.board.move_unit(fx, fy, tx, ty)
                print(f">> ¡ESQUIVA! Chino se movió a ({tx}, {ty}) y anuló los {damage} de daño.")
                unit.ability_used_this_turn = True
                return 0
            else:
                print(">> [!] Movimiento de evasión inválido. Chino recibió el impacto.")
        
        return damage