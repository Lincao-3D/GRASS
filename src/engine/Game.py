import json
import os
import pickle
import pygame
from typing import Optional, Dict, Any
from src.engine.ai.chat import Chat
from src.engine.scene.MainMenu import MainMenu
from src.utils import apply_volume

class Game:
    def __init__(self, scenario, start_player=None):
        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        self.scene = None
        self.scenario = scenario
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.options = self.load_options()
        pygame.mixer.init()
        apply_volume()
        self.player = start_player
        self.save_path = "saves/current_adventure.dat"
        
        # Chat initialization focused on debug_api_key
        api_key = self.options.get("api_key")
        self.chat = Chat(
            system_prompt=scenario.system_prompt,
            initial_message=scenario.initial_message,
            api_key=api_key,
            game=self
        ) if api_key else None

    def get_toolkit(self):
        from src.engine.ai.tools import PlayerToolkit
        return PlayerToolkit(self)

    def load_options(self) -> Dict[str, Any]:
        if os.path.exists("src/options.json"):
            with open("src/options.json", "r") as f: return json.load(f)
        return self._get_default_options()
    def save_options(self):
        with open("src/options.json", "w") as f:
            json.dump(self.options, f, indent=4)

    def _get_default_options(self):
        # Priority given to debug_api_key as repo default
        return {
            "api_key": os.environ.get("debug_api_key", ""),
            "gpt_model": "gemini-1.5-flash"
        }

    def save_session(self):
        """Save the overall state of the adventure"""
        if not os.path.exists("saves"): os.makedirs("saves")
        save_data = {
            "player": self.player,
            "chat_history": self.chat.get_history_data() if self.chat else [],
            "scenario_name": self.scenario.name
        }
        with open(self.save_path, "wb") as f:
            pickle.dump(save_data, f)

    def load_session(self):
        """The adventure continues with the Gemini save and history loaded"""
        if os.path.exists(self.save_path):
            with open(self.save_path, "rb") as f:
                data = pickle.load(f)
                self.player = data["player"]
                if self.chat:
                    self.chat.load_history_data(data["chat_history"])
                
                from src.engine.scene.ChatScene import ChatScene
                self.change_scene(ChatScene(self.screen, self, self.scenario))

    def change_scene(self, new_scene):
        self.scene = new_scene

    def main_menu(self):
        self.scene = MainMenu(None, self.screen, self)

    def back_scene(self):
        actual_scene = self.scene
        self.scene = self.previous_scene
        self.previous_scene = actual_scene

    def start(self):
            self.main_menu()
            
            
            while self.running:
                pygame.event.pump()  # Added for fixing alt + tab crash issue
                
                # 1. RETORNE O SCREEN FILL: Isso limpa os pixels do frame/cena anterior
                self.screen.fill((0, 0, 0)) 
                
                mouse_pos = pygame.mouse.get_pos()
                events = pygame.event.get()

                for event in events:
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        self.running = False

                if self.scene:
                    # 2. REMOVA a chamada self.scene.build_scene(self) daqui!
                    # Delegue a atualização e renderização para a própria classe Scene
                    self.scene.handle_events(events, mouse_pos)
                    self.scene.update()
                    self.scene.render(self.screen)
                
                pygame.display.flip()
                self.clock.tick(60) # Mantenha o controle de framerate
        
            pygame.quit()



