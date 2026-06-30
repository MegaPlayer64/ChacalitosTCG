import json
import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from src.domain.gacha_system import GachaSystem

class TarjetaRevelada(BoxLayout):
    """Mini-componente visual para representar cada carta obtenida en el sobre"""
    def __init__(self, nombre, coste, rareza, tipo, **kwargs):
        super().__init__(orientation='vertical', padding=5, spacing=5, size_hint_x=None, width=140, **kwargs)
        
        # Color de fondo según el tipo o rareza
        if tipo == 'spell':
            color_fondo = (0.5, 0.2, 0.6, 1) # Morado para trucos
        elif tipo == 'building':
            color_fondo = (0.2, 0.5, 0.3, 1) # Verde para entornos
        else:
            # Color especial si es de Excelencia (Chino Quemadas)
            color_fondo = (0.8, 0.6, 0.2, 1) if rareza == "Excelencia" else (0.1, 0.4, 0.6, 1)

        # Botón o recuadro visual de la carta
        btn_carta = Button(
            text=f"{nombre}\n\n⚡ Coste: {coste}\n[{rareza}]",
            background_color=color_fondo,
            halign='center',
            valign='middle'
        )
        btn_carta.bind(size=btn_carta.setter('text_size')) # Ajusta el texto al tamaño del recuadro
        
        self.add_widget(btn_carta)


class PantallaBanner(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ruta_perfil = "src/data/user_profile.json"
        
        layout_principal = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 1. Barra superior de Estado
        self.lbl_monedas = Label(text="🪙 Monedas: --", font_size='18sp', size_hint_y=0.1)
        layout_principal.add_widget(self.lbl_monedas)
        
        # 2. CONTENEDOR DE REVELACIÓN (Contiene la grilla horizontal)
        self.zona_sobre = BoxLayout(orientation='vertical', padding=10, size_hint_y=0.6)
        
        # Grilla para los recuadros de las cartas (1 fila, 5 columnas fijas)
        self.grilla_revelacion = GridLayout(rows=1, cols=5, spacing=15, size_hint_x=None)
        self.grilla_revelacion.bind(minimum_width=self.grilla_revelacion.setter('width'))
        
        # Mensaje inicial antes de abrir sobres
        self.lbl_inicial = Label(text="✨ ¡Prueba tu suerte! Compra un sobre de 5 cartas ✨\nCoste: 250 🪙", font_size='16sp')
        self.zona_sobre.add_widget(self.lbl_inicial)
        
        layout_principal.add_widget(self.zona_sobre)
        
        # 3. Botonera Inferior
        layout_botones = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=0.15)
        
        btn_gacha = Button(text="🎰 COMPRAR SOBRE GENERAL (250 🪙)", background_color=(0.2, 0.7, 0.3, 1), font_size='16sp')
        btn_gacha.bind(on_release=self.comprar_sobre_cinco_cartas)
        
        btn_volver = Button(text="Volver al Menú", background_color=(0.7, 0.2, 0.2, 1), size_hint_x=0.3)
        btn_volver.bind(on_release=lambda x: self.cambiar_a_menu())

        btn_tienda = Button(text="Ir a la Tienda", background_color=(0.7, 0.2, 0.2, 1), size_hint_x=0.3)
        btn_tienda.bind(on_release=lambda x: self.cambiar_a_tienda())
        
        
        layout_botones.add_widget(btn_gacha)
        layout_botones.add_widget(btn_volver)
        layout_botones.add_widget(btn_tienda)
        layout_principal.add_widget(layout_botones)
        
        self.add_widget(layout_principal)

    def on_enter(self):
        """Actualiza el balance de monedas al entrar a la tienda"""
        if os.path.exists(self.ruta_perfil):
            with open(self.ruta_perfil, "r", encoding="utf-8") as f:
                perfil = json.load(f)
            self.lbl_monedas.text = f"🪙 Mis Monedas: {perfil.get('coins', 0)}"

    def comprar_sobre_cinco_cartas(self, instance):
        # Llamamos al nuevo método asumiendo el coste de 250 por 5 cartas de la facción FEV
        resultado = GachaSystem.abrir_sobre_avanzado(tipo_banner="GENERAL", cantidad_cartas=5, costo=250)
        
        # Limpiamos la zona de revelación por si había un sobre abierto antes
        self.zona_sobre.clear_widgets()
        self.grilla_revelacion.clear_widgets()
        
        if not resultado["exito"]:
            # Si falla (ej: no hay monedas), volvemos a mostrar el label de error
            self.lbl_inicial.text = f"❌ {resultado['mensaje']}"
            self.zona_sobre.add_widget(self.lbl_inicial)
            return
            
        # Actualizamos monedas en la interfaz superior
        self.lbl_monedas.text = f"🪙 Mis Monedas: {resultado['nuevas_monedas']}"
        
        # Poblamos la grilla con los 5 recuadros independientes obtenidos del backend
        for carta in resultado["cartas"]:
            rareza = getattr(carta, 'rarity', 'Común')
            tipo = 'unit' if hasattr(carta, 'attack') else getattr(carta, 'card_type', 'unit')
            
            recuadro_carta = TarjetaRevelada(
                nombre=carta.name,
                coste=carta.cost,
                rareza=rareza,
                tipo=tipo
            )
            self.grilla_revelacion.add_widget(recuadro_carta)
            
        # Metemos la grilla llena de recuadros directamente a la vista activa
        self.zona_sobre.add_widget(self.grilla_revelacion)

    def cambiar_a_menu(self):
        self.manager.current = 'menu_screen'

    def cambiar_a_tienda(self):
        self.manager.current = 'shop_screen'
    