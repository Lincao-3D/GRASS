from typing import List, Optional, TYPE_CHECKING

import pygame

# Dice animation import
from src.engine.ui.DiceRollAnimation import DiceRollAnimation

from src.constants import IMAGE_SIZE
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Bar import Bar
from src.engine.ui.Button import Button
from src.engine.ui.EntityImg import EntityImg
from src.engine.ui.ImageTransformStrategy import ColorInverter
from src.engine.ui.RadioButton import RadioButtonGroup
from src.engine.ui.SimpleText import SimpleText
from src.model.Item import Usable
from src.model.combat import Combat
from src.model.entity import Entity
from src.model.skills import Skill
from src.utils import get_center_x, get_default_font, grid_position, print_debug

if TYPE_CHECKING:
    from src.engine.Game import Game

class CombatScene(Scene):
    def __init__(self, screen,game,combat: Combat):
        self.game = game
        self.combat = combat
        self.use_skill: bool = False
        self.use_item = False
        self.selected_skill: Optional[Skill] = None
        self.selected_item: Optional[Usable] = None
        self.target:Entity = combat.enemies[0]

        # Dice animation state variables
        self.dice_animation = None
        self.roll_animation_active = False

        self.rg_skill_select = RadioButtonGroup(
            position=(50, screen.get_height()  - screen.get_height() // 4),
            label_str="Skills",
            options=[(skill.name, skill) for skill in self.game.player.skills],
            on_change=self._set_selected_skill
        )
        self.rg_item_select = RadioButtonGroup(
            position=(50, screen.get_height()  - screen.get_height() // 4),
            label_str="Usable Items",
            options=[(item.name, item) for item in self.game.player.inventory if isinstance(item,Usable)],
            on_change=self._set_selected_item
        )
        self.life_bar = Bar(
            position=(get_center_x(screen,100), 100),
            width=100,
            max_progress=self.game.player.max_health,
            initial_progress=self.game.player.health
        )
        self.log_text = SimpleText(
            "",
            24,
            position=(0,0)
        )
        self.flee_button = Button(
                image=None,
                position=self._button_grid_position(3,screen),
                background_color=(255, 255, 255),
                text=SimpleText("Flee!", 24, position=(0, 0), text_color=(0, 0, 0)),
                hover_transform_strategy=ColorInverter(),
                click_function=lambda: self.combat.flee_player()
        )
        self.flee_button.visible = combat.fleeable
        self.flee_button.enabled = combat.fleeable
        self.action_buttons = [
            Button(
                image=None,
                position=self._button_grid_position(0,screen),
                background_color=(255, 255, 255),
                text=SimpleText("Attack", 24, position=(0, 0), text_color=(0, 0, 0)),
                hover_transform_strategy=ColorInverter(),
                click_function=self._player_attack
            ),
            Button(
                image=None,
                position=self._button_grid_position(1,screen),
                background_color=(255, 255, 255),
                text=SimpleText("Use Skill", 24, position=(0, 0), text_color=(0, 0, 0)),
                hover_transform_strategy=ColorInverter(),
                click_function=self._use_skill_button
            ),
            Button(
                image=None,
                position=self._button_grid_position(2,screen),
                background_color=(255, 255, 255),
                text=SimpleText("Use Item", 24, position=(0, 0), text_color=(0, 0, 0)),
                hover_transform_strategy=ColorInverter(),
                click_function=self._use_item_button
            ),
            self.flee_button
        ]

        self.rg_skill_select.visible = False
        self.rg_skill_select.enabled = False
        self.rg_item_select.visible = False
        self.rg_item_select.enabled  =False


        self.enemies_imgs = [EntityImg(
            entity=entity,
            position=grid_position(i, 50, 200, IMAGE_SIZE[0], IMAGE_SIZE[1], 5),
            on_click=self._set_target
        ) for i, entity in enumerate(combat.enemies)]


        super().__init__(None, screen, game)



    def update(self):
        # Handle dice animation completion
        if self.roll_animation_active and self.dice_animation:
            self.dice_animation.update(None, None)
            # Auto-remove after animation (keeps screen clean)
            if not self.dice_animation.is_rolling:
                self._end_dice_animation()


        super().update()
        self.combat.update()
        self._update_action_buttons()
        self._update_log_text()
        self._update_life_bar()
        self._update_target()
        self.typewriter.update()

    def draw(self, screen):
        # 1. Draw the base scene (background, buttons, etc.)
        super().draw(screen)
        
        # 2. Draw the typewriter log (usually at the bottom)
        # Position (50, 480) is a safe bet for a 800x600 screen
        self.typewriter.draw(screen, (50, 480))
        
        # 3. Draw the dice animation if active
        if self.roll_animation_active and self.dice_animation:
            self.dice_animation.draw(screen)
            
    def handle_events(self, events):
        # 1. Define mouse_pos by grabbing it from pygame
        mouse_pos = pygame.mouse.get_pos()
        
        super().handle_events(events, mouse_pos)
        
        # 2. Iterate through the events list to define 'event'
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_END:
                for enemy in self.combat.enemies:
                    enemy.apply_damage(None, 9999)

    def build_scene(self, game: "Game") -> List[SceneElement]:
        return [
            SimpleText("Combat!", 48,
                       (get_center_x(self.screen, get_default_font(48).size("Combat!")[0]), 0)),
            self.life_bar,
            self.rg_skill_select,
            self.rg_item_select,
            self.log_text,
        ] + self.action_buttons + self.enemies_imgs

    def _update_life_bar(self):
        self.life_bar.change_label(f"Life: {str(self.game.player.health)}/{str(self.game.player.max_health)}",True)
        self.life_bar.progress = self.game.player.health

    def _set_target(self,target):
        self.target = target
    def _update_log_text(self):
        if len(self.combat.log) == 0:
            return

        previous_log = self.log_text.text
        log = self.combat.log[-1]

        if log != previous_log:
            self._change_log_text(log)

    def _change_log_text(self,log):
        self.log_text.position = (get_center_x(self.screen, get_default_font(24).size(log)[0]), self.screen.get_height() - 100)
        self.log_text.change_text(log)

    """ Dice logic """
    def _start_dice_animation(self):
        # Clear existing dice
        if self.dice_animation and self.dice_animation in self.elements:
            self.elements.remove(self.dice_animation)
        
        # New dice at top-left origin (10, 10) - NO result text overlay
        self.dice_animation = DiceRollAnimation(position=(10, 10), duration_ms=800)  # Shorter for combat
        self.elements.append(self.dice_animation)
        self.roll_animation_active = True

    def _end_dice_animation(self):
        if self.dice_animation and self.dice_animation in self.elements:
            self.elements.remove(self.dice_animation)
            self.dice_animation = None
        self.roll_animation_active = False
    """ End of dice logic """

    def _update_action_buttons(self):
        for button in self.action_buttons:
            button.visible = self.combat.is_player_turn
            button.enabled = self.combat.is_player_turn

    def _button_grid_position(self,index,screen):
        return grid_position(index,24,screen.get_height() - 50,300,50,4,20,8)

    def _set_selected_skill(self,_,skill: Skill):
        self.selected_skill = skill

    def _set_selected_item(self,_,item:Usable):
        self.selected_item = item

    def _player_attack(self):
        # Start dice animation FIRST (pure atmosphere, no text overlay)
        self._start_dice_animation()
        
        # Roll happens immediately (hidden), animation provides visual feedback
        passed, result, damage = self.game.player.attack(self.target)
        
        # Schedule log text AFTER animation (handled by update timing)
        self.combat.print_text(f"You rolled {result} {'(success!)' if passed else '(miss!)'}")
        if passed and damage > 0:
            self.combat.delayed_action(
                text=f"You deal {damage} damage to {self.target.name}",
                action=lambda: self.target.apply_damage(self.target, damage, self.game.player.get_damage_type(), self.combat),
            )
        self.combat.end_player_turn()


    def _use_skill_button(self):
        if self.use_item:
            self.use_item = False
            self.selected_item = None
            self.rg_item_select.visible = False
            self.rg_item_select.enabled = False

        self.use_skill = not self.use_skill


        if self.selected_skill is not None:
            if not self.combat.game.player.mana >= self.selected_skill.cost:
                self._change_log_text("Not enough mana")
                return
            self.selected_skill.execute(self.combat.game.player,self.target,self.combat)
            self.combat.game.player.mana -= self.selected_skill.cost
            if self.selected_skill.skip_turn:
                self.combat.end_player_turn()

        self.rg_skill_select.visible = self.use_skill
        self.rg_skill_select.enabled = self.use_skill

        self.selected_skill = None


    def _use_item_button(self):
        if self.use_skill:
            self.use_skill = False
            self.selected_skill = None
            self.rg_skill_select.visible = False
            self.rg_skill_select.enabled = False


        self.use_item = not self.use_item

        if self.selected_item is not None:
            self.selected_item.on_use(self.combat.game.player,self.selected_item.get_targets(self.combat.game.player,self.target,self.combat.enemies))
            if self.selected_item.skip_turn:
                self.combat.end_player_turn()

        self.rg_item_select.visible = self.use_item
        self.rg_item_select.enabled = self.use_item

        self.selected_item = None


    def _update_target(self):
        if self.target is not None and self.target.dead and len(self.combat.get_alives_enemies()) > 0:
            self.target = self.combat.get_alives_enemies()[0]
        for eimg in self.enemies_imgs:
            eimg.targeted = self.target == eimg.entity
            eimg.enabled = not eimg.entity.dead
