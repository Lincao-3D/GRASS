import json
import os
import pickle
import pygame
from typing import Optional, Dict, Any
from src.engine.ai.chat import Chat
from src.engine.scene.MainMenu import MainMenu

# Import the corrected functions
from src.utils import apply_global_volume, load_sfx

class Game:
    def __init__(self, scenario, start_player=None):
        # 1. Core Pygame Setup
        self.screen = pygame.display.set_mode((800, 600), pygame.FULLSCREEN)
        pygame.display.set_caption("GRASS RPG")
        
        # Initialize mixer before loading sounds
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # 2. State & Options Initialization
        self.scene = None
        self.scenario = scenario
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.player = start_player
        self.save_path = "saves/current_adventure.dat"
        
        # Initialize options with hard defaults
        self.options = {
            "master_volume": 0.5, 
            "is_muted": False,
            "api_key": os.environ.get("debug_api_key", ""),
            "gpt_model": "gemini-1.5-flash"
        }
        
        # Load options from disk (overwrites defaults)
        self.load_options() 

        # 🔥 Load SFX first so they exist when volume is applied
        load_sfx()
        
        # Apply the loaded volume settings immediately
        self.apply_volume()

        # 3. Chat System Initialization
        api_key = self.options.get("api_key")
        self.chat = Chat(
            system_prompt=scenario.system_prompt,
            initial_message=scenario.initial_message,
            api_key=api_key,
            game=self
        ) if api_key else None

    def get_options_path(self):
        """Helper to guarantee we always hit src/options.json relative to this file."""
        # This goes up two levels from Game.py (scene/engine) to reach src/
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src", "options.json")

    def load_options(self):
        """Loads options from src/options.json and applies audio settings."""
        path = self.get_options_path()
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    file_data = json.load(f)
                    self.options.update(file_data) # Merge file data into defaults
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Config] Error loading {path}: {e}. Using internal defaults.")
            
        self.apply_volume()

    def save_options(self):
        """Saves current options dict to src/options.json."""
        path = self.get_options_path()
        try:
            # Ensure the directory exists just in case
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(self.options, f, indent=4)
        except IOError as e:
            print(f"[Config] Failed to save options: {e}")
            
        self.apply_volume()

    def apply_volume(self):
        """Dispatches the volume update command to utils without arguments."""
        # It relies entirely on the JSON file logic we just wrote
        from src.utils import apply_global_volume
        apply_global_volume()

    def _get_default_options(self):
        # Priority given to debug_api_key as repo default
        return {
            "api_key": os.environ.get("debug_api_key", ""),
            "gpt_model": "gemini-1.5-flash"
        }

    def save_session(self, filename: str = "save_game.json"):
        """Saves the overall state of the adventure to a JSON file."""
        if not os.path.exists("saves"): 
            os.makedirs("saves")
        
        # Clean filename: strip spaces, lower case, ensure .json
        clean_name = filename.strip().replace(" ", "_").lower()
        if not clean_name.endswith(".json"):
            clean_name += ".json"
            
        path = os.path.join("saves", clean_name)
        
        save_data = {
            "player": self.player.to_dict() if self.player else None,
            "chat_history": self.chat.history if self.chat else [],
            "scenario": self.scenario.dict() if hasattr(self.scenario, 'dict') else self.scenario # Pydantic
        }
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Failed to save session to {path}: {e}")
            return False

    def load_session(self, filename: str):
        """Loads the adventure state from a JSON file."""
        path = os.path.join("saves", filename) if not os.path.isabs(filename) else filename
        if not os.path.exists(path) and not os.path.isabs(filename):
            path = filename # Fallback to literal if saves/ doesn't exist
            
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Reconstruct player via Player.from_dict
                from src.model.player import Player
                
                pd = data.get("player")
                if pd:
                    self.player = Player.from_dict(pd)

                if self.chat and "chat_history" in data:
                    self.chat.history = data["chat_history"]
                
                from src.engine.scene.ChatScene import ChatScene
                self.change_scene(ChatScene(self.screen, self, self.scenario))
                return True
            except Exception as e:
                print(f"Error loading {path}: {e}")
        return False

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



