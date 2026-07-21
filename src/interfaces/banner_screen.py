import json
import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle

from src.domain.gacha_system import GachaSystem
from src.domain.audio_manager import AudioManager

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
            color_fondo = (0.8, 0.6, 0.2, 1) if rareza == "Excelencia" else (0.1, 0.4, 0.6, 1)

        btn_carta = Button(
            text=f"{nombre}\n\n⚡ Coste: {coste}\n[{rareza}]",
            background_color=color_fondo,
            halign='center',
            valign='middle'
        )
        btn_carta.bind(size=btn_carta.setter('text_size'))
        self.add_widget(btn_carta)


class PantallaBanner(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ruta_perfil = "src/data/user_profile.json"
        
        # --- CONFIGURACIÓN DE BANNERS DISPONIBLES ---
        # Aquí defines los datos de cada banner. Puedes añadir más fácilmente.
        self.lista_banners = [
            {
                "id": "SIMCE1", 
                "nombre": "Sobre SIMCE 1", 
                "desc": "¡El Chino (Quemadas) y Melsizis (DT) se unen al combate!",
                "coste_1": 100,
                "coste_5": 500,
                "imagen": "src/art/facciones_png/logo-simce.png" # Placeholder
            },
            {
                "id": "MISHEXPANSIONPACK1", 
                "nombre": "Sobre Mish", 
                "desc": "¡El equipo Mish se unen al combate! \n Cuando los unes causan gran daño a los enemigos cercanos.",
                "coste_1": 100,
                "coste_5": 500,
                "imagen": "src/art/facciones_png/logo-mish.png" # Placeholder
            },
            {
                "id": "ALIANZAS3RO", 
                "nombre": "Sobre Alianzas 3ro", 
                "desc": "¡El Dragon Menor de las Alianzas se une al combate! \n Acompañados de multiples cartas basadas en la época de alianzas",
                "coste_1": 100,
                "coste_5": 500,
                "imagen": "src/art/facciones_png/logo-alainzas3ro.png" # Placeholder
            }
        ]
        self.banner_actual = self.lista_banners[0] # Banner por defecto

        # --- LAYOUT PRINCIPAL (Horizontal al estilo Project Sekai) ---
        layout_principal = BoxLayout(orientation='horizontal')
        
        # ==========================================
        # PANEL IZQUIERDO: SELECCIÓN DE BANNERS
        # ==========================================
        panel_izquierdo = BoxLayout(orientation='vertical', size_hint_x=0.25, padding=10, spacing=10)
        
        lbl_titulo_banners = Label(text="BANNERS", font_size='18sp', bold=True, size_hint_y=None, height=40)
        panel_izquierdo.add_widget(lbl_titulo_banners)
        
        scroll_banners = ScrollView(size_hint=(1, 1))
        lista_botones_banners = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        lista_botones_banners.bind(minimum_height=lista_botones_banners.setter('height'))
        
        # Generar botones dinámicamente según la lista de banners
        for banner in self.lista_banners:
            btn_banner = Button(text=banner["nombre"], size_hint_y=None, height=60, background_color=(0.2, 0.4, 0.6, 1))
            # Pasamos el banner específico usando una función lambda con default arg
            btn_banner.bind(on_release=lambda instance, b=banner: self.cambiar_banner_activo(b))
            lista_botones_banners.add_widget(btn_banner)
            
        scroll_banners.add_widget(lista_botones_banners)
        panel_izquierdo.add_widget(scroll_banners)
        
        # Botón para salir
        btn_volver = Button(text="Volver al Menú", size_hint_y=None, height=50, background_color=(0.7, 0.2, 0.2, 1))
        btn_volver.bind(on_release=lambda x: self.cambiar_a_menu())
        panel_izquierdo.add_widget(btn_volver)

        # ==========================================
        # PANEL DERECHO: VISUALIZACIÓN Y GACHA
        # ==========================================
        self.panel_derecho = BoxLayout(orientation='vertical', size_hint_x=0.75, padding=20, spacing=15)
        
        # Barra superior (Monedas)
        self.lbl_monedas = Label(text="🪙 Monedas: --", font_size='20sp', bold=True, size_hint_y=0.1, halign='right')
        self.lbl_monedas.bind(size=self.lbl_monedas.setter('text_size'))
        self.panel_derecho.add_widget(self.lbl_monedas)
        
        # --- ZONA CENTRAL DINÁMICA ---
        # Usaremos un ScreenManager interno o simplemente limpiaremos este BoxLayout
        self.zona_central = BoxLayout(orientation='vertical', size_hint_y=0.7)
        self.panel_derecho.add_widget(self.zona_central)
        
        # --- BOTONERA DE TIROS (Bottom) ---
        self.layout_botones_tiro = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=0.2)
        
        self.btn_tirar_1 = Button(text="Tirar x1\n(-- 🪙)", font_size='16sp', background_color=(0.3, 0.7, 0.8, 1))
        self.btn_tirar_1.bind(on_release=lambda x: self.realizar_tiro(cantidad=1))
        
        self.btn_tirar_5 = Button(text="Tirar x5\n(-- 🪙)", font_size='16sp', bold=True, background_color=(0.8, 0.6, 0.2, 1))
        self.btn_tirar_5.bind(on_release=lambda x: self.realizar_tiro(cantidad=5))
        
        self.layout_botones_tiro.add_widget(self.btn_tirar_1)
        self.layout_botones_tiro.add_widget(self.btn_tirar_5)
        self.panel_derecho.add_widget(self.layout_botones_tiro)
        
        # Ensamblar todo
        layout_principal.add_widget(panel_izquierdo)
        layout_principal.add_widget(self.panel_derecho)
        self.add_widget(layout_principal)
        
        # Inicializar la vista con el banner por defecto
        self.renderizar_vista_banner()

    def on_enter(self):
        self.actualizar_monedas()
        AudioManager().play_bgm('placeholderbossanova.ogg')

    def actualizar_monedas(self):
        if os.path.exists(self.ruta_perfil):
            with open(self.ruta_perfil, "r", encoding="utf-8") as f:
                perfil = json.load(f)
            self.lbl_monedas.text = f"🪙 Mis Monedas: {perfil.get('coins', 0)}"

    def cambiar_banner_activo(self, banner_seleccionado):
        """Se ejecuta al tocar un botón del menú izquierdo"""
        self.banner_actual = banner_seleccionado
        self.renderizar_vista_banner()

    def renderizar_vista_banner(self):
        """Muestra el arte y botones del banner actualmente seleccionado"""
        self.zona_central.clear_widgets()
        
        # Imagen gigante del banner
        imagen_banner = Image(source=self.banner_actual["imagen"], allow_stretch=True, keep_ratio=True)
        
        # Título y descripción
        lbl_info = Label(
            text=f"[b]{self.banner_actual['nombre']}[/b]\n{self.banner_actual['desc']}", 
            markup=True, halign='center', size_hint_y=0.2
        )
        
        self.zona_central.add_widget(imagen_banner)
        self.zona_central.add_widget(lbl_info)
        
        # Actualizar textos de los botones de tiro
        self.btn_tirar_1.text = f"Tirar x1\n({self.banner_actual['coste_1']} 🪙)"
        self.btn_tirar_5.text = f"Tirar x5\n({self.banner_actual['coste_5']} 🪙)"
        
        # Asegurarnos de que los botones de tiro estén visibles
        self.layout_botones_tiro.opacity = 1
        self.layout_botones_tiro.disabled = False

    def realizar_tiro(self, cantidad):
        """Llama al backend de Gacha y cambia la vista a la pantalla de revelación"""
        costo_total = self.banner_actual["coste_1"] if cantidad == 1 else self.banner_actual["coste_5"]
        tipo_banner = self.banner_actual["id"]
        
        resultado = GachaSystem.abrir_sobre_avanzado(tipo_banner=tipo_banner, cantidad_cartas=cantidad, costo=costo_total)
        
        if not resultado["exito"]:
            # Pequeña alerta si no hay dinero
            self.zona_central.clear_widgets()
            self.zona_central.add_widget(Label(text=f"❌ {resultado['mensaje']}", font_size='20sp', color=(1,0,0,1)))
            return
            
        self.actualizar_monedas()
        self.renderizar_revelacion(resultado["cartas"])

    def renderizar_revelacion(self, cartas_obtenidas):
        """Oculta el arte del banner y muestra las cartas obtenidas"""
        self.zona_central.clear_widgets()
        
        # Ocultar botones de tiro durante la revelación
        self.layout_botones_tiro.opacity = 0
        self.layout_botones_tiro.disabled = True
        
        lbl_felicidades = Label(text="✨ ¡CARTAS OBTENIDAS! ✨", font_size='24sp', bold=True, size_hint_y=0.2)
        self.zona_central.add_widget(lbl_felicidades)
        
        # Contenedor para alinear las cartas en el centro
        contenedor_grilla = BoxLayout(orientation='horizontal', padding=20)
        # ScrollView por si tiran más de 5 cartas en el futuro
        scroll_cartas = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False)
        
        grilla_cartas = GridLayout(rows=1, spacing=15, size_hint_x=None)
        grilla_cartas.bind(minimum_width=grilla_cartas.setter('width'))
        
        for carta in cartas_obtenidas:
            rareza = getattr(carta, 'rarity', 'Común')
            tipo = 'unit' if hasattr(carta, 'attack') else getattr(carta, 'card_type', 'unit')
            recuadro_carta = TarjetaRevelada(nombre=carta.name, coste=carta.cost, rareza=rareza, tipo=tipo)
            grilla_cartas.add_widget(recuadro_carta)
            
        scroll_cartas.add_widget(grilla_cartas)
        contenedor_grilla.add_widget(scroll_cartas)
        self.zona_central.add_widget(contenedor_grilla)
        
        # Botón para Aceptar y volver a la vista del Banner
        btn_aceptar = Button(text="Aceptar", size_hint_y=0.2, size_hint_x=0.5, pos_hint={'center_x': 0.5}, background_color=(0.2, 0.7, 0.3, 1))
        btn_aceptar.bind(on_release=lambda x: self.renderizar_vista_banner())
        self.zona_central.add_widget(btn_aceptar)

    def cambiar_a_menu(self):
        self.manager.current = 'menu_screen'