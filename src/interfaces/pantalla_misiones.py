import os
import json
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle

from src.domain.mission_manager import MissionManager
from src.domain.grid_background import FondoCuadriculado
from src.domain.audio_manager import AudioManager


class TarjetaMision(BoxLayout):
    """Componente visual con estilo para cada tarjeta de misión diaria."""
    def __init__(self, mision, on_claim_callback, **kwargs):
        super().__init__(
            orientation='vertical', 
            padding=15, 
            spacing=8, 
            size_hint_y=None, 
            height=145, 
            **kwargs
        )
        self.mision = mision
        self.on_claim_callback = on_claim_callback

        # Fondo visual con bordes redondeados
        with self.canvas.before:
            Color(0.12, 0.14, 0.18, 0.95)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10, 10, 10, 10])
        self.bind(pos=self._update_rect, size=self._update_rect)

        self._build_card_ui()

    def _build_card_ui(self):
        self.clear_widgets()

        # 1. ENCABEZADO: Ícono, Descripción y Recompensas
        layout_info = BoxLayout(orientation='horizontal', size_hint_y=0.45, spacing=10)
        
        # Selección de ícono según el tipo de misión
        m_type = self.mision.get("type", "")
        if m_type == "deal_damage":
            icon = "⚔️"
        elif m_type == "heal_hp":
            icon = "🩹"
        elif m_type == "win_match":
            icon = "🏆"
        else:
            icon = "💀"
            
        lbl_desc = Label(
            text=f"[b]{icon} {self.mision.get('description', self.mision.get('title', 'Misión'))}[/b]",
            markup=True,
            halign='left',
            valign='middle',
            font_size='15sp',
            size_hint_x=0.65
        )
        lbl_desc.bind(size=lbl_desc.setter('text_size'))
        
        coins = self.mision.get("reward_coins", self.mision.get("coins", 50))
        essence = self.mision.get("reward_essence", self.mision.get("essence", 10))
        lbl_reward = Label(
            text=f"[color=ffd700][b]+{coins} 🪙[/b][/color]   [color=88ccff][b]+{essence} ✨[/b][/color]",
            markup=True,
            halign='right',
            valign='middle',
            font_size='14sp',
            size_hint_x=0.35
        )
        lbl_reward.bind(size=lbl_reward.setter('text_size'))
        
        layout_info.add_widget(lbl_desc)
        layout_info.add_widget(lbl_reward)
        self.add_widget(layout_info)

        # 2. ACCIÓN: Barra de progreso y Botón
        layout_accion = BoxLayout(orientation='horizontal', size_hint_y=0.55, spacing=15)
        
        progress = self.mision.get("progress", self.mision.get("current", 0))
        required = self.mision.get("required_amount", self.mision.get("target", 1))
        completed = self.mision.get("completed", progress >= required)
        claimed = self.mision.get("claimed", self.mision.get("status") == "completed")
        
        pct = min(100, int((progress / required) * 100)) if required > 0 else 100
        bars_filled = int(pct / 5)  # 20 pasos de progreso
        bar_str = "=" * bars_filled + " " * (20 - bars_filled)
        
        color_progress = "00ff88" if completed else "ffdd44"
        lbl_progreso = Label(
            text=f"[color={color_progress}][b]Progreso:[/b] {progress} / {required} ({pct}%)[/color]\n"
                 f"[size=10sp][color=777777][{bar_str}][/color][/size]",
            markup=True,
            halign='left',
            valign='middle',
            font_size='13sp',
            size_hint_x=0.6
        )
        lbl_progreso.bind(size=lbl_progreso.setter('text_size'))
        layout_accion.add_widget(lbl_progreso)

        # Estado del Botón
        m_id = self.mision.get("id", self.mision.get("mission_id"))
        if claimed:
            btn_accion = Button(
                text="✓ RECLAMADO",
                background_color=(0.3, 0.3, 0.3, 1),
                disabled=True,
                size_hint_x=0.4,
                font_size='14sp'
            )
        elif completed or progress >= required:
            btn_accion = Button(
                text="🎁 RECLAMAR",
                background_color=(0.1, 0.8, 0.3, 1),
                disabled=False,
                size_hint_x=0.4,
                font_size='14sp'
            )
            btn_accion.bind(on_release=lambda x: self.on_claim_callback(m_id))
        else:
            btn_accion = Button(
                text="EN PROGRESO",
                background_color=(0.35, 0.35, 0.4, 1),
                disabled=True,
                size_hint_x=0.4,
                font_size='13sp'
            )
            
        layout_accion.add_widget(btn_accion)
        self.add_widget(layout_accion)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class PantallaMisiones(Screen):
    """Pantalla principal de Misiones Diarias unificada."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ruta_perfil = "src/data/user_profile.json"

        # 1. Fondo cuadriculado interactivo
        fondo_grilla = FondoCuadriculado(size=self.size)
        self.add_widget(fondo_grilla, index=0)

        layout_principal = BoxLayout(orientation='vertical', padding=25, spacing=15)

        # 2. Panel Superior (Título y Divisas)
        layout_superior = BoxLayout(orientation='vertical', size_hint_y=0.15, spacing=5)
        
        lbl_titulo = Label(
            text="[b][size=24sp]MISIONES DIARIAS[/size][/b]",
            markup=True,
            halign='center',
            size_hint_y=0.55
        )
        self.lbl_divisas = Label(
            text="🪙 Monedas: --   |   ✨ Esencia: --",
            markup=True,
            halign='center',
            font_size='15sp',
            size_hint_y=0.45
        )
        
        layout_superior.add_widget(lbl_titulo)
        layout_superior.add_widget(self.lbl_divisas)
        layout_principal.add_widget(layout_superior)

        # 3. Contenedor con Scroll para las Tarjetas
        self.scroll_misiones = ScrollView(size_hint_y=0.72)
        self.grid_misiones = GridLayout(cols=1, spacing=12, size_hint_y=None)
        self.grid_misiones.bind(minimum_height=self.grid_misiones.setter('height'))
        self.scroll_misiones.add_widget(self.grid_misiones)
        
        layout_principal.add_widget(self.scroll_misiones)

        # 4. Panel Inferior (Botón Volver)
        layout_inferior = BoxLayout(orientation='horizontal', size_hint_y=0.13, spacing=20)
        btn_volver = Button(
            text="< Volver al Menú",
            background_color=(0.7, 0.2, 0.2, 1),
            size_hint_x=0.4,
            pos_hint={'center_x': 0.5},
            font_size='16sp'
        )
        btn_volver.bind(on_release=lambda x: self.go_back())
        layout_inferior.add_widget(btn_volver)
        layout_principal.add_widget(layout_inferior)

        self.add_widget(layout_principal)

    def on_enter(self):
        """Refresca los datos del perfil y las misiones rotativas al entrar."""
        self.actualizar_interfaz()

    def actualizar_interfaz(self):
        self.grid_misiones.clear_widgets()

        # Cargar balance de perfil
        perfil = MissionManager._load_profile(self.ruta_perfil)
        coins = perfil.get("coins", 0)
        essence = perfil.get("craft_essence", perfil.get("essence", 0))
        
        self.lbl_divisas.text = f"[color=ffd700][b]🪙 Monedas:[/b] {coins}[/color]   |   [color=88ccff][b]✨ Esencias:[/b] {essence}[/color]"

        # Obtener o crear misiones diarias reales
        misiones = MissionManager.get_or_create_daily_missions(self.ruta_perfil)

        # Si retorna lista o diccionario, iterar correctamente
        if isinstance(misiones, dict):
            misiones_list = list(misiones.values())
        else:
            misiones_list = misiones

        for m in misiones_list:
            tarjeta = TarjetaMision(
                mision=m,
                on_claim_callback=self.reclamar_recompensa
            )
            self.grid_misiones.add_widget(tarjeta)

    def reclamar_recompensa(self, mission_id):
        resultado = MissionManager.claim_reward(mission_id, self.ruta_perfil)
        if resultado.get("exito", False) or resultado.get("success", False):
            try:
                AudioManager().play_sfx("heal")
            except Exception:
                pass
            self.actualizar_interfaz()
        else:
            try:
                AudioManager().play_sfx("error1")
            except Exception:
                pass

    def go_back(self):
        try:
            AudioManager().play_sfx("select1")
        except Exception:
            pass
        if self.manager:
            if 'menu_screen' in self.manager.screen_names:
                self.manager.current = 'menu_screen'
            else:
                self.manager.current = 'main_menu'