from typing import List, TYPE_CHECKING
import pygame #

from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement #
from src.engine.ui.Button import Button
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.Slider import Slider  
from src.engine.ui.Toggle import Toggle  
from src.utils import get_center_x # 

# CIRCULAR IMPORT FIX
if TYPE_CHECKING:
    from src.engine.Game import Game

class Options(Scene):
    def build_scene(self, game: "Game") -> List[SceneElement]:
        # THE INITIALIZATION FIX: Must be the absolute first line!
        self.game = game
        
        screen_w = self.screen.get_width()
        
        # Now it is safe to read from self.game.options
        current_vol = self.game.options.get("master_volume", 0.5)
        current_mute = self.game.options.get("is_muted", False)
        
        elements = [
            SimpleText("Options", 48, (screen_w // 2 - 100, 50))
        ]

        # 1. Volume Slider
        elements.append(SimpleText("Master Volume", 20, (screen_w // 2 - 150, 120)))
        elements.append(Slider(
            position=(screen_w // 2 - 150, 150),
            width=300, 
            min_value=0.0, max_value=1.0,
            start_value=current_vol,
            on_change=self._on_volume_change
        ))

        # 2. Mute Toggle
        elements.append(SimpleText("Mutar Áudio", 20, (screen_w // 2 - 150, 210)))
        elements.append(Toggle(
            position=(screen_w // 2 + 50, 210), 
            value=current_mute,
            on_toggle=self._on_mute_change,
        ))

        # 3. Scenario Assistant 
        elements.append(Button(
            image=None,
            text=SimpleText("Assistente de mudança de Cenário/Mundo/Crônica", 12, (0, 0), (255, 215, 0)),
            background_color=(50, 50, 50),
            position=(screen_w // 2 - 150, 300),
            click_function=self._open_scenario_assistant,
            tooltip_text="Facilita a alteração do cenário/mundo - ou mude completamente o tipo de RPG"
        ))

        # 4. Save & Return
        elements.append(Button(
            image=None,
            text=SimpleText("Save & Return", 24, (0, 0), (255, 255, 255)),
            position=(screen_w // 2 - 100, 450),
            click_function=self._return_to_main,
            tooltip_text="Salva quaisquer alterações e retorna para o menu principal"
        ))

        return elements

    def _on_volume_change(self, value: float):  # Add type hint
        """Called repeatedly as the slider is dragged."""
        self.game.options["master_volume"] = value
        self.game.apply_volume()  # Use Game method instead of utils import

    def _on_mute_change(self, is_muted: bool):  # Add type hint  
        """Called when the toggle is clicked."""
        self.game.options["is_muted"] = is_muted
        self.game.apply_volume()  # Use Game method instead of utils import

    def _return_to_main(self):
        """Saves to JSON and returns to the menu."""
        self.game.save_options()  # Already perfect
        from src.engine.scene.MainMenu import MainMenu
        self.game.change_scene(MainMenu(None, self.screen, self.game))


    def _open_scenario_assistant(self):
        from src.engine.scene.ScenarioAssistant import ScenarioAssistant
        self.game.change_scene(ScenarioAssistant(None, self.screen, self.game))