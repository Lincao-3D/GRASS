from typing import Tuple, Optional, List

import pygame

from src.engine.ui.UIElement import UIElement
from src.utils import get_default_font


class TextAreaShow(UIElement):

    def __init__(self, position: Tuple[int, int],width:int,height:int,text:str="",text_size:int = 12,padding:int = 12,background_color:Tuple[int,int,int] = (0,0,0),border_color:Tuple[int,int,int] = (255,255,255),text_color:Tuple[int,int,int]= (255,255,255)):
        super().__init__(None, position)
        self.width = width
        self.height = height
        self.padding = padding
        self.background_color = background_color
        self.border_color = border_color
        self.rect = pygame.rect.Rect(self.position[0],self.position[1],self.width,self.height)
        self.text_color = text_color
        self.font = get_default_font(text_size)
        try:
            from src.utils import get_assets_path
            import os
            self.font_bold = pygame.font.Font(os.path.join(get_assets_path(), "font.ttf"), text_size)
            self.font_bold.set_bold(True)
        except:
            self.font_bold = self.font
        
        self._text = ""
        self._cached_lines = []
        self.scroll_offset = 0
        self.focused = False
        
        # Now set the property, triggering the setter to wrap the initial text
        self.text = text

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if not hasattr(self, '_text') or self._text != value:
            self._text = value
            self._cached_lines = self._wrap_text()
            # Auto-scroll to bottom on text change:
            if hasattr(self, 'font'):
                line_height = self.font.get_height()
                max_visible_lines = (self.height - 2 * self.padding) // line_height
                total_lines = len(self._cached_lines)
                if total_lines > max_visible_lines:
                    self.scroll_offset = total_lines - max_visible_lines
                else:
                    self.scroll_offset = 0

    def _wrap_text(self) -> List[List[Tuple[str, bool]]]:
        import re
        lines: List[List[Tuple[str, bool]]] = []
        current_line: List[Tuple[str, bool]] = []
        current_line_width = 0
        max_width = self.width - 2 * self.padding

        # Split into paragraphs
        for paragraph in self._text.split("\n"):
            # Use regex to find **bold** segments
            # This matches **text** or non-** text
            parts = re.split(r'(\*\*.*?\*\*)', paragraph)
            
            for part in parts:
                if not part: continue
                is_bold = part.startswith("**") and part.endswith("**")
                clean_part = part[2:-2] if is_bold else part
                font = self.font_bold if is_bold else self.font
                
                # Split part into words to handle wrapping within a bold segment
                words = clean_part.split(" ")
                for i, word in enumerate(words):
                    display_word = word + (" " if i < len(words) - 1 else "")
                    word_width = font.size(display_word)[0]
                    
                    if current_line_width + word_width <= max_width:
                        current_line.append((display_word, is_bold))
                        current_line_width += word_width
                    else:
                        lines.append(current_line)
                        current_line = [(display_word, is_bold)]
                        current_line_width = word_width
            
            # End of paragraph
            lines.append(current_line)
            current_line = []
            current_line_width = 0

        return lines

    def render(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        # Fundo + Borda (unchanged)
        pygame.draw.rect(surface, self.background_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        
        # Use cached lines instead of wrapping every frame
        lines = self._cached_lines
        line_height = self.font.get_height()
        max_visible_lines = (self.height - 2 * self.padding) // line_height
        
        total_lines = len(lines)
        
        # Render visible lines
        visible_lines = lines[self.scroll_offset:self.scroll_offset + max_visible_lines]
        
        y = self.rect.y + self.padding
        for line_segments in visible_lines:
            x = self.rect.x + self.padding
            for segment_text, is_bold in line_segments:
                font = self.font_bold if is_bold else self.font
                color = (255, 215, 0) if is_bold else self.text_color # Gold for bold
                text_surf = font.render(segment_text, True, color)
                surface.blit(text_surf, (x, y))
                x += text_surf.get_width()
            y += line_height

        # Draw visual scrollbar if total_lines > max_visible_lines
        if total_lines > max_visible_lines:
            scrollbar_width = 6
            scrollbar_margin = 4
            track_x = self.rect.right - scrollbar_width - scrollbar_margin
            track_y = self.rect.y + scrollbar_margin
            track_height = self.rect.height - 2 * scrollbar_margin
            
            # Calculate thumb height
            thumb_height = max(15, int(track_height * (max_visible_lines / total_lines)))
            
            # Calculate thumb position
            max_scroll_offset = total_lines - max_visible_lines
            if max_scroll_offset > 0:
                scroll_fraction = self.scroll_offset / max_scroll_offset
                thumb_y = track_y + int(scroll_fraction * (track_height - thumb_height))
            else:
                thumb_y = track_y
                
            thumb_surf = pygame.Surface((scrollbar_width, thumb_height), pygame.SRCALPHA)
            thumb_surf.fill((255, 255, 255, 120))  # Semi-transparent white
            surface.blit(thumb_surf, (track_x, thumb_y))

    def update(self, event: pygame.event.Event, mouse_position: Tuple[int, int]):
        if event is None:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.focused = self.rect.collidepoint(mouse_position)

        if not self.focused:
            return

        if event.type == pygame.MOUSEWHEEL:
            lines = self._cached_lines
            total_lines = len(lines)
            line_height = self.font.get_height()
            visible_lines = (self.height - 2 * self.padding) // line_height
            max_scroll_offset = max(0, total_lines - visible_lines)
            if event.y == 1:
                if self.scroll_offset < max_scroll_offset:
                    self.scroll_offset += 1
            elif event.y == -1:
                if self.scroll_offset > 0:
                    self.scroll_offset -= 1