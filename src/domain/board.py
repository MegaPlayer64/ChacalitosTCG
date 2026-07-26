# src/domain/models/board.py

class Board:
    def __init__(self, width=6, height=5):
        self.width = width
        self.height = height
        # Diccionario para acceso rápido: (x, y) -> Unit
        self.grid = {}

    def is_within_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_occupied(self, x, y):
        return (x, y) in self.grid

    def get_unit_at(self, x, y):
        return self.grid.get((x, y))

    def set_unit_at(self, x, y, unit):
        if self.is_within_bounds(x, y):
            self.grid[(x, y)] = unit
            unit.pos_x, unit.pos_y = x, y

    def remove_unit(self, x, y):
        if (x, y) in self.grid:
            del self.grid[(x, y)]

    def move_unit(self, from_x, from_y, to_x, to_y):
        unit = self.get_unit_at(from_x, from_y)
        if unit and self.is_within_bounds(to_x, to_y) and not self.is_occupied(to_x, to_y):
            self.remove_unit(from_x, from_y)
            self.set_unit_at(to_x, to_y, unit)
            return True
        return False

    def get_all_units(self, player_id=None):
        if player_id is None:
            return list(self.grid.values())
        return [unit for unit in self.grid.values() if unit.owner_id is not None and int(unit.owner_id) == int(player_id)]
    
    def get_neighbors(self, x, y):
        """Retorna las coordenadas de las casillas adyacentes (hasta 8 vecinos)."""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if self.is_within_bounds(nx, ny):
                    neighbors.append((nx, ny))
        return neighbors