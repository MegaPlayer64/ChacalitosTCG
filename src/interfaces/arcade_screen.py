import json
import os
import random
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from src.domain.grid_background import FondoCuadriculado

OPCION_MAZO_RANDOM = "[Aleatorio] Mazo Random (Bono 1.5x 🪙)"

class PantallaArcade(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ruta_perfil = "src/data/user_profile.json"
        self.ruta_mapa = "src/data/arcade_map.json"
        self.stages_catalogo = self._cargar_mapa()
        
        # Mapa generado para la run actual
        self.run_map = []
        self.current_stage_index = 0
        self.opcion_seleccionada = None
        self.mazos = []

        self.add_widget(FondoCuadriculado(size=self.size), index=0)

        self.layout_global = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Header
        self.lbl_titulo = Label(
            text="[b]MODO ARCADE: SELECCIÓN DE RUTA[/b]",
            font_size='22sp',
            markup=True,
            size_hint_y=0.1
        )
        self.lbl_advertencia = Label(text="[color=ff0000][b]SI SALES DEL MODO, NO PUEDES SEGUIR DESDE EL ÚLTIMO PUNTO DEJADO[/b][/color]", markup=True, size_hint_y=0.1, halign='center', valign='middle')
        self.layout_global.add_widget(self.lbl_advertencia)
        self.layout_global.add_widget(self.lbl_titulo)

        # Panel para las 2 Tarjetas de Oponentes de la Run
        self.layout_opciones = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=0.48)
        self.layout_global.add_widget(self.layout_opciones)

        # Selector de Mazo del Jugador
        panel_j1 = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.22)
        panel_j1.add_widget(Label(text="Tu Mazo:", font_size='16sp'))

        self.spinner_mazo_j1 = Spinner(
            text='Cargando...',
            values=(),
            size_hint=(None, None), size=(320, 44), pos_hint={'center_x': 0.5}
        )
        panel_j1.add_widget(self.spinner_mazo_j1)
        self.layout_global.add_widget(panel_j1)

        # Botones de Acción
        layout_botones = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=0.2)
        btn_volver = Button(text="ABANDONAR TORRE", background_color=(0.8, 0.2, 0.2, 1))
        btn_volver.bind(on_release=lambda x: self.abandonar_torre())

        self.btn_iniciar = Button(text="SELECCIONA UN RIVAL", disabled=True, background_color=(0.3, 0.3, 0.3, 1))
        self.btn_iniciar.bind(on_release=self.iniciar_combate)

        layout_botones.add_widget(btn_volver)
        layout_botones.add_widget(self.btn_iniciar)
        self.layout_global.add_widget(layout_botones)

        self.add_widget(self.layout_global)

    def _cargar_mapa(self):
        if os.path.exists(self.ruta_mapa):
            try:
                with open(self.ruta_mapa, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[!] Error cargando arcade_map.json: {e}")
        return []

    def generar_nueva_run(self):
        """
        Selecciona 2 opciones al azar de cada piso del catálogo
        para crear una ruta única en esta partida.
        """
        self.current_stage_index = 0
        self.run_map = []
        
        for stage in self.stages_catalogo:
            opciones_totales = stage.get("options", [])
            # Tomamos 2 opciones aleatorias (o menos si no hay suficientes)
            cant_opciones = min(2, len(opciones_totales))
            opciones_generadas = random.sample(opciones_totales, cant_opciones)
            
            self.run_map.append({
                "stage": stage.get("stage", 1),
                "title": stage.get("title", "Piso"),
                "options": opciones_generadas
            })
        print(">> [ARCADE] ¡Nueva Torre generada con rutas aleatorias!")

    def on_enter(self):
        self.mazos = self.obtener_lista_mazos()
        opciones_visuales = [m['nombre'] for m in self.mazos]
        opciones_con_random = [OPCION_MAZO_RANDOM] + opciones_visuales

        if opciones_visuales:
            self.spinner_mazo_j1.values = tuple(opciones_con_random)
            if self.spinner_mazo_j1.text not in opciones_con_random:
                self.spinner_mazo_j1.text = opciones_con_random[0]

        # Si venimos desde el menú o reiniciamos la torre, generamos rutas nuevas
        if not self.run_map or self.current_stage_index == 0:
            self.generar_nueva_run()

        self.renderizar_opciones_piso()

    def renderizar_opciones_piso(self):
        self.layout_opciones.clear_widgets()
        self.opcion_seleccionada = None
        self.btn_iniciar.disabled = True
        self.btn_iniciar.text = "SELECCIONA UN RIVAL"
        self.btn_iniciar.background_color = (0.3, 0.3, 0.3, 1)

        if self.current_stage_index >= len(self.run_map):
            self.lbl_titulo.text = "[b]¡TORRE COMPLETADA![/b]"
            return

        stage_actual = self.run_map[self.current_stage_index]
        self.lbl_titulo.text = f"[b]{stage_actual['title']}[/b]"

        # Muestra únicamente las 2 opciones seleccionadas para esta run
        for op in stage_actual.get("options", []):
            panel_op = BoxLayout(orientation='vertical', padding=12, spacing=8)
            
            info_text = (
                f"[b]{op['title']}[/b]\n\n"
                f"Rival: [color=ffbb33]{op['ai_type']}[/color]\n"
                f"Botín: [color=00ff88]+{op['reward']} 🪙[/color]\n\n"
                f"[i]{op['desc']}[/i]"
            )
            lbl_info = Label(text=info_text, markup=True, halign='center', valign='middle')
            lbl_info.bind(size=lbl_info.setter('text_size'))
            
            btn_elegir = Button(
                text="ELEGIR ESTA RUTA",
                size_hint_y=0.28,
                background_color=(0.2, 0.6, 0.8, 1)
            )
            btn_elegir.bind(on_release=lambda x, data=op, btn_ref=btn_elegir: self.seleccionar_opcion(data, btn_ref))

            panel_op.add_widget(lbl_info)
            panel_op.add_widget(btn_elegir)
            self.layout_opciones.add_widget(panel_op)

    def seleccionar_opcion(self, opcion_data, boton_pulsado):
        self.opcion_seleccionada = opcion_data
        
        # Resetear estilos de selección
        for child in self.layout_opciones.children:
            for widget in child.children:
                if isinstance(widget, Button):
                    widget.background_color = (0.2, 0.6, 0.8, 1)

        boton_pulsado.background_color = (0.2, 0.8, 0.2, 1)
        self.btn_iniciar.disabled = False
        self.btn_iniciar.text = f"COMBATIR CONTRA {opcion_data['title'].upper()}"
        self.btn_iniciar.background_color = (0.2, 0.8, 0.2, 1)

    def obtener_lista_mazos(self):
        mazos = []
        # base_path = "src/data/premade_decks"
        # if os.path.exists(base_path):
            # for root, dirs, files in os.walk(base_path):
                # for file in files:
                    # if file.endswith('.json'):
                        # full_path = os.path.join(root, file).replace('\\', '/')
                        # mazos.append({
                            # 'nombre': f"[Premade] {file.replace('.json', '')}",
                           # 'ruta': full_path,
                            #'tipo_origen': 'archivo'
                        # })

        if os.path.exists(self.ruta_perfil):
            try:
                with open(self.ruta_perfil, "r", encoding="utf-8") as f:
                    perfil = json.load(f)
                for nombre_mazo in perfil.get("decks", {}).keys():
                    mazos.append({
                        'nombre': f"[Personal] {nombre_mazo}",
                        'ruta': nombre_mazo,
                        'tipo_origen': 'perfil'
                    })
            except Exception as e:
                print(f"[!] Error leyendo perfil: {e}")

        return mazos

    def _resolver_config_mazo(self, texto_spinner):
        if texto_spinner == OPCION_MAZO_RANDOM:
            if self.mazos:
                elegido = random.choice(self.mazos)
                elegido['is_random'] = True
                return elegido
            return None
        config = next((m for m in self.mazos if m['nombre'] == texto_spinner), None)
        if config:
            config['is_random'] = False
        return config

    def iniciar_combate(self, instance=None):
        if not self.opcion_seleccionada:
            return

        config_j1 = self._resolver_config_mazo(self.spinner_mazo_j1.text)
        if not config_j1:
            return

        opcion = self.opcion_seleccionada

        self.manager.app.game_settings = {
            'mode': 'arcade',
            'stage_index': self.current_stage_index,
            'stage_data': {
                'ai_type': opcion['ai_type'],
                'ai_deck': opcion['ai_deck'],
                'ai_deck_origin': 'archivo',
                'reward': opcion['reward']
            },
            'p1': {
                'tipo': 'Humano',
                'mazo': config_j1['ruta'],
                'origen': config_j1['tipo_origen'],
                'is_random': config_j1.get('is_random', False)
            },
            'p2': {
                'tipo': opcion['ai_type'],
                'mazo': opcion['ai_deck'],
                'origen': 'archivo'
            }
        }

        self.manager.current = 'vs_screen'

    def abandonar_torre(self):
        self.current_stage_index = 0
        self.run_map = []
        self.manager.current = 'menu_screen'