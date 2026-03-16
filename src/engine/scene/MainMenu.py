from typing import List, Optional
import pygame
import os
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.ImageTransformStrategy import ColorInverter
from src.engine.ui.SimpleText import SimpleText
from src.utils import get_center_x, get_default_font

class MainMenu(Scene):
    def build_scene(self, game) -> List[SceneElement]:
        elements = [
            SimpleText("G.R.A.S.S", 48, (get_center_x(self.screen, 200), 50)),
            Button(
                image=None, position=(get_center_x(self.screen, 200), 150),
                text=SimpleText("New Game!", 30, (0,0), (0,0,0)),
                background_color=(255,255,255),
                click_function=self.character_creator_scene
            )
        ]

        # Dynamic button for continuing/continue
        if os.path.exists("saves/current_adventure.dat"):
            elements.append(Button(
                image=None, position=(get_center_x(self.screen, 200), 230),
                text=SimpleText("Continue Adventure", 30, (0,0), (0,0,0)),
                background_color=(100,255,100), # Verde suave para destacar
                click_function=self.game.load_session
            ))

        elements.append(Button(
            image=None, position=(get_center_x(self.screen, 200), 310),
            text=SimpleText("Options", 30, (0,0), (0,0,0)),
            background_color=(255,255,255),
            click_function=self.options_scene
        ))
        return elements
    
    def options_scene(self):
        from src.engine.scene.Options import Options
        self.game.change_scene(Options(None,self.screen,self.game))

    def character_creator_scene(self):
        from src.engine.scene.CharacterCreator import CharacterCreator
        self.game.change_scene(CharacterCreator(None,self.screen,self.game))
