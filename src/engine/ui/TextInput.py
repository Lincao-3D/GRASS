from typing import Tuple, Callable, Optional, List

import pygame

from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.UIElement import UIElement
from src.utils import get_default_font, typewriter_sound


class TextInput(UIElement):
    def __init__(self, position: Tuple[int,int], width: int,height:int = 24,initial_text:str="", background_color:Tuple[int,int,int] = (255, 255, 255),focus_background_color:Tuple[int,int,int] = (50, 100, 255),text_size:int = 12, text_color:Tuple[int,int,int] = (255, 255, 255), padding: int = 6, border_width = 1,label_str: str = None,label_top: bool=True,label_size:int = 24,on_change: Optional[Callable[[str],None]] = None,on_submit: Optional[Callable[[str],None]] = None):
        super().__init__(None,position)
        self.width = width
        self.base_height = height
        self.padding = padding
        self.text_size = text_size
        self.text_color = text_color
        self.background_color = background_color
        self.focus_background_color = focus_background_color
        self.focus = False
        self.border_width = border_width
        self.font = get_default_font(text_size)
        self.text_str = initial_text
        self.rect = pygame.Rect(position[0], position[1], width, height)
        self.base_y = position[1]
        
        self.on_change = on_change
        self.on_submit = on_submit
        self.label = None
        if label_str:
            self.label = SimpleText(
                size=label_size,
                text_color=text_color,
                position=(position[0], position[1] - height) if label_top else (position[0] - get_default_font(label_size).size(label_str)[0] - 5, position[1]),
                text=label_str
            )
        
        self._update_rect()

    def _wrap_text(self) -> List[str]:
        words = self.text_str.split(' ')
        lines = []
        current_line = ""
        max_w = self.width - (2 * self.padding)
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if self.font.size(test_line)[0] <= max_w:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return lines

    def _update_rect(self):
        lines = self._wrap_text()
        line_height = self.font.get_height()
        new_height = max(self.base_height, len(lines) * line_height + (self.padding * 2))
        
        # Grow UPWARDS: subtract difference from base_y
        self.rect.height = new_height
        self.rect.y = self.base_y - (new_height - self.base_height)

    def _on_change(self):
        typewriter_sound()
        self._update_rect()
        if self.on_change:
            self.on_change(self.text_str)

    def render(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        # Draw background/border
        color = self.focus_background_color if self.focus else self.background_color
        pygame.draw.rect(surface, color, self.rect, width=self.border_width)
        
        # Draw lines
        lines = self._wrap_text()
        line_height = self.font.get_height()
        y = self.rect.y + self.padding
        
        show_cursor = self.focus and (pygame.time.get_ticks() % 1000 < 500)
        
        for i, line in enumerate(lines):
            line_to_render = line
            if show_cursor and i == len(lines) - 1:
                line_to_render = line + "|"
            txt_surf = self.font.render(line_to_render, True, self.text_color)
            surface.blit(txt_surf, (self.rect.x + self.padding, y))
            y += line_height
            
        if self.label:
            self.label.render(surface)

    def update(self, event: pygame.event.Event, mouse_position: Tuple[int, int]):
        if not event:
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mouse_position):
                self.focus = True
                pygame.key.start_text_input()
            else:
                self.focus = False
                pygame.key.stop_text_input()

        if not self.focus:
            return

        if event.type == pygame.TEXTINPUT:
            self.text_str += event.text
            self._on_change()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text_str = self.text_str[:-1]
                self._on_change()
            if event.key == pygame.K_RETURN:
                if self.on_submit:
                    self.on_submit(self.text_str)
                    self.text_str = ""
                    self._on_change()

    def change_text(self, text: str):
        self.text_str = text
        self._on_change()

    @property
    def text(self):
        # Mocking old API for compatibility if needed
        class MockText:
            def __init__(self, parent): self.parent = parent
            @property
            def text(self): return self.parent.text_str
            @text.setter
            def text(self, val): self.parent.text_str = val
            def change_text(self, val): self.parent.change_text(val)
        return MockText(self)
