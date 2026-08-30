from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from src.domain.rewards_system import RewardsSystem


class PantallaResultado(Screen):
    """Pantalla de Victoria / Derrota que muestra las recompensas obtenidas."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        
        self.victoria_local = True 
        self.turn_count = 1
        
        self.lbl_titulo = Label(
            text="",
            font_size='48sp',
            markup=True,
            size_hint_y=0.35,
            halign='center'
        )
        self.lbl_detalle = Label(
            text="",
            font_size='20sp',
            markup=True,
            size_hint_y=0.25,
            halign='center'
        )

        self.btn_accion_principal = Button(
            text="REVANCHA",
            font_size='18sp',
            size_hint_y=0.2,
            background_color=(0.2, 0.6, 0.9, 1)
        )

        btn_menu = Button(
            text="MENÚ PRINCIPAL",
            font_size='18sp',
            size_hint_y=0.2,
            background_color=(0.4, 0.4, 0.4, 1)
        )
        btn_menu.bind(on_release=lambda x: self._ir_a('menu_screen'))

        self.layout.add_widget(self.lbl_titulo)
        self.layout.add_widget(self.lbl_detalle)
        self.layout.add_widget(self.btn_accion_principal)
        self.layout.add_widget(btn_menu)
        self.add_widget(self.layout)

    def on_enter(self):
        settings = getattr(self.manager.app, 'game_settings', {}) or {}
        mode = settings.get('mode', 'normal')

        if mode == 'arcade':
            self._procesar_resultado_arcade(settings)
        else:
            self._procesar_resultado_estandar(settings)

    def _procesar_resultado_arcade(self, settings):
        stage_data = settings.get('stage_data', {})
        stage_index = settings.get('stage_index', 0)
        p1_info = settings.get('p1', {})
        
        # Desvincular handlers previos
        if hasattr(self, '_callback_actual'):
            self.btn_accion_principal.unbind(on_release=self._callback_actual)

        if self.victoria_local:
            base_reward = stage_data.get('reward', 50)
            is_random = p1_info.get('is_random', False)
            mult_extra = 1.5 if is_random else 1.0
            
            # Otorgar recompensa centralizada
            premios = RewardsSystem.otorgar_recompensa(
                victoria=True,
                dificultad_rival=stage_data.get('ai_type', 'IA Normal'),
                monedas_base_override=base_reward,
                mult_extra=mult_extra,
                turn_count=self.turn_count
            )

            if premios:
                bonus_text = " [color=ffbb33](¡Bono 1.5x Mazo Random!)[/color]" if is_random else ""
                msg_ticket = f"  |  +{premios['tickets']} 🎟️ Tickets" if premios['tickets'] > 0 else ""
                msg_exp = f"  |  +{premios.get('exp_pase', 0)} 🎖️ EXP Pase"
                msg_lvl = f"\n[color=ffd700][b]🎉 ¡NUEVO NIVEL EN EL PASE: Nivel {premios['new_level']}! 🎉[/b][/color]" if premios.get('level_up') else ""
                
                self.lbl_detalle.text += (
                    f"\n\n[color=00ff88][b]¡RECOMPENSA DE PISO![/b][/color]\n"
                    f"+{premios['monedas']} 🪙 Monedas{bonus_text}  |  +{premios['esencia']} ✨ Esencia{msg_ticket}{msg_exp}{msg_lvl}"
                )

            # Control de flujo de la torre
            pantalla_arcade = self.manager.get_screen('arcade_screen')
            total_stages = len(pantalla_arcade.stages) if hasattr(pantalla_arcade, 'stages') else 4

            if stage_index + 1 < total_stages:
                self.btn_accion_principal.text = "SIGUIENTE PISO ➔"
                self.btn_accion_principal.background_color = (0.2, 0.8, 0.2, 1)
                self._callback_actual = lambda x: self._avanzar_piso_arcade(pantalla_arcade, stage_index + 1)
            else:
                self.lbl_titulo.text = "[color=ffbb33][b]¡TORRE COMPLETADA![/b][/color]"
                self.btn_accion_principal.text = "VOLVER A TORRE ARCADE"
                self.btn_accion_principal.background_color = (0.8, 0.6, 0.1, 1)
                self._callback_actual = lambda x: self._ir_a('arcade_screen')

            self.btn_accion_principal.bind(on_release=self._callback_actual)

        else:
            # Derrota en Modo Arcade
            premios = RewardsSystem.otorgar_recompensa(
                victoria=False,
                dificultad_rival=stage_data.get('ai_type', 'IA Normal'),
                turn_count=self.turn_count
            )
            if premios:
                msg_exp = f"  |  +{premios.get('exp_pase', 0)} 🎖️ EXP Pase"
                self.lbl_detalle.text += (
                    f"\n\n[color=ff6666][b]RECOMPENSA DE CONSOLACIÓN[/b][/color]\n"
                    f"+{premios['monedas']} 🪙 Monedas  |  +{premios['esencia']} ✨ Esencia{msg_exp}"
                )

            self.btn_accion_principal.text = "REINTENTAR TORRE 🔄"
            self.btn_accion_principal.background_color = (0.9, 0.3, 0.3, 1)
            self._callback_actual = lambda x: self._reiniciar_torre_arcade()
            self.btn_accion_principal.bind(on_release=self._callback_actual)

    def _procesar_resultado_estandar(self, settings):
        if hasattr(self, '_callback_actual'):
            self.btn_accion_principal.unbind(on_release=self._callback_actual)

        tipo_rival = settings.get('p2', {}).get('tipo', 'IA Normal') if settings else "IA Normal"
        premios = RewardsSystem.otorgar_recompensa(victoria=self.victoria_local, dificultad_rival=tipo_rival, turn_count=self.turn_count)
            
        if premios:
            msg_ticket = f"  |  +{premios['tickets']} 🎟️ Ticket" if premios['tickets'] > 0 else ""
            msg_exp = f"  |  +{premios.get('exp_pase', 0)} 🎖️ EXP Pase"
            msg_lvl = f"\n[color=ffd700][b]🎉 ¡NUEVO NIVEL EN EL PASE: Nivel {premios['new_level']}! 🎉[/b][/color]" if premios.get('level_up') else ""
            self.lbl_detalle.text += (
                f"\n\n[color=00ff88][b]¡BOTÍN DE GUERRA![/b][/color]\n"
                f"+{premios['monedas']} 🪙 Monedas  |  +{premios['esencia']} ✨ Esencia{msg_ticket}{msg_exp}{msg_lvl}"
            )

        self.btn_accion_principal.text = "REVANCHA\n(Volver a selección)"
        self.btn_accion_principal.background_color = (0.2, 0.6, 0.9, 1)
        self._callback_actual = lambda x: self._ir_a('selection_screen')
        self.btn_accion_principal.bind(on_release=self._callback_actual)

    def _avanzar_piso_arcade(self, pantalla_arcade, siguiente_piso):
        pantalla_arcade.current_stage_index = siguiente_piso
        self._ir_a('arcade_screen')

    def _reiniciar_torre_arcade(self):
        pantalla_arcade = self.manager.get_screen('arcade_screen')
        pantalla_arcade.current_stage_index = 0
        self._ir_a('arcade_screen')

    def configurar(self, ganador_nombre: str, perdedor_nombre: str, jugador_local_id: int, ganador_id: int, turn_count: int = 1):
        self.victoria_local = (jugador_local_id == ganador_id) or jugador_local_id < 0
        self.turn_count = max(1, turn_count)
        
        if self.victoria_local:
            self.lbl_titulo.text = "[color=00ff88][b]¡VICTORIA![/b][/color]"
        else:
            self.lbl_titulo.text = "[color=ff4444][b]DERROTA[/b][/color]"
            
        self.lbl_detalle.text = (
            f"[b]{ganador_nombre}[/b] ganó la partida.\n"
            f"La base de [b]{perdedor_nombre}[/b] fue destruida."
        )

    def _ir_a(self, pantalla):
        self.manager.current = pantalla