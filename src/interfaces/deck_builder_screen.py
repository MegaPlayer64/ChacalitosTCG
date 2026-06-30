import json
import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

from src.infrastructure.loaders.card_loader import CardLoader

class PantallaDeckBuilder(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ruta_perfil = "src/data/user_profile.json"
        
        self.mazo_actual_ids = []
        self.inventario_disponible = {} 
        self.carta_marcada_id = None 

        layout_global = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # --- 1. ENCABEZADO: Nombre del Mazo Interactiva ---
        layout_header = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=10)
        layout_header.add_widget(Label(text="Mazo a editar:", size_hint_x=0.2, font_size='16sp'))
        
        # BLINDAJE SELECTOR: Cuando el usuario termine de escribir y presione Enter o desenfoque, cargará ese mazo
        self.txt_nombre_mazo = TextInput(text="mazo_principal", multiline=False, size_hint_x=0.4, font_size='16sp')
        self.txt_nombre_mazo.bind(on_text_validate=self.cambiar_y_cargar_mazo_dinamico)
        layout_header.add_widget(self.txt_nombre_mazo)
        
        self.lbl_contador_mazo = Label(text="Tamaño: 0 / 40 cartas", size_hint_x=0.4, font_size='16sp')
        layout_header.add_widget(self.lbl_contador_mazo)
        layout_global.add_widget(layout_header)

        # --- 2. ÁREA CENTRAL ---
        layout_columnas = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.82)

        # Columna Izquierda: Colección Disponible
        col_izquierda = BoxLayout(orientation='vertical', size_hint_x=0.4)
        col_izquierda.add_widget(Label(text="Mi Colección (Clic para marcar/añadir)", size_hint_y=0.06))
        scroll_coleccion = ScrollView()
        self.grilla_coleccion = GridLayout(cols=2, spacing=5, size_hint_y=None)
        self.grilla_coleccion.bind(minimum_height=self.grilla_coleccion.setter('height'))
        scroll_coleccion.add_widget(self.grilla_coleccion)
        col_izquierda.add_widget(scroll_coleccion)

        # Columna Central: Cartas en el Mazo
        col_central = BoxLayout(orientation='vertical', size_hint_x=0.3)
        col_central.add_widget(Label(text="Cartas en el Mazo (Clic para quitar)", size_hint_y=0.06))
        scroll_mazo = ScrollView()
        self.lista_mazo_visual = GridLayout(cols=1, spacing=4, size_hint_y=None)
        self.lista_mazo_visual.bind(minimum_height=self.lista_mazo_visual.setter('height'))
        scroll_mazo.add_widget(self.lista_mazo_visual)
        col_central.add_widget(scroll_mazo)

        # Columna Derecha: Panel Informativo
        col_derecha = BoxLayout(orientation='vertical', size_hint_x=0.3, spacing=10)
        col_derecha.add_widget(Label(text="🔍 Detalles de la Carta", size_hint_y=0.06))
        self.lbl_detalles_carta = Label(
            text="Selecciona una carta para inspeccionar.", 
            text_size=(250, None), halign='left', valign='top', size_hint_y=0.5
        )
        self.lbl_detalles_carta.bind(size=self.lbl_detalles_carta.setter('text_size'))
        col_derecha.add_widget(self.lbl_detalles_carta)
        
        col_derecha.add_widget(Label(text="📊 Sinergias del Mazo", size_hint_y=0.06))
        self.lbl_sinergias = Label(text="No hay tags.", text_size=(250, None), halign='left', valign='top', size_hint_y=0.38)
        self.lbl_sinergias.bind(size=self.lbl_sinergias.setter('text_size'))
        col_derecha.add_widget(self.lbl_sinergias)

        layout_columnas.add_widget(col_izquierda)
        layout_columnas.add_widget(col_central)
        layout_columnas.add_widget(col_derecha)
        layout_global.add_widget(layout_columnas)

        # --- 3. BOTONERA INFERIOR ---
        layout_botones = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.1)
        btn_guardar = Button(text="💾 GUARDAR MAZO ACTUAL", background_color=(0.2, 0.6, 0.3, 1))
        btn_guardar.bind(on_release=self.ejecutar_guardado)
        
        btn_volver = Button(text="Volver al Menú", background_color=(0.7, 0.2, 0.2, 1), size_hint_x=0.3)
        btn_volver.bind(on_release=lambda x: self.cambiar_a_menu())
        
        layout_botones.add_widget(btn_guardar)
        layout_botones.add_widget(btn_volver)
        layout_global.add_widget(layout_botones)

        self.add_widget(layout_global)

    def on_enter(self):
        """Se ejecuta al entrar a la pantalla utilizando el mazo escrito actualmente"""
        self.cargar_datos_del_perfil()

    def cambiar_y_cargar_mazo_dinamico(self, instance):
        """Permite cambiar de mazo desde la interfaz escribiendo el nombre y presionando Enter"""
        self.cargar_datos_del_perfil()

    def cargar_datos_del_perfil(self):
        if not os.path.exists(self.ruta_perfil):
            return

        with open(self.ruta_perfil, "r", encoding="utf-8") as f:
            perfil = json.load(f)

        nombre_mazo_buscado = self.txt_nombre_mazo.text.strip().lower().replace(" ", "_")
        
        # Cargar la lista de IDs del mazo seleccionado, o empezar de cero si es nuevo
        if "decks" in perfil and nombre_mazo_buscado in perfil["decks"]:
            self.mazo_actual_ids = perfil["decks"][nombre_mazo_buscado]
        else:
            self.mazo_actual_ids = []
        
        # Re-indexar el inventario disponible
        inventario_total = perfil.get("inventory", {})
        self.inventario_disponible = {k: int(v) for k, v in inventario_total.items()}
        
        # Descontar lo que ya esté en este mazo
        for cid in self.mazo_actual_ids:
            cid_str = str(cid)
            if cid_str in self.inventario_disponible:
                self.inventario_disponible[cid_str] -= 1

        self.refrescar_interfaz_completa()

    def refrescar_interfaz_completa(self):
        self.grilla_coleccion.clear_widgets()
        self.lista_mazo_visual.clear_widgets()
        
        # 1. Pintar Colección
        for card_id_str, cantidad_libre in self.inventario_disponible.items():
            card_id = int(card_id_str)
            carta_obj = CardLoader.get_card_stats_by_id(card_id)
            
            if carta_obj:
                marcada = (card_id == self.carta_marcada_id)
                color_btn = (0.2, 0.5, 0.7, 1) if marcada else (0.2, 0.2, 0.2, 1)
                
                texto_item = f"{carta_obj.name}\n({cantidad_libre} libres)"
                if cantidad_libre == 0:
                    texto_item = f"{carta_obj.name}\n(En uso)"
                    color_btn = (0.1, 0.1, 0.1, 0.6)
                
                btn_item = Button(text=texto_item, size_hint_y=None, height=80, halign='center', background_color=color_btn)
                btn_item.card_id = card_id
                btn_item.bind(on_release=self.marcar_o_añadir_carta)
                self.grilla_coleccion.add_widget(btn_item)

        # 2. Pintar Lista del Mazo
        for card_id in sorted(self.mazo_actual_ids):
            carta_obj = CardLoader.get_card_stats_by_id(card_id)
            if carta_obj:
                btn_mazo = Button(text=f"{carta_obj.name} | Coste: {carta_obj.cost}E", size_hint_y=None, height=40, background_color=(0.1, 0.4, 0.5, 1))
                btn_mazo.card_id = card_id
                btn_mazo.bind(on_release=self.quitar_carta_del_mazo)
                self.lista_mazo_visual.add_widget(btn_mazo)

        # 3. Actualizar metadatos
        self.lbl_contador_mazo.text = f"Tamaño: {len(self.mazo_actual_ids)} / 40 cartas"
        self.calcular_sinergias_de_tags()

    def marcar_o_añadir_carta(self, instance):
        cid = instance.card_id
        cid_str = str(cid)
        
        if self.carta_marcada_id != cid:
            self.carta_marcada_id = cid
            self.actualizar_panel_detalles(cid)
            self.refrescar_interfaz_completa()
        else:
            # --- REGLAS DE BLINDAJE DE TORNEO ---
            # 1. Control de límite máximo del mazo (40 cartas)
            if len(self.mazo_actual_ids) >= 40:
                self.lbl_contador_mazo.text = "❌ ¡Límite alcanzado! Máximo 40 cartas."
                return

            # 2. Control de copias máximas de una misma ID (Máximo 4)
            copias_en_mazo = self.mazo_actual_ids.count(cid)
            if copias_en_mazo >= 4:
                self.lbl_contador_mazo.text = "❌ Máximo 4 copias de la misma carta."
                return

            # Si pasa los filtros, añadimos la carta
            if self.inventario_disponible.get(cid_str, 0) > 0:
                self.inventario_disponible[cid_str] -= 1
                self.mazo_actual_ids.append(cid)
                self.refrescar_interfaz_completa()

    def quitar_carta_del_mazo(self, instance):
        cid = instance.card_id
        cid_str = str(cid)
        
        if cid in self.mazo_actual_ids:
            self.mazo_actual_ids.remove(cid)
            if cid_str in self.inventario_disponible:
                self.inventario_disponible[cid_str] += 1
            else:
                self.inventario_disponible[cid_str] = 1
            self.refrescar_interfaz_completa()

    def actualizar_panel_detalles(self, card_id):
        carta = CardLoader.get_card_stats_by_id(card_id)
        if not carta:
            return
        rareza = getattr(carta, 'rarity', 'Común')
        habilidad = getattr(carta, 'description', 'Ninguna habilidad especial.')
        tags = getattr(carta, 'groups', 'Ninguno')

        if hasattr(carta, 'attack') and hasattr(carta, 'health'):
            stats_combate = f"❤️ Vida: {carta.health}  |  ⚔️ Ataque: {carta.attack}\n🏃 Velocidad: {carta.speed}"
        else:
            stats_combate = "🔮 Carta de Efecto / Truco / Entorno"

        self.lbl_detalles_carta.text = f"🏷️ [{rareza}] {carta.name.upper()}\n⚡ Coste: {carta.cost}\n{stats_combate}\n👥 Tags: {tags}\n\n📜 EFECTO:\n{habilidad}"

    def calcular_sinergias_de_tags(self):
        if not self.mazo_actual_ids:
            self.lbl_sinergias.text = "Mazo vacío."
            return
        conteo_tags = {}
        for cid in self.mazo_actual_ids:
            carta = CardLoader.get_card_stats_by_id(cid)
            if carta:
                grupos_data = getattr(carta, 'groups', '')
                if isinstance(grupos_data, list):
                    lista_tags = [str(t).strip() for t in grupos_data]
                elif isinstance(grupos_data, str) and grupos_data != '-':
                    lista_tags = [t.strip() for t in grupos_data.replace('\n', ',').split(',')]
                else:
                    lista_tags = []

                for tag in lista_tags:
                    if tag:
                        conteo_tags[tag] = conteo_tags.get(tag, 0) + 1

        if not conteo_tags:
            self.lbl_sinergias.text = "Sin tags."
            return

        sinergias_ordenadas = sorted(conteo_tags.items(), key=lambda x: x[1], reverse=True)
        texto_sinergia = "👥 Facciones en el Mazo:\n"
        for tag, cant in sinergias_ordenadas:
            alerta = "🔥 (Sinergia Activa)" if cant >= 3 else ""
            texto_sinergia += f" • {tag}: {cant} uds {alerta}\n"
        self.lbl_sinergias.text = texto_sinergia

    def ejecutar_guardado(self, instance):
        from src.domain.deck_system import DeckSystem
        nombre_mazo = self.txt_nombre_mazo.text.strip().lower().replace(" ", "_")
        if not nombre_mazo:
            nombre_mazo = "mazo_principal"
            
        exito = DeckSystem.guardar_mazo(nombre_mazo, self.mazo_actual_ids)
        if exito:
            self.lbl_contador_mazo.text = f"✅ '{nombre_mazo}' guardado con éxito ({len(self.mazo_actual_ids)} uds)"

    def cambiar_a_menu(self):
        self.manager.current = 'menu_screen'