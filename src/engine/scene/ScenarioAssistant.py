# Create this file at: src/engine/scene/ScenarioAssistant.py
import pygame
from src.engine.scene.Scene import Scene
from src.engine.ui.Button import Button
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.TextInput import TextInput

class ScenarioAssistant(Scene):
    def build_scene(self, game):
        sw, sh = self.screen.get_width(), self.screen.get_height()
        
        # We create a centered "Iframe" look using coordinates
        # Width: 600, Height: 400
        modal_x = (sw - 600) // 2
        modal_y = (sh - 400) // 2

        elements = [
            # A background label for the modal area
            SimpleText("World Generator Assistant", 32, (modal_x + 50, modal_y + 20)),
            
            # Example Input for the prompt
            TextInput(
                position=(modal_x + 50, modal_y + 100),
                width=500,
                # placeholder="Describe your world..."
            ),

            Button(
                text=SimpleText("Back to Options", 20, (0,0), (255,255,255)),
                position=(modal_x + 50, modal_y + 320),
                click_function=self._close
            )
        ]
        return elements

    def _close(self):
        from src.engine.scene.Options import Options
        self.game.change_scene(Options(None, self.screen, self.game))

    def update(self):
        # Draw a dark overlay over the previous scene (optional visual effect)
        self.screen.fill((20, 20, 20, 180)) 
        super().update()