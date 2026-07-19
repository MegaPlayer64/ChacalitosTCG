from kivy.uix.widget import Widget
from kivy.graphics import Color, Line

class FondoCuadriculado(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Vinculamos el redibujado al cambio de tamaño o posición de la pantalla
        self.bind(size=self.actualizar_canvas, pos=self.actualizar_canvas)

    def actualizar_canvas(self, *args):
        self.canvas.before.clear() # Limpiamos dibujos anteriores
        
        with self.canvas.before:
            # 1. Color del fondo base (ej: Gris muy oscuro)
            Color(0.05, 0.05, 0.05, 1)
            from kivy.graphics import Rectangle
            Rectangle(pos=self.pos, size=self.size)
            
            # 2. Color de las líneas de la cuadrícula (Gris tenue/sutil)
            Color(0.2, 0.2, 0.2, 0.4) 
            
            tamano_cuadro = 40 # Tamaño en píxeles de cada celda
            x_inicio, y_inicio = self.pos
            ancho, alto = self.size

            # Dibujar líneas verticales
            for x in range(int(x_inicio), int(x_inicio + ancho), tamano_cuadro):
                Line(points=[x, y_inicio, x, y_inicio + alto], width=1)

            # Dibujar líneas horizontales
            for y in range(int(y_inicio), int(y_inicio + alto), tamano_cuadro):
                Line(points=[x_inicio, y, x_inicio + ancho, y], width=1)