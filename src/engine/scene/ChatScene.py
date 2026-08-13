import queue
import time
import json
import pygame
from typing import List, Callable, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.engine.Game import Game

# Engine & UI Imports
from src.engine.ui.TypewriterManager import TypewriterManager
from src.engine.scene.CombatScene import CombatScene
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.ImageTransformStrategy import ColorInverter
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.StaticImage import StaticImage
from src.engine.ui.TextArea import TextAreaShow
from src.engine.ui.TextInput import TextInput
from src.engine.ui.HorizontalBar import HorizontalBar
from src.model.Item import Usable
from src.model.scenario import Scenario
from src.utils import get_center_x, print_debug, get_default_font, typewriter_sound, log_to_session

class ChatScene(Scene):
    def __init__(self, screen, game: "Game", scenario: Scenario):
        # 1. Initialize attributes before super().__init__ if they are used in build_scene
        self.game = game
        self.scenario = scenario
        self.screen = screen # Ensure screen is accessible for save feedback
        
        self.eminent_combat = None
        self.last_sound_time = 0
        self.sound_cooldown = 0.08
        self.loading = False
        self.active_typewriter = None 

        # 2. Setup UI Elements
        initial_text = ""
        if hasattr(self.game, "chat") and self.game.chat and getattr(self.game.chat, "history", None):
            for i, msg in enumerate(self.game.chat.history):
                role = msg.get("role")
                parts = msg.get("parts", [])
                text_content = "".join(part.get("text", "") for part in parts)
                
                # Força a primeira mensagem a ser do DM caso venha trocada do backend/histórico
                if i == 0 and role == "user":
                    initial_text += f"DM:\n{text_content}\n"
                elif role == "user":
                    initial_text += f"{self.game.player.name}:\n{text_content}\n"
                elif role == "model" or role == "assistant":
                    initial_text += f"DM:\n{text_content}\n"
        else:
            initial_text = f"DM:\n{scenario.initial_message}\n"
        # initial_text = ""
        # if hasattr(self.game, "chat") and self.game.chat and getattr(self.game.chat, "history", None):
        #     for msg in self.game.chat.history:
        #         role = msg.get("role")
        #         parts = msg.get("parts", [])
        #         text_content = "".join(part.get("text", "") for part in parts)
        #         if role == "user":
        #             initial_text += f"Player:\n{text_content}\n"
        #         elif role == "model":
        #             initial_text += f"DM:\n{text_content}\n"
        # else:
        #     initial_text = f"DM:\n{scenario.initial_message}\n"

        self.actual_text = TextAreaShow(
            text=initial_text,
            position=(20, screen.get_height() // 2),
            width=screen.get_width() - 32,
            height=(screen.get_height() // 2) - 75
        )
        
        self.player_input = TextInput(
            position=(24, screen.get_height() - 50),
            width=screen.get_width() - 300,
            on_change=self._on_change,
            on_submit=self._submit
        )

        self.submit_button = Button(
            image=None,
            position=(screen.get_width() - 200, screen.get_height() - 50),
            text=SimpleText("Submit!", 24, (0, 0), (0, 0, 0)),
            background_color=(255, 255, 255),
            hover_transform_strategy=ColorInverter(),
            click_function=lambda: self._submit(self.player_input.text.text)
        )

        self.combat_button = Button(
            image=None,
            position=(get_center_x(screen, get_default_font(24).size("Enter Combat!")[0]), screen.get_height() - 50),
            text=SimpleText("Enter Combat!", 24, (0, 0), (0, 0, 0)),
            background_color=(255, 255, 255),
            hover_transform_strategy=ColorInverter(),
            click_function=self._submit_combat
        )
        self.combat_button.visible = self.combat_button.enabled = False

        # Local variable for buttons as requested
        btn_save = Button(
            image=None,
            text=SimpleText("Save", 18, (0, 0), (255, 255, 255)),
            background_color=(50, 50, 150),
            position=(screen.get_width() - 100, 20),
            click_function=self._save_game
        )

        btn_options = Button(
            image=None,
            text=SimpleText("Options", 18, (0, 0), (255, 255, 255)),
            background_color=(100, 100, 100),
            position=(screen.get_width() - 250, 20),
            click_function=self._open_options
        )

        btn_sheet = Button(
            image=None,
            text=SimpleText("Sheet", 18, (0, 0), (255, 255, 255)),
            background_color=(150, 50, 50),
            position=(screen.get_width() - 400, 20),
            click_function=self._toggle_char_sheet
        )

        # 3. Setup Commands
        self.commands: Dict[str, Callable[[List[str]], None]] = {
            "save": self._manual_save,
            "get_player_status": self._get_player_attribute,
            "player": lambda args: self._put_text(f"\nSystem:\n{self.game.player.to_text(markdown=False)}"),
            "quit": lambda args: self.game.main_menu(),
            "exit": lambda args: self.game.main_menu()
        }

        # Store buttons so build_scene can access it
        self.btn_save = btn_save
        self.btn_options = btn_options
        self.btn_sheet = btn_sheet

        # 4. Finalize Scene Initialization
        super().__init__(None, screen, game)
        self.player_input.focus = True
        pygame.key.start_text_input()

    def build_scene(self, game: "Game") -> List[SceneElement]:
        """Defines what is drawn on the screen."""
        from src.engine.ui.CharacterSheetPanel import CharacterSheetPanel
        self.char_sheet = CharacterSheetPanel(self.game.player, (self.screen.get_width(), 0), self.screen)
        
        return [
            StaticImage(
                relative_path="chat.png",
                size=(400, 400),
                position=(get_center_x(self.screen, 400), 0),
                circle_radius=200
            ),
            self.submit_button,
            self.player_input,
            self.actual_text,
            self.combat_button,
            self.btn_save,
            self.btn_options,
            self.btn_sheet,
            self.char_sheet
        ]

    def _open_options(self):
        from src.engine.scene.Options import Options
        self.game.change_scene(Options(None, self.screen, self.game))

    def _toggle_char_sheet(self):
        if hasattr(self, 'char_sheet'):
            self.char_sheet.toggle()

    def _save_game(self):
        """Prompt user for filename before saving"""
        self._put_text("\n[System: Type a filename for your save and press Enter]\n")
        self.saving_mode = True
        self.player_input.focus = True
        pygame.key.start_text_input()

    def _manual_save(self, args: List[str]):
        """Logic for the /save command"""
        self.game.save_session()
        self._put_text("\n[Sistema: Jogo salvo com sucesso!]\n")

    def _on_change(self, text):
        self.player_input.text.text = text

    def _submit(self, text):
        text = text.strip()
        if not text:
            return
        
        if getattr(self, 'saving_mode', False):
            if self.game.save_session(text):
                self._put_text(f"\n[System: Game saved as '{text}']\n")
            else:
                self._put_text(f"\n[System: Failed to save game!]\n")
            self.saving_mode = False
            self.player_input.text_str = ""
            return

        # Check for commands
        if text.startswith("/"):
            parts = text[1:].split()
            cmd = parts[0]
            args = parts[1:]
            if cmd in self.commands:
                self.commands[cmd](args)
                self.player_input.text.change_text("")
                return

        self.player_input.text.change_text("")
        user_msg = f"\n{self.game.player.name}:\n{text}\nDM:\n"
        self._put_text(user_msg)
        log_to_session(f"PLAYER ({self.game.player.name}): {text}")
        self._hide_input()
        
        self.active_typewriter = TypewriterManager("Mestre está pensando...", speed_ms=50)
        
        try:
            self.game.chat.send_message(text, callback=self._on_chat_response)
        except Exception as e:
            self._on_chat_response(f"[Erro na API: {str(e)}]")

    def _on_chat_response(self, response_text):
        if response_text is None:
            response_text = "[Erro: Resposta vazia da API]"

        # Extract JSON state updates
        import re
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            try:
                json_data = json.loads(match.group(1))
                self._update_player_state(json_data)
                # Remove the JSON block from the text shown to the user
                response_text = re.sub(json_pattern, '', response_text, flags=re.DOTALL).strip()
            except Exception as e:
                print(f"Error processing AI JSON: {e}")

        log_to_session(f"DM: {response_text}")
        self.active_typewriter = TypewriterManager(response_text, speed_ms=25)

    def _update_player_state(self, data: dict):
        """Processes JSON blocks from the AI to update character state."""
        player = self.game.player
        if not player: return

        # Stats updates
        if "stats" in data:
            s = data["stats"]
            if "hp" in s: player.heal(s["hp"])
            if "gold" in s: player.gold = max(0, player.gold + s["gold"])
            if "xp" in s: player.give_xp(s["xp"])
            if "mana" in s: player.mana = max(0, min(player.max_mana, player.mana + s["mana"]))

        # Inventory updates
        if "inventory" in data:
            for item_id, qty in data["inventory"].items():
                try:
                    player.give_item(int(item_id), qty)
                except: pass

        # XP / Level Up notification (Simplified for now)
        if "xp" in data.get("stats", {}):
            from src.engine.ui.HorizontalBar import HorizontalBar
            self.elements.append(HorizontalBar(self.screen.get_width(), self.screen.get_height(), f"+{data['stats']['xp']} XP GAINED!"))

    def handle_events(self, events: List[pygame.event.Event], mouse_pos: tuple):
        # 1. Always trigger parent event router so UI Elements remain interactive
        super().handle_events(events, mouse_pos)
        
        # 2. Intercept instant-reveal text shortcuts while typing is active
        if self.active_typewriter and not self.active_typewriter.is_complete:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        new_text = self.active_typewriter.reveal_all()
                        if new_text:
                            self.actual_text.text += new_text
                            typewriter_sound()

    def update(self):
        super().update()
        if self.active_typewriter and not self.active_typewriter.is_complete:
            # Read continuous state of the keyboard for smooth fast-forwarding
            keys = pygame.key.get_pressed()
            fast_forward_active = keys[pygame.K_SPACE]
            
            new_text = self.active_typewriter.update(fast_forward=fast_forward_active)
            if new_text:
                self.actual_text.text += new_text
                typewriter_sound()
        elif self.active_typewriter and self.active_typewriter.is_complete:
            self.active_typewriter = None
            self._show_input()

    def _put_text(self, new_text):
        self.actual_text.text += new_text
        typewriter_sound()

    def _get_player_attribute(self, args: List[str]):
        if not args:
            self._put_text("\nSystem:\nArgumentos inválidos!\n")
            return
        attr = args[0].lower()
        if not hasattr(self.game.player, attr):
            self._put_text(f"\nSystem:\nAtributo {attr} não encontrado!\n")
            return
        self._put_text(f"\nSystem:\n{attr}={str(getattr(self.game.player, attr))}\n")

    def _submit_combat(self):
        if self.eminent_combat:
            self.game.change_scene(CombatScene(
                game=self.game,
                screen=self.screen,
                combat=self.eminent_combat
            ))

    def _hide_input(self):
        self.submit_button.visible = self.submit_button.enabled = False
        self.player_input.visible = self.player_input.enabled = False

    def _show_input(self):
        if self.eminent_combat is None:
            self.submit_button.visible = self.submit_button.enabled = True
            self.player_input.visible = self.player_input.enabled = True

    def wait_combat_confirm(self, combat):
        self._hide_input()
        self.combat_button.visible = self.combat_button.enabled = True
        self.eminent_combat = combat

    def end_combat(self):
        self.combat_button.visible = self.combat_button.enabled = False
        if self.eminent_combat:
            self.game.chat.submit(f"event:combat_ended\n"
                                f"Victory:{str(self.eminent_combat.result.victory)}\n"
                                f"Player Fled:{str(self.eminent_combat.result.player_flee)}\n"
                                f"Enemies Flee: {len(self.eminent_combat.result.enemies_flee)}\n"
                                f"Player Kills: {self.eminent_combat.result.kills}\n"
                                f"Total Enemies: {len(self.eminent_combat.result.enemies)}")
            self.eminent_combat = None
        self._show_input()