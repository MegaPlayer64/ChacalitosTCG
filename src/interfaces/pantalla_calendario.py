"""
Pantalla y Modal de Calendario Semanal de Recompensas (Weekly Calendar).
Permite a los jugadores recibir recursos (Oro, Esencia, Tickets) cada día,
y en el Día 7 otorga una copia de la carta N°99 Richi (Discurso).
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, RoundedRectangle, Line

from src.domain.weekly_calendar_manager import WeeklyCalendarManager
from src.domain.grid_background import FondoCuadriculado
from src.domain.audio_manager import AudioManager


class TarjetaDiaCalendario(BoxLayout):
    """Tarjeta individual para cada uno de los 7 días del calendario."""
    def __init__(self, day_info, on_claim_callback=None, **kwargs):
        is_grand = day_info.get("is_grand_prize", False)
        target_width = 175 if is_grand else 115
        
        super().__init__(
            orientation='vertical',
            size_hint=(None, 1),
            width=target_width,
            padding=[8, 10, 8, 10],
            spacing=6,
            **kwargs
        )
        self.day_info = day_info
        self.on_claim_callback = on_claim_callback
        self._build_card()

    def _build_card(self):
        self.clear_widgets()
        status = self.day_info.get("status", "locked")
        is_grand = self.day_info.get("is_grand_prize", False)
        day_num = self.day_info.get("day", 1)

        # Fondo con color según estado
        self.canvas.before.clear()
        with self.canvas.before:
            if status == "claimed":
                Color(0.14, 0.26, 0.18, 0.95)
            elif status == "available":
                if is_grand:
                    Color(0.35, 0.22, 0.50, 0.98)
                else:
                    Color(0.18, 0.35, 0.65, 0.98)
            else:
                Color(0.11, 0.13, 0.17, 0.95)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10, 10, 10, 10])

            # Borde dorado para el Día 7 o Día disponible
            if is_grand:
                Color(1.0, 0.84, 0.0, 0.8)
                self.bg_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 10], width=1.5)
            elif status == "available":
                Color(0.2, 0.8, 1.0, 0.8)
                self.bg_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 10], width=1.2)
            else:
                self.bg_line = None

        self.bind(pos=self._update_geom, size=self._update_geom)

        # 1. Cabecera del día
        if is_grand:
            lbl_day = Label(
                text="[color=ffd700][b]⭐ DÍA 7 ⭐[/b][/color]\n[size=10sp][color=ffffff]GRAN PREMIO[/color][/size]",
                markup=True,
                font_size='13sp',
                halign='center',
                size_hint_y=0.22
            )
        else:
            lbl_day = Label(
                text=f"[b]Día {day_num}[/b]",
                markup=True,
                font_size='14sp',
                size_hint_y=0.18
            )
        self.add_widget(lbl_day)

        # 2. Ícono central o miniatura de carta
        if is_grand:
            # Intentar cargar miniatura de arte de CardArtWidget para Richi (Discurso)
            art_added = False
            try:
                from src.interfaces.widgets.card_art_widget import CardArtWidget
                card_art = CardArtWidget(card_id="99", is_detail=False, size_hint=(None, None), size=(72, 72))
                box_art = BoxLayout(size_hint_y=0.38, padding=[0, 2, 0, 2])
                box_art.add_widget(card_art)
                self.add_widget(box_art)
                art_added = True
            except Exception:
                pass

            if not art_added:
                lbl_icon = Label(text="🎴", font_size='36sp', size_hint_y=0.38)
                self.add_widget(lbl_icon)
        else:
            icon = self.day_info.get("icon", "🎁")
            lbl_icon = Label(text=icon, font_size='32sp', size_hint_y=0.40)
            self.add_widget(lbl_icon)

        # 3. Etiqueta de recompensa
        lbl_reward = Label(
            text=f"[b]{self.day_info.get('label', 'Recompensa')}[/b]",
            markup=True,
            font_size='12sp',
            halign='center',
            valign='middle',
            size_hint_y=0.22
        )
        lbl_reward.bind(size=lbl_reward.setter('text_size'))
        self.add_widget(lbl_reward)

        # 4. Indicador de estado / Botón pequeño
        if status == "claimed":
            lbl_status = Label(
                text="[color=00ff88][b]✓ Reclamado[/b][/color]",
                markup=True,
                font_size='11sp',
                size_hint_y=0.18
            )
            self.add_widget(lbl_status)
        elif status == "available":
            btn_mini = Button(
                text="🎁 Reclamar",
                background_color=(0.15, 0.8, 0.35, 1),
                font_size='11sp',
                size_hint_y=0.20
            )
            if self.on_claim_callback:
                btn_mini.bind(on_release=lambda x: self.on_claim_callback())
            self.add_widget(btn_mini)
        else:
            lbl_status = Label(
                text="[color=777777]🔒 Bloqueado[/color]",
                markup=True,
                font_size='11sp',
                size_hint_y=0.18
            )
            self.add_widget(lbl_status)

    def _update_geom(self, *args):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
        if hasattr(self, 'bg_line') and self.bg_line:
            self.bg_line.rounded_rectangle = [self.x, self.y, self.width, self.height, 10]


class PantallaCalendario(Screen):
    """Pantalla interactiva del Calendario Semanal de Recompensas."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calendar_manager = WeeklyCalendarManager()

        # Fondo cuadriculado del motor
        fondo = FondoCuadriculado(size=self.size)
        self.add_widget(fondo, index=0)

        self._build_ui()

    def on_enter(self):
        """Refresca el estado al entrar en la pantalla."""
        self.calendar_manager = WeeklyCalendarManager()
        self.refresh_ui()

    def _build_ui(self):
        self.main_layout = BoxLayout(orientation='vertical', padding=[20, 15, 20, 15], spacing=12)

        # 1. HEADER: Título, Ciclo y Monedas
        self.header = BoxLayout(orientation='horizontal', size_hint_y=0.14, spacing=10)
        
        box_titles = BoxLayout(orientation='vertical', size_hint_x=0.55, spacing=2)
        self.lbl_title = Label(
            text="[b]CALENDARIO SEMANAL DE RECOMPENSAS[/b]",
            markup=True,
            font_size='22sp',
            halign='left',
            valign='middle'
        )
        self.lbl_title.bind(size=self.lbl_title.setter('text_size'))
        
        self.lbl_subtitle = Label(
            text="[color=aaaaaa]Inicia sesión cada día para acumular recompensas y desbloquear a Richi (Discurso).[/color]",
            markup=True,
            font_size='12sp',
            halign='left',
            valign='middle'
        )
        self.lbl_subtitle.bind(size=self.lbl_subtitle.setter('text_size'))
        
        box_titles.add_widget(self.lbl_title)
        box_titles.add_widget(self.lbl_subtitle)

        self.lbl_currencies = Label(
            text="🪙 0 | ✨ 0 | 🎟️ 0",
            markup=True,
            font_size='16sp',
            size_hint_x=0.45,
            halign='right',
            valign='middle'
        )
        self.lbl_currencies.bind(size=self.lbl_currencies.setter('text_size'))

        self.header.add_widget(box_titles)
        self.header.add_widget(self.lbl_currencies)
        self.main_layout.add_widget(self.header)

        # 2. CONTENEDOR DE TARJETAS HORIZONTALES (Días 1 al 7)
        self.scroll_days = ScrollView(size_hint_y=0.58, do_scroll_x=True, do_scroll_y=False)
        self.box_cards = BoxLayout(
            orientation='horizontal',
            spacing=10,
            size_hint_x=None,
            padding=[5, 5, 5, 5]
        )
        self.box_cards.bind(minimum_width=self.box_cards.setter('width'))
        self.scroll_days.add_widget(self.box_cards)
        self.main_layout.add_widget(self.scroll_days)

        # 3. ÁREA DE ACCIÓN Y MENSAJES
        self.box_action = BoxLayout(orientation='vertical', size_hint_y=0.16, spacing=6)
        
        self.lbl_message = Label(
            text="",
            markup=True,
            font_size='13sp',
            halign='center',
            size_hint_y=0.35
        )
        self.lbl_message.bind(size=self.lbl_message.setter('text_size'))

        self.btn_claim_main = Button(
            text="🎁 RECLAMAR RECOMPENSA DE HOY",
            size_hint=(0.5, 0.65),
            pos_hint={'center_x': 0.5},
            background_color=(0.15, 0.75, 0.35, 1),
            font_size='15sp'
        )
        self.btn_claim_main.bind(on_release=lambda x: self.claim_today())

        self.box_action.add_widget(self.lbl_message)
        self.box_action.add_widget(self.btn_claim_main)
        self.main_layout.add_widget(self.box_action)

        # 4. FOOTER: Botón de volver
        self.footer = BoxLayout(size_hint_y=0.12)
        self.btn_back = Button(
            text="< Volver al Menú Principal",
            size_hint=(0.35, 0.9),
            pos_hint={'center_x': 0.5},
            background_color=(0.7, 0.2, 0.2, 1),
            font_size='15sp'
        )
        self.btn_back.bind(on_release=self.go_back)
        self.footer.add_widget(self.btn_back)
        self.main_layout.add_widget(self.footer)

        self.add_widget(self.main_layout)

    def refresh_ui(self):
        """Actualiza todas las tarjetas y estado de la pantalla."""
        st = self.calendar_manager.get_status()

        coins = st.get("coins", 0)
        essence = st.get("essence", 0)
        tickets = st.get("tickets", 0)
        cycle = st.get("current_cycle", 1)
        cur_day = st.get("current_day", 1)
        can_claim = st.get("can_claim_today", False)

        # Header
        self.lbl_subtitle.text = f"[color=aaaaaa]Semana / Ciclo #{cycle} • Conéctate cada día para avanzar el calendario.[/color]"
        self.lbl_currencies.text = (
            f"[color=ffd700][b]🪙 {coins}[/b][/color]  "
            f"[color=88ccff][b]✨ {essence}[/b][/color]  "
            f"[color=ff99bb][b]🎟️ {tickets}[/b][/color]"
        )

        # Reconstruir tarjetas de los 7 días
        self.box_cards.clear_widgets()
        for day_info in st.get("days_info", []):
            card = TarjetaDiaCalendario(day_info=day_info, on_claim_callback=self.claim_today)
            self.box_cards.add_widget(card)

        # Botón de reclamo principal
        if can_claim:
            cur_reward = next((d for d in st.get("days_info", []) if d["day"] == cur_day), {})
            reward_label = cur_reward.get("label", "Recompensa")
            self.btn_claim_main.text = f"🎁 RECLAMAR DÍA {cur_day}: {reward_label}"
            self.btn_claim_main.disabled = False
            self.btn_claim_main.background_color = (0.15, 0.8, 0.35, 1)
            self.lbl_message.text = f"[color=00ff88][b]¡Tienes disponible la recompensa del Día {cur_day}![/b][/color]"
        else:
            if len(st.get("claimed_days", [])) >= 7:
                self.btn_claim_main.text = "🎉 ¡Semana Completada! Mañana comenzará un nuevo ciclo."
                self.lbl_message.text = "[color=ffd700]¡Felicidades! Has completado los 7 días del calendario semanal.[/color]"
            else:
                next_day = min(7, cur_day + 1)
                self.btn_claim_main.text = f"✓ Recompensa de hoy reclamada (Vuelve mañana para el Día {next_day})"
                self.lbl_message.text = f"[color=aaaaaa]Has reclamado tu recompensa de hoy. ¡Vuelve mañana para continuar con el Día {next_day}![/color]"
            self.btn_claim_main.disabled = True
            self.btn_claim_main.background_color = (0.35, 0.4, 0.45, 0.8)

    def claim_today(self):
        """Ejecuta el reclamo del día actual y reproduce feedback sonoro/visual."""
        res = self.calendar_manager.claim_today()
        if res.get("success"):
            try:
                AudioManager().play_sfx("heal")
            except Exception:
                pass
            self.refresh_ui()
            self.lbl_message.text = f"[color=00ff88][b]🎉 {res.get('message', '¡Recompensa reclamada!')}[/b][/color]"
        else:
            try:
                AudioManager().play_sfx("error1")
            except Exception:
                pass
            self.lbl_message.text = f"[color=ff6666]{res.get('message', 'No se pudo reclamar.')}[/color]"

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


class WeeklyCalendarModal(ModalView):
    """Modal emergente opcional para desplegar el calendario directamente sobre cualquier pantalla."""
    def __init__(self, **kwargs):
        super().__init__(size_hint=(0.95, 0.9), auto_dismiss=True, **kwargs)
        self.calendar_manager = WeeklyCalendarManager()

        self.box_content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        with self.box_content.canvas.before:
            Color(0.12, 0.14, 0.18, 0.98)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12, 12, 12, 12])
        self.box_content.bind(
            pos=lambda inst, v: setattr(self.bg_rect, 'pos', inst.pos),
            size=lambda inst, v: setattr(self.bg_rect, 'size', inst.size)
        )

        # Header modal
        header = BoxLayout(orientation='horizontal', size_hint_y=0.15)
        lbl_mtitle = Label(
            text="[b]📅 CALENDARIO SEMANAL DE RECOMPENSAS[/b]",
            markup=True,
            font_size='18sp',
            halign='left'
        )
        lbl_mtitle.bind(size=lbl_mtitle.setter('text_size'))
        header.add_widget(lbl_mtitle)
        self.box_content.add_widget(header)

        # Scroll de días
        self.scroll = ScrollView(size_hint_y=0.6, do_scroll_x=True, do_scroll_y=False)
        self.box_days = BoxLayout(orientation='horizontal', spacing=8, size_hint_x=None)
        self.box_days.bind(minimum_width=self.box_days.setter('width'))
        self.scroll.add_widget(self.box_days)
        self.box_content.add_widget(self.scroll)

        # Botón de reclamo y cerrar
        self.btn_claim = Button(
            text="🎁 Reclamar Recompensa de Hoy",
            size_hint=(0.6, 0.13),
            pos_hint={'center_x': 0.5},
            background_color=(0.15, 0.8, 0.35, 1)
        )
        self.btn_claim.bind(on_release=lambda x: self._on_claim())
        self.box_content.add_widget(self.btn_claim)

        btn_close = Button(
            text="Cerrar",
            size_hint=(0.3, 0.12),
            pos_hint={'center_x': 0.5},
            background_color=(0.6, 0.2, 0.2, 1)
        )
        btn_close.bind(on_release=self.dismiss)
        self.box_content.add_widget(btn_close)

        self.add_widget(self.box_content)
        self.refresh()

    def refresh(self):
        st = self.calendar_manager.get_status()
        self.box_days.clear_widgets()
        for d in st.get("days_info", []):
            card = TarjetaDiaCalendario(day_info=d, on_claim_callback=self._on_claim)
            self.box_days.add_widget(card)

        if st.get("can_claim_today"):
            self.btn_claim.disabled = False
            cur_day = st.get("current_day", 1)
            self.btn_claim.text = f"🎁 Reclamar Recompensa del Día {cur_day}"
        else:
            self.btn_claim.disabled = True
            self.btn_claim.text = "✓ Recompensa de hoy ya reclamada"

    def _on_claim(self):
        res = self.calendar_manager.claim_today()
        if res.get("success"):
            try:
                AudioManager().play_sfx("heal")
            except Exception:
                pass
            self.refresh()

