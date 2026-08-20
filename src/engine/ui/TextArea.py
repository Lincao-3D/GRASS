import json
import re
from typing import Tuple, Optional, List, Dict, Any
import pygame

from src.engine.ui.UIElement import UIElement
from src.utils import get_default_font


class TextAreaShow(UIElement):

    def __init__(
        self, 
        position: Tuple[int, int], 
        width: int, 
        height: int, 
        text: str = "", 
        text_size: int = 14, 
        padding: int = 12, 
        background_color: Tuple[int, int, int] = (15, 15, 22), 
        border_color: Tuple[int, int, int] = (60, 60, 80), 
        text_color: Tuple[int, int, int] = (220, 220, 220)
    ):
        super().__init__(None, position)
        self.width = width
        self.height = height
        self.padding = padding
        self.background_color = background_color
        self.border_color = border_color
        self.rect = pygame.Rect(self.position[0], self.position[1], self.width, self.height)
        self.text_color = text_color
        
        self.font = get_default_font(text_size)
        
        try:
            from src.utils import get_assets_path
            import os
            self.font_bold = pygame.font.Font(os.path.join(get_assets_path(), "font.ttf"), text_size)
            self.font_bold.set_bold(True)
        except Exception:
            self.font_bold = pygame.font.SysFont("Arial", text_size, bold=True)

        try:
            self.font_card_title = pygame.font.SysFont("Georgia", text_size + 1, bold=True)
        except Exception:
            self.font_card_title = self.font_bold

        self._text = ""
        self._cached_lines = []
        self.scroll_y = 0  # Pixel-based vertical scroll
        self.focused = False
        
        # Scrollbar interaction state
        self.dragging_scrollbar = False

        self.text = text

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if not hasattr(self, '_text') or self._text != value:
            self._text = value
            self._cached_lines = self._wrap_text()
            
            # Auto-scroll to bottom on text updates
            total_height = sum(item[2] for item in self._cached_lines)
            visible_height = self.height - 2 * self.padding
            max_scroll = max(0, total_height - visible_height)
            self.scroll_y = max_scroll

    def _calculate_card_height(self, card_data: Dict[str, Any]) -> int:
        """Calculates exact pixel height for a combat card."""
        header_h = 28
        item_h = 20
        inimigos = card_data.get("inimigos", [])
        return header_h + (len(inimigos) * item_h) + 20 # Height + bottom margin

    def _wrap_text(self) -> List[Tuple[Any, str, int]]:
        """
        Parses incoming text stream into layout items.
        Supports both markdown ```json blocks and raw JSON { ... } blocks.
        Returns tuples of: (payload, item_type, pixel_height)
        """
        lines_out = []
        max_width = self.width - 2 * self.padding
        line_height = self.font.get_height()
        
        text = self._text
        import json
        import re
        
        # 1. Identify all JSON blocks (markdown wrapped first, then raw brace-wrapped objects)
        blocks = [] # List of (start_idx, end_idx, parsed_data)
        
        # Match markdown blocks
        for m in re.finditer(r'```json\s*(.*?)\s*```', text, re.DOTALL):
            try:
                data = json.loads(m.group(1))
                blocks.append((m.start(), m.end(), data))
            except Exception:
                pass
                
        # Match raw JSON objects (not inside already identified blocks)
        stack = []
        start_idx = -1
        for i, char in enumerate(text):
            inside = False
            for b_start, b_end, _ in blocks:
                if b_start <= i < b_end:
                    inside = True
                    break
            if inside:
                continue
                
            if char == '{':
                if not stack:
                    start_idx = i
                stack.append('{')
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        candidate = text[start_idx:i+1]
                        try:
                            data = json.loads(candidate)
                            blocks.append((start_idx, i+1, data))
                        except ValueError:
                            pass
                            
        # Sort blocks by start index
        blocks.sort(key=lambda x: x[0])
        
        # Segment the text into alternating text and card payloads
        last_idx = 0
        segments = []
        for b_start, b_end, data in blocks:
            if b_start > last_idx:
                segments.append((text[last_idx:b_start], 'text'))
            segments.append((data, 'card'))
            last_idx = b_end
        if last_idx < len(text):
            segments.append((text[last_idx:], 'text'))
            
        # Process and wrap each segment
        for payload, seg_type in segments:
            if seg_type == 'card':
                card_h = self._calculate_card_height(payload)
                lines_out.append((payload, 'card', card_h))
            else:
                raw_lines = payload.split("\n")
                for raw_line in raw_lines:
                    parts = re.split(r'(\*\*.*?\*\*)', raw_line)
                    current_line = []
                    current_line_width = 0
                    
                    for part in parts:
                        if not part: continue
                        is_bold = part.startswith("**") and part.endswith("**")
                        clean_part = part[2:-2] if is_bold else part
                        font = self.font_bold if is_bold else self.font
                        
                        words = clean_part.split(" ")
                        for i, word in enumerate(words):
                            display_word = word + (" " if i < len(words) - 1 else "")
                            word_width = font.size(display_word)[0]
                            style = 'bold' if is_bold else 'normal'
                            
                            if current_line_width + word_width <= max_width:
                                current_line.append((display_word, style))
                                current_line_width += word_width
                            else:
                                if current_line:
                                    lines_out.append((current_line, 'text', line_height))
                                current_line = [(display_word, style)]
                                current_line_width = word_width
                    if current_line or not raw_line:
                        lines_out.append((current_line, 'text', line_height))
                        
        return lines_out

    def _get_scrollbar_metrics(self, total_height: int, visible_height: int):
        """Calculates exact rects for scrollbar track and thumb."""
        scrollbar_width = 8
        scrollbar_margin = 4
        track_x = self.rect.right - scrollbar_width - scrollbar_margin
        track_y = self.rect.y + scrollbar_margin
        track_height = self.rect.height - 2 * scrollbar_margin
        
        if total_height <= visible_height:
            return None, None, track_y, track_height
            
        thumb_height = max(20, int(track_height * (visible_height / total_height)))
        max_scroll = total_height - visible_height
        
        scroll_fraction = self.scroll_y / max_scroll if max_scroll > 0 else 0
        thumb_y = track_y + int(scroll_fraction * (track_height - thumb_height))
            
        track_rect = pygame.Rect(track_x - 4, track_y, scrollbar_width + 8, track_height)
        thumb_rect = pygame.Rect(track_x, thumb_y, scrollbar_width, thumb_height)
        return track_rect, thumb_rect, track_y, track_height

    def _render_combat_card(self, surface: pygame.Surface, card_data: Dict[str, Any], x: int, y: int):
        """Renders an inline combat card badge."""
        card_w = self.width - (2 * self.padding) - 8 # Reserved right margin for scrollbar
        inimigos = card_data.get("inimigos", [])
        
        header_h = 28
        item_h = 20
        total_card_h = header_h + (len(inimigos) * item_h) + 12
        card_rect = pygame.Rect(x, y, card_w, total_card_h)
        
        # Surface Card Box
        pygame.draw.rect(surface, (28, 20, 24), card_rect, border_radius=4)
        pygame.draw.rect(surface, (180, 50, 50), card_rect, width=1, border_radius=4)
        
        # Red Accent Strip
        marker_rect = pygame.Rect(x, y, 5, total_card_h)
        pygame.draw.rect(surface, (220, 60, 60), marker_rect, border_top_left_radius=4, border_bottom_left_radius=4)
        
        # Card Header
        title_str = f"⚔  EVENTO DE {card_data.get('evento', 'COMBATE').upper()}"
        title_surf = self.font_card_title.render(title_str, True, (220, 60, 60))
        surface.blit(title_surf, (x + 14, y + 5))
        
        pygame.draw.line(surface, (80, 35, 35), (x + 10, y + header_h), (x + card_w - 10, y + header_h), 1)
        
        # Enemy Listing
        curr_y = y + header_h + 6
        for enemy in inimigos:
            nome = enemy.get("nome", "Desconhecido")
            qtd = enemy.get("quantidade", 1)
            
            qty_surf = self.font_bold.render(f"{qtd}x", True, (245, 215, 110))
            surface.blit(qty_surf, (x + 18, curr_y))
            
            name_surf = self.font.render(nome, True, (230, 230, 230))
            surface.blit(name_surf, (x + 48, curr_y))
            
            curr_y += item_h

    def render(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        # 1. Main Background Box
        pygame.draw.rect(surface, self.background_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        
        visible_height = self.height - 2 * self.padding
        total_height = sum(item[2] for item in self._cached_lines)
        
        # 2. Viewport Clipping (Prevents overflow out of text box)
        viewport_rect = pygame.Rect(
            self.rect.x + self.padding, 
            self.rect.y + self.padding, 
            self.width - 2 * self.padding, 
            visible_height
        )
        old_clip = surface.get_clip()
        surface.set_clip(viewport_rect.clip(old_clip))
        
        # 3. Render Items with Pixel Offset
        y = self.rect.y + self.padding - self.scroll_y
        x = self.rect.x + self.padding

        for payload, line_type, item_h in self._cached_lines:
            # Culling Check
            if y + item_h < viewport_rect.top:
                y += item_h
                continue
            if y > viewport_rect.bottom:
                break
                
            if line_type == 'card':
                self._render_combat_card(surface, payload, x, y)
            else:
                for segment_text, style in payload:
                    font = self.font_bold if style == 'bold' else self.font
                    color = (255, 215, 0) if style == 'bold' else self.text_color
                    text_surf = font.render(segment_text, True, color)
                    surface.blit(text_surf, (x, y))
                    x += text_surf.get_width()
                x = self.rect.x + self.padding
            
            y += item_h

        # Restore Clipping
        surface.set_clip(old_clip)

        # 4. Render Scrollbar (Unclipped on Top)
        if total_height > visible_height:
            _, thumb_rect, _, _ = self._get_scrollbar_metrics(total_height, visible_height)
            if thumb_rect:
                thumb_surf = pygame.Surface((thumb_rect.width, thumb_rect.height), pygame.SRCALPHA)
                thumb_color = (220, 220, 220, 200) if self.dragging_scrollbar else (255, 255, 255, 120)
                thumb_surf.fill(thumb_color)
                surface.blit(thumb_surf, thumb_rect.topleft)

    def update(self, event: Optional[pygame.event.Event], mouse_position: Tuple[int, int]):
        total_height = sum(item[2] for item in self._cached_lines)
        visible_height = self.height - 2 * self.padding
        max_scroll = max(0, total_height - visible_height)

        # Handle dragging scrollbar thumb continuously
        if self.dragging_scrollbar and max_scroll > 0:
            track_rect, thumb_rect, track_y, track_height = self._get_scrollbar_metrics(total_height, visible_height)
            if thumb_rect:
                thumb_h = thumb_rect.height
                rel_y = mouse_position[1] - track_y - (thumb_h // 2)
                fraction = max(0.0, min(1.0, rel_y / (track_height - thumb_h)))
                self.scroll_y = int(fraction * max_scroll)

        if event is None:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.focused = self.rect.collidepoint(mouse_position)
            if self.focused and max_scroll > 0:
                track_rect, thumb_rect, track_y, track_height = self._get_scrollbar_metrics(total_height, visible_height)
                if thumb_rect and thumb_rect.collidepoint(mouse_position):
                    self.dragging_scrollbar = True
                elif track_rect and track_rect.collidepoint(mouse_position):
                    # Direct track click jump
                    thumb_h = thumb_rect.height if thumb_rect else 20
                    rel_y = mouse_position[1] - track_y - (thumb_h // 2)
                    fraction = max(0.0, min(1.0, rel_y / (track_height - thumb_h)))
                    self.scroll_y = int(fraction * max_scroll)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging_scrollbar = False

        if not self.focused:
            return

        # Smooth Pixel Mouse-Wheel Scroll
        if event.type == pygame.MOUSEWHEEL:
            scroll_speed = 24 # Pixels per notch
            if event.y == 1: # Wheel Up
                self.scroll_y = max(0, self.scroll_y - scroll_speed)
            elif event.y == -1: # Wheel Down
                self.scroll_y = min(max_scroll, self.scroll_y + scroll_speed)