# src/interfaces/battle_pass_view.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, RoundedRectangle
from src.domain.battle_pass_manager import BattlePassManager
from src.domain.grid_background import FondoCuadriculado
from src.domain.audio_manager import AudioManager

class BattlePassView(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bp_manager = BattlePassManager()

        # 0. Fondo cuadriculado
        fondo_grilla = FondoCuadriculado(size=self.size)
        self.add_widget(fondo_grilla, index=0)

        self.build_ui()

    def on_enter(self):
        """Se ejecuta al abrir la pantalla para refrescar el progreso y recompensas."""
        self.bp_manager = BattlePassManager()
        self.refresh_ui()

    def build_ui(self):
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 1. HEADER: Nombre de Temporada y Monedas
        self.header = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        self.lbl_title = Label(
            text="[b]PASE DE BATALLA[/b]", 
            markup=True, 
            font_size='24sp', 
            size_hint_x=0.5,
            halign='left',
            valign='middle'
        )
        self.lbl_title.bind(size=self.lbl_title.setter('text_size'))
        
        self.lbl_currencies = Label(
            text="🪙 0 | ✨ 0 | 🎟️ 0", 
            markup=True,
            font_size='16sp', 
            size_hint_x=0.5,
            halign='right',
            valign='middle'
        )
        self.lbl_currencies.bind(size=self.lbl_currencies.setter('text_size'))
        
        self.header.add_widget(self.lbl_title)
        self.header.add_widget(self.lbl_currencies)
        self.main_layout.add_widget(self.header)

        # 2. BARRA DE PROGRESO DE NIVEL
        self.progress_box = BoxLayout(orientation='vertical', size_hint_y=0.15, spacing=5)
        self.lbl_level_info = Label(text="Nivel 1 | EXP: 0 / 100", font_size='16sp', size_hint_y=0.4, markup=True)
        self.pb_exp = ProgressBar(max=100, value=0, size_hint_y=0.6)
        
        self.progress_box.add_widget(self.lbl_level_info)
        self.progress_box.add_widget(self.pb_exp)
        self.main_layout.add_widget(self.progress_box)

        # 3. TRACK HORIZONTAL DE RECOMPENSAS (Niveles 1 al 30)
        self.scroll_rewards = ScrollView(size_hint_y=0.55, do_scroll_x=True, do_scroll_y=False)
        self.grid_rewards = GridLayout(rows=1, spacing=15, size_hint_x=None, padding=[10, 10])
        self.grid_rewards.bind(minimum_width=self.grid_rewards.setter('width'))
        self.scroll_rewards.add_widget(self.grid_rewards)
        self.main_layout.add_widget(self.scroll_rewards)

        # 4. BOTÓN DE VOLVER AL MENÚ
        self.footer = BoxLayout(size_hint_y=0.15)
        self.btn_back = Button(
            text="< Volver al Menú Principal", 
            size_hint=(0.35, 0.8), 
            pos_hint={'center_x': 0.5},
            background_color=(0.7, 0.2, 0.2, 1),
            font_size='16sp'
        )
        self.btn_back.bind(on_release=self.go_back)
        self.footer.add_widget(self.btn_back)
        self.main_layout.add_widget(self.footer)

        self.add_widget(self.main_layout)

    def refresh_ui(self):
        """Carga los datos actualizados del JSON y renderiza las tarjetas de recompensa."""
        bp = self.bp_manager.profile_data.get("battle_pass", {})
        currencies = self.bp_manager.profile_data.get("currencies", {})
        config = self.bp_manager.season_config
        rewards_cfg = config.get("rewards", {})

        current_lvl = bp.get("level", 1)
        current_exp = bp.get("exp", 0)
        exp_per_lvl = config.get("exp_per_level", 100)
        claimed_lvls = bp.get("claimed_levels", [])

        coins = self.bp_manager.profile_data.get("coins", currencies.get("coins", 0))
        essence = self.bp_manager.profile_data.get("craft_essence", currencies.get("essence", 0))
        tickets = self.bp_manager.profile_data.get("tickets", currencies.get("tickets", 0))

        # Actualizar Header
        self.lbl_title.text = f"[b]{config.get('season_name', 'Pase de Batalla')}[/b]"
        self.lbl_currencies.text = (
            f"[color=ffd700][b]🪙 {coins}[/b][/color]  "
            f"[color=88ccff][b]✨ {essence}[/b][/color]  "
            f"[color=ff99bb][b]🎟️ {tickets}[/b][/color]"
        )

        # Actualizar Barra
        self.lbl_level_info.text = f"[b]Nivel {current_lvl} / {config.get('max_level', 30)}[/b]  |  EXP: {current_exp} / {exp_per_lvl}"
        self.pb_exp.max = exp_per_lvl
        self.pb_exp.value = current_exp

        # Renderizar Tarjetas de Niveles
        self.grid_rewards.clear_widgets()
        max_lvl = config.get("max_level", 30)

        for lvl in range(1, max_lvl + 1):
            lvl_str = str(lvl)
            reward_data = rewards_cfg.get(lvl_str, None)

            # Tarjeta de nivel
            card = BoxLayout(orientation='vertical', size_hint=(None, 1), width=150, padding=10, spacing=6)
            
            # Fondo según estado
            with card.canvas.before:
                if lvl in claimed_lvls:
                    Color(0.18, 0.28, 0.2, 0.95)
                elif lvl <= current_lvl:
                    Color(0.2, 0.35, 0.65, 0.95)
                else:
                    Color(0.12, 0.14, 0.18, 0.95)
                rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[8, 8, 8, 8])
            card.bind(pos=lambda inst, v, r=rect: setattr(r, 'pos', inst.pos),
                      size=lambda inst, v, r=rect: setattr(r, 'size', inst.size))

            lbl_num = Label(text=f"[b]Nivel {lvl}[/b]", font_size='15sp', markup=True, size_hint_y=0.25)
            card.add_widget(lbl_num)

            if reward_data:
                lbl_desc = Label(
                    text=f"[b]{reward_data.get('label', 'Recompensa')}[/b]", 
                    font_size='12sp', 
                    markup=True,
                    halign='center', 
                    valign='middle',
                    size_hint_y=0.45
                )
                lbl_desc.bind(size=lbl_desc.setter('text_size'))
                card.add_widget(lbl_desc)

                # Botón de Reclamar / Estado
                if lvl in claimed_lvls:
                    btn_action = Button(text="✓ Reclamado", disabled=True, size_hint_y=0.3, font_size='12sp')
                elif lvl <= current_lvl:
                    btn_action = Button(
                        text="🎁 Reclamar", 
                        size_hint_y=0.3, 
                        background_color=(0.2, 0.8, 0.3, 1),
                        font_size='12sp'
                    )
                    btn_action.bind(on_release=lambda instance, l=lvl: self.claim_level(l))
                else:
                    btn_action = Button(text="🔒 Bloqueado", disabled=True, size_hint_y=0.3, font_size='12sp')
                
                card.add_widget(btn_action)
            else:
                lbl_empty = Label(text="[color=777777]Sin Recompensa[/color]", markup=True, font_size='11sp', size_hint_y=0.75)
                card.add_widget(lbl_empty)

            self.grid_rewards.add_widget(card)

    def claim_level(self, level: int):
        if self.bp_manager.claim_reward(level):
            try:
                AudioManager().play_sfx("heal")
            except Exception:
                pass
            self.refresh_ui()
        else:
            try:
                AudioManager().play_sfx("error1")
            except Exception:
                pass

    def go_back(self, instance=None):
        try:
            AudioManager().play_sfx("select1")
        except Exception:
            pass
        if self.manager:
            if 'menu_screen' in self.manager.screen_names:
                self.manager.current = 'menu_screen'
            else:
                self.manager.current = 'main_menu'