# src/engine/scene/CharacterCreator.py
import random
import pygame

from typing import List, TYPE_CHECKING, Optional
# Dice roll import
from src.engine.ui.DiceRollAnimation import DiceRollAnimation

from src.constants import START_SKILLS
from src.engine.scene.ChatScene import ChatScene
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.ImageTransformStrategy import ColorInverter
from src.engine.ui.RadioButton import RadioButtonGroup
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.TextInput import TextInput
from src.model.attribs import CharacterAttrib, CharacterExpertise, roll_attribs, random_attribs
from src.model.classes import CharacterClass, CharacterClassEnum, CLASS_FACTORY
from src.model.player import Player
from src.model.race import CharacterRace
from src.model.skills import SkillEnum, SKILL_FACTORY
from src.utils import get_center_x, get_default_font, grid_position

if TYPE_CHECKING:
    from src.engine.Game import Game

class CharacterCreator(Scene):
    def __init__(self, background, screen, game: "Game"):
        # Basic state FIRST
        self.selected_race = None
        self.selected_class = None
        self.rolled_atribs = roll_attribs()
        while len(set(self.rolled_atribs)) != len(self.rolled_atribs):
            self.rolled_atribs = roll_attribs()
        self.avaliable_skills: List[SkillEnum] = []
        self.skill_len = 0  # Will be set after class selection
        self.selected_skills = []
        self.selected_expertises = []
        self.error: Optional[SimpleText] = None
        self.selected_name = self._gerar_nome(random.randint(6, 8), bool(random.randint(0, 1)))
        self.re_rolls = 3
        
        # Dice animation state
        self.dice_animation = None
        self.roll_animation_active = False
        self.roll_start_time = 0
        self.dice_assignments = {} # {column_index: (Attribute, Value)}
        self.selected_attribs = {} # Final valid mapping
        # CREATE ALL UI ELEMENTS BEFORE super()
        self.skills_radio_button = RadioButtonGroup(
            label_str="Select skills after class",
            multiselect=0,
            position=(20, 90),
            options=[],
            on_change=self._set_selected_skills
        )
        
        self.attrib_radio_button = self._build_scene_attribs(screen)
            # FIXED: Proper closure capture with default args
        for i, radio_group in enumerate(self.attrib_radio_button):
            radio_group.on_change = lambda p, x, idx=i: self._attrib_changed(idx, self.rolled_atribs[i], p, x)


        self.reroll_button = Button(
            image=None,
            position=(24, 24),
            background_color=(255, 255, 255),
            text=SimpleText(text="Reroll (3)", text_color=(0, 0, 0), position=(0, 0), size=24),
            hover_transform_strategy=ColorInverter(),
            click_function=self._reroll
        )
        

        self._update_attrib_checklist()

        # NOW super() calls build_scene() - all elements exist
        super().__init__(background, screen, game)
        self.selected_attribs = {}
        
        # REPLACE checklist with correct position
        self.attrib_checklist = SimpleText(
            text="Attributes: Select to check", 
            position=(self.screen.get_width() - 500, 580),
            size=13,
            text_color=(200, 200, 200),
        )
        self.elements.append(self.attrib_checklist) 
        self._update_attrib_checklist()
        # Initialize visuals
        self._update_attrib_checklist()
        self._start_dice_animation()


    def _start_dice_animation(self):
        # Clear any existing dice animation
        if hasattr(self, 'dice_animation') and self.dice_animation:
            if self.dice_animation in self.elements:
                self.elements.remove(self.dice_animation)
        
        # Create new DiceRollAnimation at top-left origin (10, 10)
        self.dice_animation = DiceRollAnimation(
            position=(10, 10),  # Top-left aligned as requested
            duration_ms=1500
        )

        # HOOK: Mark spawn time for 3‑second autodisappear
        self.dice_animation.hide_after_3_seconds()

        self.elements.append(self.dice_animation)
        self.roll_animation_active = True
        self.roll_start_time = pygame.time.get_ticks()


    def update(self):
        # Dice animation logic FIRST
        if self.roll_animation_active and hasattr(self, 'dice_animation'):
            self.dice_animation.update(None, None)  # No event/mouse needed for dice
            
            if pygame.time.get_ticks() - self.roll_start_time > 1500:
                self.roll_animation_active = False
                # DiceRollAnimation handles its own stopping - no need to remove here
        # Call parent update
        super().update()

    def _reroll(self):
        if self.re_rolls <= 0:
            return
        self.re_rolls -= 1

        # calling of dice GIF animation
        self._start_dice_animation() 
        self.dice_animation.temp_result_str = f"Rolled: {self.rolled_atribs}"
        # ↑ Store result string for later

        self.rolled_atribs = roll_attribs()
        while len(set(self.rolled_atribs)) != len(self.rolled_atribs):
            self.rolled_atribs = roll_attribs()
        
        self.reroll_button.text.change_text(f"Reroll ({self.re_rolls})")
        self.reroll_button.update_image()

        # FIXED: Update radio buttons with proper lambda (dice_idx = i, current_attr = x, roll_value = rolled_atribs[i])
        for i, radio_button_group in enumerate(self.attrib_radio_button):
            value = self.rolled_atribs[i]
            radio_button_group.set_text(str(value))
            # FIXED: Proper closure with default args
            radio_button_group.on_change = lambda p, x, idx=i, val=value: self._attrib_changed(idx, val, p, x)



        """ def _update_attrib_checklist(self):
                # 1. Clean up old checklist items dynamically
                self.elements = [e for e in self.elements if not getattr(e, "is_attrib_checklist_item", False)]

                # 2. Recalculate COL_4 using the same logic as build_scene
                screen_w = self.screen.get_width()
                MARGIN = 40
                USABLE_WIDTH = screen_w - (MARGIN * 2)
                COL_4 = MARGIN + ((USABLE_WIDTH / 4) * 3)
                
                y_offset = 630
                line_height = 24 # Spacing between attributes

                header = SimpleText(
                    text="Attributes:",
                    size=20, # Slightly smaller header
                    position=(COL_4, y_offset - 30),
                    text_color=(255, 215, 0)
                )
                header.is_attrib_checklist_item = True
                self.elements.append(header) """
    
    def _attrib_changed(self, dice_idx, roll_value, previous, current):
        """Wrapper - now receives correct dice_idx"""
        print(f"DEBUG: Changed dice {dice_idx} (value {roll_value}): {previous} → {current}")
        self._set_selected_attribs(dice_idx, current, roll_value)


    def _update_attrib_checklist(self):
        """
        Atualiza a lista visual de atributos no lado direita da tela.
        Remove os itens antigos e cria novos baseados no estado atual de self.selected_attribs.
        """
        # 1. Limpa os elementos antigos da checklist (sem sobrepor)
        # self.elements = [e for e in self.elements if not getattr(e, 'is_checklist', False)]
        
        # THE FIX: Use slice assignment [:] to update the original list reference 
        # so the Game loop sees the changes immediately.
        if not hasattr(self, 'elements'): 
            return
        
        # Keep your exact positioning logic
        new_elements = [e for e in self.elements if not getattr(e, 'is_checklist', False)]
        
        screen_w = self.screen.get_width()
        MARGIN = 40
        USABLE_WIDTH = screen_w - (MARGIN * 2)
        COL_4_X = MARGIN + (USABLE_WIDTH / 4 * 3)  # Your exact column
        y_offset = 641  # Your exact Y start
        line_height = 28  # Your exact spacing

        # → Your header (unchanged)
        header = SimpleText(
            text="Attributes Checklist:",
            size=20,
            position=(COL_4_X, y_offset - 40),
            text_color=(255, 215, 0)
        )
        header.is_checklist = True
        new_elements.append(header)

        # NEW: Calculate attribute usage counts first
        attr_counts = {}
        for idx, (attr, val) in self.dice_assignments.items():
            attr_counts[attr] = attr_counts.get(attr, 0) + 1
        
        # Valid only if used exactly once
        self.selected_attribs = {a: v for idx, (a, v) in self.dice_assignments.items() if attr_counts[a] == 1}

        # → Your items loop (enhanced with conflict detection)
        # Inside _update_attrib_checklist(), replace the items loop:
        for attr in CharacterAttrib:
            count = attr_counts.get(attr, 0)
            valor = self.selected_attribs.get(attr)
            
            if count == 1:
                status, color = f"[X] {valor}", (100, 255, 100)      # ✅ Valid (exactly 1)
            elif count > 1:
                status, color = f"[!] x{count}", (255, 50, 50)       # 🚨 Conflict (2+ assignments)
            else:
                status, color = "[ ] --", (200, 200, 200)             # ⭕ Empty
            
            txt = SimpleText(
                text=f"{attr.value.capitalize():<10} {status}",
                size=18,
                position=(COL_4_X, y_offset),
                text_color=color
            )
            txt.is_checklist = True
            new_elements.append(txt)
            y_offset += line_height
        
        # Apply the new list
        self.elements[:] = new_elements


    """ # 3. Build the live list
    for attr in CharacterAttrib:
        line_height = 24 # Spacing between attributes
        screen_w = self.screen.get_width()
        MARGIN = 40
        USABLE_WIDTH = screen_w - (MARGIN * 2)
        COL_4 = MARGIN + ((USABLE_WIDTH / 4) * 3)
        
        # Using brackets creates a nice uniform block for the eye
        status = "[ X ]" if attr in self.selected_attribs else "[   ]"
        line_text = f"{status} {attr.value.capitalize()}"
        
        text_el = SimpleText(
            text=line_text,
            size=18, # Font size 18 prevents right-side clipping
            position=(COL_4, y_offset),
            text_color=(200, 200, 200)
        )
        text_el.is_attrib_checklist_item = True
        self.elements.append(text_el)
        
        y_offset += line_height """

    def _play(self):
        if not self._validate():
            return
        player = Player(
            self.selected_name,
            CLASS_FACTORY[self.selected_class],
            self.selected_race,
            self.selected_attribs,
            self.selected_skills,
            self.selected_expertises
        )
        # FIXED: Extract SkillEnum from Skill objects
        # [skill for skill in self.selected_skills],
        self.game.player = player
        self.game.change_scene(ChatScene(self.screen, self.game, self.game.scenario))


    def _validate(self) -> bool:
        if not self.selected_race:
            self._update_error("Select a race")
            return False
        if not self.selected_class:
            self._update_error("Select a class")
            return False
        if not self.selected_skills:
            self._update_error(f"You must select at least {self.skill_len} skill(s)")
            return False
        if len(self.selected_skills) < self.skill_len:
            self._update_error(f"You must select at least {self.skill_len} skill(s)")
            return False
        
        # === DEBUG BLOCK ===
            print(f"DEBUG: len(self.selected_attribs) = {len(self.selected_attribs)}")
            print(f"DEBUG: len(CharacterAttrib) = {len(CharacterAttrib)}")
            print(f"DEBUG: self.selected_attribs keys: {[k.value for k in self.selected_attribs.keys()]}")
            print(f"DEBUG: self.selected_attribs values: {list(self.selected_attribs.values())}")
            print(f"DEBUG: rolled_atribs: {self.rolled_atribs}")
        
        # Filter out any None keys just in case, though the fix above prevents them
        valid_selections = {k: v for k, v in self.selected_attribs.items() if k is not None}
        
        if len(valid_selections) < 6:
            print(f"Select all 6 attributes! (Current: {len(valid_selections)})")
            return False
        # FIXED: Clearer error + count debugging
        # if len(self.selected_attribs) != len(CharacterAttrib):
        #     self._update_error(f"You must assign all {len(CharacterAttrib)} attribute values (selected: {len(self.selected_attribs)})")
        #     return False
        
        # FIXED: Proper missing detection (identity-safe)
        assigned_attrs = list(self.selected_attribs.keys())
        missing = [attr.value for attr in CharacterAttrib if attr not in assigned_attrs]
        if missing:
            self._update_error(f"Missing attributes: {', '.join(missing)} (selected {len(assigned_attrs)}/{len(CharacterAttrib)})")
            return False
        
        if not self.selected_name or self.selected_name.replace(" ", "") == "":
            self._update_error("You must select a name")
            return False
        if len(self.selected_expertises) != 4:
            self._update_error("You must select exactly 4 expertises")
            return False
        
        return True


    def _update_error(self, error_txt: str):
        if self.error is None:
            SIZE = 24
            # CORREÇÃO APLICADA AQUI: removido aspas da variável error_txt
            fw, fh = get_default_font(SIZE).size(error_txt)
            self.error = SimpleText(
                text=error_txt,
                position=(get_center_x(self.screen, fw), self.screen.get_height() - fh - 90),
                size=SIZE,
                text_color=(255, 0, 0)
            )
            self.elements.append(self.error)
        else:
            self.error.change_text(error_txt)

    def _set_selected_skills(self, previous, skills: List[SkillEnum]) -> None:
        self.selected_skills = skills

    def _set_selected_race(self, previous, race: CharacterRace):
        self.selected_race = race

    def _set_selected_class(self, previous, clazz: CharacterClass):
        self.selected_class = clazz
        self.avaliable_skills = [
            skill for skill in SkillEnum 
            if self.selected_class in SKILL_FACTORY[skill].classes and SKILL_FACTORY[skill].min_level == 1
        ]
        self.skill_len = START_SKILLS if len(self.avaliable_skills) >= START_SKILLS else len(self.avaliable_skills)
        self.skills_radio_button.set_options([(skill.name, skill) for skill in [SKILL_FACTORY[se] for se in self.avaliable_skills]])
        self.skills_radio_button.multiselect = self.skill_len
        self.skills_radio_button.set_text(f"Select {str(self.skill_len)} skill(s)")

    def _set_selected_name(self, name):
        self.selected_name = name

    def _set_selected_attribs(self, dice_idx, current_attr, roll_value):
        print(f"DEBUG: Assigned dice {dice_idx} -> {current_attr.value if current_attr else None}: {roll_value}")
        """
        Handles the logic of assigning a dice roll to an attribute.
        """
        # 1. Clean up: If we are switching away from an attribute, remove it
        # if previous_attr in self.selected_attribs:
        #     del self.selected_attribs[previous_attr]

        if current_attr is not None:
            self.dice_assignments[dice_idx] = (current_attr, roll_value)
            radio_group = self.attrib_radio_button[dice_idx]
            radio_group.set_selected(current_attr)
        else:
            self.dice_assignments.pop(dice_idx, None)  # Clean deselection
        
        self._update_attrib_checklist()  # 🔥 ADD THIS - was missing!

        # 2. THE FIX: Only add to dictionary if current_attr is NOT None
        # This prevents the '7 attributes' bug (where None was being counted as a key)
        """ if current_attr is not None:
            # Check if another dice already claimed this attribute (Optional Conflict Handling)
            # For now, we simply overwrite the assignment
            self.selected_attribs[current_attr] = roll_value

        # 3. Refresh the UI
        self._update_attrib_checklist() """

    def build_scene(self, game: "Game") -> List[SceneElement]:
        """Grid-based layout: 4 columns, auto-flow"""
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        # Percentage-based Columns to avoid absolute pixel overlaps
        COL_1 = screen_h * 0.15      # Race, Name
        COL_2 = screen_h * 0.60      # Class, Skills
        COL_3 = screen_w * 0.45      # Expertises
        # COL_4 (Checklist/Dice) is handled dynamically in _update_attrib_checklist
        
        return [
            # --- Header ---
            SimpleText("Character Creator", 48, (get_center_x(self.screen, 789), 10)),
            
            # --- Column 1: Race & Name ---
            RadioButtonGroup(
                label_str="Select Race", 
                position=(COL_1 + 235, 92), 
                on_change=self._set_selected_race, 
                options=[(race.value, race) for race in CharacterRace]
            ),
            TextInput(
                initial_text=self.selected_name,
                label_str="Name:", 
                position=(COL_1, 350),
                width=200, 
                on_change=self._set_selected_name, 
                label_top=False
            ),
            
            # --- Column 2: Class & Skills ---
            RadioButtonGroup(
                label_str="Select Class", 
                position=(COL_1, 480), 
                on_change=self._set_selected_class, 
                options=[(clazz.value, clazz) for clazz in CharacterClassEnum]
            ),
            self.skills_radio_button,  # Positioned at initialization, updated dynamically
            
            # --- Column 3: Expertises ---
            RadioButtonGroup(
                label_str="Select 4 Expertises",
                position=(COL_2, 480),
                options=[(expertise.value, expertise) for expertise in CharacterExpertise],
                multiselect=4, 
                on_change=self._change_expertise
            ),
            
            # --- Bottom Row: Action Buttons ---
            Button(
                image=None,
                text=SimpleText(text="Create!", size=24, position=(0, 0), text_color=(0, 0, 0)),
                hover_transform_strategy=ColorInverter(),
                background_color=(100, 255, 100),
                click_function=self._play,
                position=(get_center_x(self.screen, 120) - 60, self.screen.get_height() - 60)
            ),
            
            Button(
                image=None,
                text=SimpleText(text="Random!", size=24, position=(-50, 0), text_color=(0, 0, 0)),
                hover_transform_strategy=ColorInverter(),
                background_color=(200, 200, 200),
                click_function=self._play_with_random,  # Now a real method
                position=(self.screen.get_width() - 180, self.screen.get_height() - 60)
            ),

            self.reroll_button
        ] + self.attrib_radio_button

    # def _play_with_random(self):
    #     self._set_selected_race(None, random.choice(list(CharacterRace)))
    #     self._set_selected_class(None, random.choice(list(CharacterClassEnum)))
    #     self.selected_attribs = random_attribs()
    #     self.selected_skills = random.choices(population=self.avaliable_skills, k=self.skill_len)
    #     self.selected_expertises = random.choices(population=list(CharacterExpertise), k=4)
    #     self._play()

    def _play_with_random(self):
        print("🎲 Generating random character...")
        
        # 1-3. Race, Class, Name (unchanged)
        self.selected_race = random.choice(list(CharacterRace))
        self._set_selected_race(None, self.selected_race)
        
        self.selected_class = random.choice(list(CharacterClassEnum))
        self._set_selected_class(None, self.selected_class)
        
        self.selected_name = self._gerar_nome(random.randint(6, 10), bool(random.randint(0, 1)))
        self._set_selected_name(self.selected_name)
        
        # 4. 🔥 FIX: REROLL + REBUILD radio groups
        self.rolled_atribs = roll_attribs()
        while len(set(self.rolled_atribs)) != len(self.rolled_atribs):
            self.rolled_atribs = roll_attribs()
        
        # CRITICAL: Rebuild radio buttons with NEW rolls
        self.attrib_radio_button = self._build_scene_attribs(self.screen)
        
        # Reassign on_change handlers with new rolls
        for i, radio_group in enumerate(self.attrib_radio_button):
            radio_group.on_change = lambda p, x, idx=i: self._attrib_changed(idx, self.rolled_atribs[i], p, x)
        
        # 5. Assign random unique attributes
        available_attrs = list(CharacterAttrib)
        random.shuffle(available_attrs)
        
        self.dice_assignments.clear()
        for i in range(len(self.rolled_atribs)):
            attr = available_attrs[i]
            self.dice_assignments[i] = (attr, self.rolled_atribs[i])
            
            # 🔥 VISUAL: Update radio button display text AND selection
            self.attrib_radio_button[i].set_text(f"Dado: {self.rolled_atribs[i]}")
            self.attrib_radio_button[i].set_selected(attr)
        
        # 6-7. Skills & Expertises (unchanged)
        if self.avaliable_skills:
            self.selected_skills = random.choices(self.avaliable_skills, k=self.skill_len)
            self._set_selected_skills([], self.selected_skills)
        
        self.selected_expertises = random.sample(list(CharacterExpertise), 4)
        self._change_expertise([], self.selected_expertises)
        
        # 8. Refresh visuals
        self._update_attrib_checklist()
        
        print("✅ Random character generated with visual updates!")

    def _change_expertise(self, previous, actual):
        self.selected_expertises = actual

    """     def _build_scene_attribs(self, screen):
            item_width = 180  # Adjusted smaller
            item_height = 200
            h_spacing = 4
            v_spacing = 11

            start_x = (self.skills_radio_button.position[0]
                    + self.skills_radio_button.rect.width + 620)
            start_y = self.skills_radio_button.position[1]

            available_width = screen.get_width() - start_x
            columns = max(1, available_width // (item_width + h_spacing))

            return [
                RadioButtonGroup(
                    label_str=f"Value: {value}",  # UX win: Focus on rolled value
                    position=grid_position(
                        index=index,
                        start_x=start_x, start_y=start_y,
                        item_width=item_width, item_height=item_height,
                        columns=columns, h_spacing=h_spacing, v_spacing=v_spacing
                    ),
                    options=[(attrib.value, attrib) for attrib in CharacterAttrib],
                    on_change=lambda p, x, val=value: self._set_selected_attribs(p, x, val)
                )
                for index, value in enumerate(self.rolled_atribs)
            ]
    """
    def _build_scene_attribs(self, screen: pygame.Surface) -> List[SceneElement]:
        # Configuração de Grid para 6 colunas (uma para cada valor rolado)
        item_width = 110
        # item_height = 200 # Altura para caber os 6 atributos dentro de cada grupo
        h_spacing = 58
        
        # Posicionamento: Começa após as expertises (Coluna 4)
        start_x = screen.get_width() * 0.35 
        start_y = 90

        # Criamos os 6 grupos de rádio (um para cada dado rolado)
        radio_groups = []
        for index, value in enumerate(self.rolled_atribs):
            # pos = (start_x, start_y + (index * 45)) # Empilhamento vertical ou horizontal
            x = start_x + index * (item_width + h_spacing)
            y = start_y
            pos = (x, y)

            rg = RadioButtonGroup(
                label_str=f"Dado: {value}",
                position=pos,
                options=[(attr.value.capitalize(), attr) for attr in CharacterAttrib],
                on_change=None  # Will be set in __init__ loop
            )
            radio_groups.append(rg)

        return radio_groups

    def _gerar_nome(self, tamanho: int = 6, iniciar_com_consoante: bool = True) -> str:
        vogais = "aeiou"
        consoantes = "bcdfghjklmnpqrstvwxyz"

        nome = []
        usar_consoante = iniciar_com_consoante

        for _ in range(tamanho):
            if usar_consoante:
                nome.append(random.choice(consoantes))
            else:
                nome.append(random.choice(vogais))
            usar_consoante = not usar_consoante

        return "".join(nome).capitalize()
