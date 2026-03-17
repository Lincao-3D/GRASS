from src.engine.scene.Scene import Scene
from src.engine.ui.Button import Button
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.Slider import Slider  
from src.engine.ui.Toggle import Toggle  

class Options(Scene):
    def build_scene(self, game: "Game"):
        self.game = game
        screen_w = self.screen.get_width()
        
        elements = [
            SimpleText("Options", 48, (screen_w // 2 - 100, 50))
        ]

        # 1. Volume Slider
        elements.append(SimpleText("Master Volume", 20, (screen_w // 2 - 150, 120)))
        elements.append(Slider(
            position=(screen_w // 2 - 150, 150),
            width=300, 
            min_value=0.0, max_value=1.0,
            start_value=self.game.options.get("master_volume", 0.5),
            on_change=self._on_volume_change
        ))

        # 2. Mute Toggle
        elements.append(SimpleText("Mute Audio", 20, (screen_w // 2 - 150, 210)))
        elements.append(Toggle(
            position=(screen_w // 2 + 50, 210), 
            value=self.game.options.get("is_muted", False),
            on_toggle=self._on_mute_change
        ))

        # 3. Scenario Assistant (TODO 2)
        elements.append(Button(
            image=None,
            text=SimpleText("Cenário/Mundo Assistant", 18, (0, 0), (255, 215, 0)),
            background_color=(50, 50, 50),
            position=(screen_w // 2 - 150, 300),
            click_function=self._open_scenario_assistant
        ))

        # 4. Save & Return
        elements.append(Button(
            image=None,
            text=SimpleText("Save & Return", 24, (0, 0), (255, 255, 255)),
            position=(screen_w // 2 - 100, 450),
            click_function=self._return_to_main
        ))

        return elements

    def _on_volume_change(self, value):
        self.game.options["master_volume"] = value
        from src.utils import apply_volume
        apply_volume()

    def _on_mute_change(self, is_muted):
        self.game.options["is_muted"] = is_muted
        from src.utils import apply_volume
        apply_volume()

    def _return_to_main(self):
        self.game.save_options()
        from src.engine.scene.MainMenu import MainMenu
        self.game.change_scene(MainMenu(None, self.screen, self.game))

    def _open_scenario_assistant(self):
        from src.engine.scene.ScenarioAssistant import ScenarioAssistant
        self.game.change_scene(ScenarioAssistant(None, self.screen, self.game))