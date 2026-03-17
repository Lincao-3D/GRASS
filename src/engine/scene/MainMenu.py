import os
import json
from typing import List, TYPE_CHECKING
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.SimpleText import SimpleText
from src.utils import get_center_x

if TYPE_CHECKING:
    from src.engine.Game import Game

class MainMenu(Scene):
    def build_scene(self, game: "Game") -> List[SceneElement]:
        self.game = game
        screen_w = self.screen.get_width()
        
        elements = [
            SimpleText("GRASS RPG", 64, (get_center_x(self.screen, 300), 100)),
            Button(
                image=None,
                text=SimpleText("New Game", 24, (0, 0), (255, 255, 255)),
                position=(screen_w // 2 - 100, 250),
                click_function=self.character_creator_scene
            )
        ]

        # Check for save file
        if os.path.exists("save_game.json"):
            elements.append(Button(
                image=None,
                text=SimpleText("Continue", 24, (0, 0), (100, 255, 100)),
                position=(screen_w // 2 - 100, 320),
                click_function=self.load_game_scene
            ))

        elements.append(Button(
            image=None,
            text=SimpleText("Options", 24, (0, 0), (255, 255, 255)),
            position=(screen_w // 2 - 100, 390),
            click_function=self.options_scene
        ))

        return elements

    def load_game_scene(self):
        # The actual restoration logic is usually handled by the Game class
        # But we trigger the transition to ChatScene here
        from src.engine.scene.ChatScene import ChatScene
        # Assuming your Game class has a method to load the file into its state:
        # self.game.load_save_file("save_game.json") 
        self.game.load_session("save_game.json") # Check usage
        self.game.change_scene(ChatScene(self.screen, self.game, self.game.scenario))

    def options_scene(self):
        from src.engine.scene.Options import Options
        self.game.change_scene(Options(None, self.screen, self.game))

    def character_creator_scene(self):
        from src.engine.scene.CharacterCreator import CharacterCreator
        self.game.change_scene(CharacterCreator(None, self.screen, self.game))