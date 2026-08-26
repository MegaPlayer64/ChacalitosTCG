import os
import json
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle

from src.domain.mission_manager import MissionManager
from src.domain.grid_background import FondoCuadriculado
from src.domain.audio_manager import AudioManager

class TarjetaMision(BoxLayout):
    """Componente visual para cada tarjeta de misión diaria."""
    def __init__(self, mision, on_claim_callback, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=140, **kwargs)
        self.mision = mision
        self.on_claim_callback = on_claim_callback

        # Fondo con bordes redondeados
        with self.canvas.before:
            Color(0.12, 0.14, 0.18, 0.95)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[8, 8, 8, 8])
        self.bind(pos=self._update_rect, size=self._update_rect)

        # 1. Encabezado de la misión (Icono + Descripción + Recompensa)
        layout_info = BoxLayout(orientation='horizontal', size_hint_y=0.45, spacing=10)
        
        # Icono según tipo de misión
        m_type = mision.get("type", "")
        if m_type == "deal_damage":
            icon = "⚔️"
        elif m_type == "heal_hp":
            icon = "🩹"
        else:
            icon = "💀"
            
        lbl_desc = Label(
            text=f"[b]{icon} {mision.get('description', '')}[/b]",
            markup=True,
            halign='left',
            valign='middle',
            font_size='15sp',
            size_hint_x=0.65
        )
        lbl_desc.bind(size=lbl_desc.setter('text_size'))
        
        coins = mision.get("reward_coins", 50)
        essence = mision.get("reward_essence", 10)
        lbl_reward = Label(
            text=f"[color=ffd700][b]+{coins} 🪙[/b][/color]  [color=88ccff][b]+{essence} ✨[/b][/color]",
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

        # 2. Barra de progreso visual y botón de acción
        layout_accion = BoxLayout(orientation='horizontal', size_hint_y=0.55, spacing=15)
        
        progress = mision.get("progress", 0)
        required = mision.get("required_amount", 1)
        completed = mision.get("completed", False)
        claimed = mision.get("claimed", False)
        
        pct = min(100, int((progress / required) * 100)) if required > 0 else 100
        bars_filled = int(pct / 5)  # 20 steps
        bar_str = "=" * bars_filled + " " * (20 - bars_filled)
        
        color_progress = "00ff88" if completed else "ffdd44"
        lbl_progreso = Label(
            text=f"[color={color_progress}][b]Progreso:[/b] {progress} / {required} ({pct}%)[/color]\n[size=10sp][color=777777][{bar_str}][/color][/size]",
            markup=True,
            halign='left',
            valign='middle',
            font_size='13sp',
            size_hint_x=0.6
        )
        lbl_progreso.bind(size=lbl_progreso.setter('text_size'))
        layout_accion.add_widget(lbl_progreso)

        # Botón de reclamar o estado
        if claimed:
            btn_accion = Button(
                text="✓ RECLAMADO",
                background_color=(0.3, 0.3, 0.3, 1),
                disabled=True,
                size_hint_x=0.4,
                font_size='14sp'
            )
        elif completed:
            btn_accion = Button(
                text="🎁 RECLAMAR",
                background_color=(0.1, 0.8, 0.3, 1),
                disabled=False,
                size_hint_x=0.4,
                font_size='14sp'
            )
            btn_accion.bind(on_release=lambda x: self.on_claim_callback(mision["id"]))
        else:
            btn_accion = Button(
                text=f"EN PROGRESO",
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ruta_perfil = "src/data/user_profile.json"

        # Fondo cuadriculado del juego
        fondo_grilla = FondoCuadriculado(size=self.size)
        self.add_widget(fondo_grilla, index=0)

        layout_principal = BoxLayout(orientation='vertical', padding=25, spacing=15)

        # 1. Panel Superior (Título y Balances)
        layout_superior = BoxLayout(orientation='vertical', size_hint_y=0.18, spacing=5)
        
        lbl_titulo = Label(
            text="[b][size=24sp]MISIONES DIARIAS[/size][/b]",
            markup=True,
            halign='center',
            size_hint_y=0.55
        )
        self.lbl_divisas = Label(
            text="🪙 Monedas: --  |  ✨ Esencia: --",
            markup=True,
            halign='center',
            font_size='15sp',
            size_hint_y=0.45
        )
        self.lbl_mensaje = Label(
            text="",
            markup=True,
            halign='center',
            font_size='13sp',
            size_hint_y=0.0
        )
        
        layout_superior.add_widget(lbl_titulo)
        layout_superior.add_widget(self.lbl_divisas)
        layout_principal.add_widget(layout_superior)

        # 2. Contenedor de las 3 tarjetas de misión
        self.contenedor_misiones = BoxLayout(orientation='vertical', spacing=12, size_hint_y=0.68)
        layout_principal.add_widget(self.contenedor_misiones)

        # 3. Botón inferior para volver al menú
        layout_inferior = BoxLayout(orientation='horizontal', size_hint_y=0.14, spacing=20)
        btn_volver = Button(
            text="Volver al Menú",
            background_color=(0.7, 0.2, 0.2, 1),
            size_hint_x=0.4,
            pos_hint={'center_x': 0.5},
            font_size='16sp'
        )
        btn_volver.bind(on_release=lambda x: self.cambiar_a_menu())
        layout_inferior.add_widget(btn_volver)
        layout_principal.add_widget(layout_inferior)

        self.add_widget(layout_principal)

    def on_enter(self):
        """Se ejecuta al entrar a la pantalla: obtiene las misiones del día y refresca la vista."""
        self.actualizar_interfaz()

    def actualizar_interfaz(self, mensaje=""):
        self.contenedor_misiones.clear_widgets()

        # Cargar perfil
        perfil = MissionManager._load_profile(self.ruta_perfil)
        coins = perfil.get("coins", 0)
        essence = perfil.get("craft_essence", 0)
        
        self.lbl_divisas.text = f"[color=ffd700][b]🪙 Monedas:[/b] {coins}[/color]   |   [color=88ccff][b]✨ Esencias:[/b] {essence}[/color]"

        # Obtener misiones rotativas
        misiones = MissionManager.get_or_create_daily_missions(self.ruta_perfil)

        for m in misiones:
            tarjeta = TarjetaMision(
                mision=m,
                on_claim_callback=self.reclamar_recompensa
            )
            self.contenedor_misiones.add_widget(tarjeta)

    def reclamar_recompensa(self, mission_id):
        resultado = MissionManager.claim_reward(mission_id, self.ruta_perfil)
        if resultado.get("exito"):
            AudioManager().play_sfx("heal")
            self.actualizar_interfaz()
        else:
            AudioManager().play_sfx("error1")

    def cambiar_a_menu(self):
        self.manager.current = 'menu_screen'
