import pygame
from src.engine.ui.UIElement import UIElement

class Toggle(UIElement):

    def __init__(self, position, value, on_toggle):
        self.x, self.y = position
        self.width = 50
        self.height = 24
        self.value = value
        self.on_toggle = on_toggle

    def update(self, event, mouse_pos):

        if event is None:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._mouse_over(mouse_pos):

                self.value = not self.value

                if self.on_toggle:
                    self.on_toggle(self.value)

    def render(self, screen):

        color = (200,0,0) if self.value else (0,200,0)

        pygame.draw.rect(
            screen,
            color,
            (self.x,self.y,self.width,self.height)
        )

    def _mouse_over(self, mouse_pos):

        mx,my = mouse_pos

        return (
            self.x <= mx <= self.x+self.width
            and self.y <= my <= self.y+self.height
        )