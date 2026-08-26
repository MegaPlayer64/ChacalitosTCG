import json
import os
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.modalview import ModalView  # <-- CAPA FLOTANTE / MODAL

from src.infrastructure.loaders.card_loader import CardLoader


# ==========================================
# 1. CAPA / MODAL DE INSPECCIÓN DE CARTA
# ==========================================
class ModalDetalleCarta(ModalView):
    def __init__(self, datos_carta, **kwargs):
        super().__init__(size_hint=(0.75, 0.8), auto_dismiss=True, **kwargs)
        
        obj = datos_carta["objeto"]
        tipo = datos_carta["tipo"]
        rareza = datos_carta["rareza"]
        grupos_str = ", ".join(datos_carta["grupos"]) if datos_carta["grupos"] else "Ninguno"
        desc = getattr(obj, 'description', getattr(obj, 'descripcion', 'Sin descripción disponible.'))

        # Color de fondo según tipo
        if tipo == 'spell':
            color_header = "[color=bb88ff]"
            bg_card = (0.2, 0.1, 0.3, 1)
        elif tipo == 'building':
            color_header = "[color=88ffbb]"
            bg_card = (0.1, 0.25, 0.15, 1)
        else:
            color_header = "[color=88ccff]"
            bg_card = (0.1, 0.2, 0.35, 1)

        layout_contenido = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # Encabezado: Nombre y Coste
        lbl_titulo = Label(
            text=f"{color_header}[b]{obj.name.upper()}[/b][/color]\n[size=14sp]Coste: {obj.cost}E | Rareza: {rareza}[/size]",
            markup=True,
            font_size='20sp',
            size_hint_y=0.18,
            halign='center'
        )
        layout_contenido.add_widget(lbl_titulo)

        # Si es UNIDAD, mostramos sus estadísticas de combate
        if tipo == 'unit':
            atk = getattr(obj, 'attack', 0)
            hp = getattr(obj, 'health', getattr(obj, 'max_health', 0))
            spd = getattr(obj, 'speed', 0)
            rng = getattr(obj, 'range_atk', 1)

            lbl_stats = Label(
                text=f"[color=ff5555][b]⚔️ Daño: {atk}[/b][/color]  |  [color=55ff55][b]❤️ Vida: {hp}[/b][/color]\n"
                     f"[color=55ffffff][b]⚡ Vel: {spd}[/b][/color]  |  [color=ffff55][b]🎯 Rango: {rng}[/b][/color]",
                markup=True,
                font_size='15sp',
                size_hint_y=0.15,
                halign='center'
            )
            layout_contenido.add_widget(lbl_stats)

        # Tags / Grupos
        lbl_tags = Label(
            text=f"[color=aaaaaa][i]Grupos / Tags:[/i] {grupos_str}[/color]",
            markup=True,
            font_size='13sp',
            size_hint_y=0.1,
            halign='center'
        )
        layout_contenido.add_widget(lbl_tags)

        # Descripción / Lore / Efecto Especial
        scroll_desc = ScrollView(size_hint_y=0.45)
        lbl_desc = Label(
            text=f"[i]{desc}[/i]",
            markup=True,
            font_size='14sp',
            size_hint_y=None,
            halign='center',
            valign='top'
        )
        lbl_desc.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        lbl_desc.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll_desc.add_widget(lbl_desc)
        layout_contenido.add_widget(scroll_desc)

        # Botón para cerrar
        btn_cerrar = Button(
            text="CERRAR",
            size_hint_y=0.12,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_cerrar.bind(on_release=self.dismiss)
        layout_contenido.add_widget(btn_cerrar)

        self.add_widget(layout_contenido)


# ==========================================
# 2. TARJETA DEL ÁLBUM
# ==========================================
class TarjetaAlbum(BoxLayout):
    def __init__(self, datos_carta, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=180, **kwargs)
        
        nombre = datos_carta["nombre"]
        coste = datos_carta["coste"]
        rareza = datos_carta["rareza"]
        tipo = datos_carta["tipo"]
        cantidad = datos_carta["cantidad"]

        if tipo == 'spell':
            color_fondo = (0.5, 0.2, 0.6, 1) # Morado
        elif tipo == 'building':
            color_fondo = (0.2, 0.5, 0.3, 1) # Verde
        else:
            color_fondo = (0.1, 0.4, 0.6, 1) # Azul Unidades

        btn_visual = Button(
            text=f"{nombre}\nCoste: {coste}E\n[{rareza}]", 
            background_color=color_fondo,
            halign='center'
        )
        
        # Al presionar el botón de la carta, abrimos la capa Modal
        btn_visual.bind(on_release=lambda instance: ModalDetalleCarta(datos_carta).open())

        lbl_cant = Label(text=f"Poseídas: x{cantidad}", size_hint_y=0.2, color=(1, 1, 1, 1))
        
        self.add_widget(btn_visual)
        self.add_widget(lbl_cant)


# ==========================================
# 3. PANTALLA PRINCIPAL
# ==========================================
class PantallaInventario(Screen):
    PESO_RAREZA = {
        "Común": 1,
        "Especial": 2,
        "Épica": 3,
        "Excelencia": 4
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ruta_perfil = "src/data/user_profile.json"
        self.coleccion_datos = []
        
        layout_principal = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 1. Header
        self.lbl_titulo = Label(text="ÁLBUM DE COLECCIÓN", size_hint_y=0.08, font_size='18sp')
        layout_principal.add_widget(self.lbl_titulo)
        
        # 2. Filtros
        layout_filtros = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.08)
        
        self.spn_orden = Spinner(
            text="Ordenar: ID",
            values=["Ordenar: ID", "Ordenar: Rareza", "Ordenar: Coste", "Ordenar: Cantidad", "Ordenar: Nombre"],
            size_hint_x=0.35
        )
        self.spn_orden.bind(text=self.actualizar_vista)

        self.spn_tipo = Spinner(
            text="Tipo: Todos",
            values=["Tipo: Todos", "Unidades", "Trucos (Spells)", "Entornos (Buildings)"],
            size_hint_x=0.32
        )
        self.spn_tipo.bind(text=self.actualizar_vista)

        self.spn_tag = Spinner(
            text="Tag: Todas",
            values=["Tag: Todas"],
            size_hint_x=0.33
        )
        self.spn_tag.bind(text=self.actualizar_vista)

        layout_filtros.add_widget(self.spn_orden)
        layout_filtros.add_widget(self.spn_tipo)
        layout_filtros.add_widget(self.spn_tag)
        layout_principal.add_widget(layout_filtros)
        
        # 3. Grilla de Cartas con Scroll
        scroll = ScrollView(size_hint_y=0.74)
        self.grilla_cartas = GridLayout(cols=4, spacing=10, size_hint_y=None)
        self.grilla_cartas.bind(minimum_height=self.grilla_cartas.setter('height'))
        
        scroll.add_widget(self.grilla_cartas)
        layout_principal.add_widget(scroll)
        
        # 4. Botonera Inferior
        layout_botones = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.1)
        
        btn_volver = Button(text="Volver al Menú", size_hint_x=0.25)
        btn_volver.bind(on_release=lambda x: self.cambiar_a_menu())
        
        btn_reciclar = Button(text="♻️ RECICLAR DUPLICADOS", font_size='14sp', background_color=(0.7, 0.4, 0.1, 1), size_hint_x=0.35)
        btn_reciclar.bind(on_release=self.ejecutar_reciclaje_ui)
        
        btn_crear_mazo = Button(text="CREAR O EDITAR MAZO", font_size='14sp', background_color=(0.2, 0.6, 0.4, 1), size_hint_x=0.4)
        btn_crear_mazo.bind(on_release=self.abrir_deck_builder)
        
        layout_botones.add_widget(btn_volver)
        layout_botones.add_widget(btn_reciclar)
        layout_botones.add_widget(btn_crear_mazo)
        
        layout_principal.add_widget(layout_botones)
        self.add_widget(layout_principal)

    def on_enter(self):
        self.cargar_inventario_desde_json()

    def cargar_inventario_desde_json(self):
        if not os.path.exists(self.ruta_perfil):
            self.lbl_titulo.text = "ÁLBUM DE COLECCIÓN (Perfil no encontrado)"
            return
            
        try:
            with open(self.ruta_perfil, "r", encoding="utf-8") as f:
                perfil_data = json.load(f)
        except Exception as e:
            print(f"[!] Error al parsear el JSON del perfil: {e}")
            return

        usuario = perfil_data.get("username", "Jugador")
        monedas = perfil_data.get("coins", 0)
        esencia = perfil_data.get("craft_essence", 0)
        self.lbl_titulo.text = f"ÁLBUM DE {usuario.upper()}  |  🪙 Monedas: {monedas}  |  ✨ Esencia: {esencia}"

        inventario_usuario = perfil_data.get("inventory", {})
        self.coleccion_datos.clear()
        tags_detectadas = set()

        for card_id_str, cantidad in inventario_usuario.items():
            card_id = int(card_id_str)
            carta_objeto = CardLoader.get_card_stats_by_id(card_id)
            
            if carta_objeto and cantidad > 0:
                rareza = getattr(carta_objeto, 'rarity', 'Común')
                tipo = 'unit' if hasattr(carta_objeto, 'attack') else getattr(carta_objeto, 'card_type', 'unit')
                
                grupos_raw = getattr(carta_objeto, 'groups', getattr(carta_objeto, 'grupos', ''))
                
                if isinstance(grupos_raw, str):
                    lista_preliminar = grupos_raw.replace('\n', ',').split(',')
                elif isinstance(grupos_raw, (list, tuple)):
                    lista_preliminar = grupos_raw
                else:
                    lista_preliminar = []

                grupos = [str(g).strip() for g in lista_preliminar if str(g).strip() not in ('', '-')]

                for tag in grupos:
                    tags_detectadas.add(tag)
                    
                self.coleccion_datos.append({
                    "id": card_id,
                    "objeto": carta_objeto,
                    "cantidad": cantidad,
                    "nombre": carta_objeto.name,
                    "coste": carta_objeto.cost,
                    "rareza": rareza,
                    "tipo": tipo,
                    "grupos": grupos
                })

        self.spn_tag.values = ["Tag: Todas"] + sorted(list(tags_detectadas))
        self.actualizar_vista()

    def actualizar_vista(self, *args):
        self.grilla_cartas.clear_widgets()
        cartas_filtradas = list(self.coleccion_datos)

        # Filtros
        tipo_sel = self.spn_tipo.text
        if tipo_sel == "Unidades":
            cartas_filtradas = [c for c in cartas_filtradas if c["tipo"] == "unit"]
        elif tipo_sel == "Trucos (Spells)":
            cartas_filtradas = [c for c in cartas_filtradas if c["tipo"] == "spell"]
        elif tipo_sel == "Entornos (Buildings)":
            cartas_filtradas = [c for c in cartas_filtradas if c["tipo"] == "building"]

        tag_sel = self.spn_tag.text
        if tag_sel != "Tag: Todas":
            tag_limpia = tag_sel.replace("Tag: ", "")
            cartas_filtradas = [c for c in cartas_filtradas if tag_limpia in c["grupos"]]

        # Orden
        orden_sel = self.spn_orden.text
        if orden_sel == "Ordenar: Rareza":
            cartas_filtradas.sort(key=lambda c: self.PESO_RAREZA.get(c["rareza"], 0), reverse=True)
        elif orden_sel == "Ordenar: Coste":
            cartas_filtradas.sort(key=lambda c: c["coste"])
        elif orden_sel == "Ordenar: Cantidad":
            cartas_filtradas.sort(key=lambda c: c["cantidad"], reverse=True)
        elif orden_sel == "Ordenar: Nombre":
            cartas_filtradas.sort(key=lambda c: c["nombre"].lower())
        else:
            cartas_filtradas.sort(key=lambda c: c["id"])

        # Renderizar en UI
        for c in cartas_filtradas:
            tarjeta = TarjetaAlbum(datos_carta=c)  # Pass dict directly
            self.grilla_cartas.add_widget(tarjeta)

    def ejecutar_reciclaje_ui(self, instance):
        from src.domain.craft_system import CraftSystem
        
        resultado = CraftSystem.reciclar_excesos()
        if resultado["exito"]:
            self.lbl_titulo.text = f"♻️ ¡Moliste {resultado['cartas_rotas']} cartas por +{resultado['esencia_obtenida']} ✨!"
            self.cargar_inventario_desde_json()
        else:
            self.lbl_titulo.text = f"❌ {resultado['mensaje']}"
            
    def cambiar_a_menu(self):
        self.manager.current = 'menu_screen'

    def abrir_deck_builder(self, instance):
        self.manager.current = 'deck_builder_screen'