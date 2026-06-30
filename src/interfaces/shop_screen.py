import json
import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from src.domain.shop_system import ShopSystem

class TarjetaOferta(BoxLayout):
    """Componente visual para cada una de las 3 ofertas del día"""
    def __init__(self, id_carta, nombre, coste, rareza, tipo, precio, funcion_compra, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=8, **kwargs)
        
        if tipo == 'spell':
            color_fondo = (0.5, 0.2, 0.6, 1) # Morado
        elif tipo == 'building':
            color_fondo = (0.2, 0.5, 0.3, 1) # Verde
        else:
            color_fondo = (0.8, 0.6, 0.2, 1) if rareza == "Excelencia" else (0.1, 0.4, 0.6, 1)

        # Info de la carta
        self.add_widget(Label(text=f"{nombre}\nCoste: {coste}E\n[{rareza}]", halign='center', size_hint_y=0.5))
        
        # Botón de comprar con su precio asignado
        self.btn_comprar = Button(
            text=f"🛒 Canjear\n({precio} ✨)", 
            background_color=color_fondo,
            halign='center'
        )
        # Guardamos los atributos dentro del botón para poder leerlos al hacer clic
        self.btn_comprar.card_id = id_carta
        self.btn_comprar.precio = precio
        self.btn_comprar.nombre_carta = nombre
        self.btn_comprar.bind(on_release=funcion_compra)
        
        self.add_widget(self.btn_comprar)


class PantallaTienda(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ruta_perfil = "src/data/user_profile.json"
        
        layout_principal = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 1. Encabezado de divisas
        self.lbl_divisas = Label(text="TIENDA DE ESENCIAS  |  ✨ Esencia Actual: --", font_size='18sp', size_hint_y=0.12)
        layout_principal.add_widget(self.lbl_divisas)
        
        # 2. Vitrina de ofertas (3 columnas para las 3 cartas)
        self.vitrina = GridLayout(rows=1, cols=3, spacing=15, size_hint_y=0.73)
        layout_principal.add_widget(self.vitrina)
        
        # 3. Botonera inferior
        layout_botones = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=0.15)

        btn_volver = Button(text="Volver al Menú", background_color=(0.7, 0.2, 0.2, 1), size_hint_x=0.3)
        btn_volver.bind(on_release=lambda x: self.cambiar_a_menu())

        btn_banner = Button(text="Ir al Banner", background_color=(0.7, 0.2, 0.2, 1), size_hint_x=0.3)
        btn_banner.bind(on_release=lambda x: self.cambiar_a_banner())
        
        
        layout_botones.add_widget(btn_volver)
        layout_botones.add_widget(btn_banner)
        layout_principal.add_widget(layout_botones)
        
        self.add_widget(layout_principal)

    def on_enter(self):
        """Se ejecuta al abrir la tienda: refresca saldo y monta la rotación del día"""
        self.actualizar_interfaz_tienda()

    def actualizar_interfaz_tienda(self):
        self.vitrina.clear_widgets()
        
        # Leer esencia actual del jugador
        if os.path.exists(self.ruta_perfil):
            with open(self.ruta_perfil, "r", encoding="utf-8") as f:
                perfil = json.load(f)
            self.lbl_divisas.text = f"🏪 ROTACIÓN DIARIA  |  ✨ Mis Esencias: {perfil.get('craft_essence', 0)}"

        # Solicitar al backend las 3 cartas fijas de hoy
        ofertas_hoy = ShopSystem.obtener_rotacion_diaria()
        
        for o in ofertas_hoy:
            tarjeta = TarjetaOferta(
                id_carta=o["id"],
                nombre=o["nombre"],
                coste=o["coste_energia"],
                rareza=o["rareza"],
                tipo=o["tipo"],
                precio=o["precio_esencia"],
                funcion_compra=self.procesar_canje
            )
            self.vitrina.add_widget(tarjeta)

    def procesar_canje(self, instance):
        # Llamamos al backend de canjes pasando los metadatos incrustados en el botón
        resultado = ShopSystem.comprar_carta_tienda(instance.card_id, instance.precio)
        
        if resultado["exito"]:
            self.lbl_divisas.text = f"🎉 ¡Canjeado con éxito: {instance.nombre_carta}!  |  ✨ Restante: {resultado['nueva_esencia']}"
            # Re-renderizamos para reflejar el nuevo estado de esencias
            self.actualizar_interfaz_tienda()
        else:
            self.lbl_divisas.text = f"❌ {resultado['mensaje']}"

    def cambiar_a_menu(self):
        self.manager.current = 'menu_screen'
    
    def cambiar_a_banner(self):
        self.manager.current = 'banner_screen'