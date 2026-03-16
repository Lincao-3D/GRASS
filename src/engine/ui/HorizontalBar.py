import pygame
import math
from src.engine.ui.UIElement import UIElement

class HorizontalBar(UIElement):
    def __init__(self, x, y, width, text="PLACEHOLDER"):
        super().__init__(x, y)
        self.width = width
        self.height = 30  # 3 linhas de ~10px
        self.text = text
        self.font = pygame.font.Font("assets/font.ttf", 18)
        
        # Cores
        self.COLOR_BLACK = (0, 0, 0)
        self.COLOR_DARK_GRAY = (40, 40, 40)
        self.COLOR_WHITE = (255, 255, 255)
        
        self.row_height = 8
        self.offset = 15  # Deslocamento entre linhas
        self.edge_width = 25 # Largura da seção ▤

    def draw(self, screen):
        now = pygame.time.get_ticks()
        # Efeito de piscar baseado no tempo (senoide)
        flash_alpha = (math.sin(now * 0.01) + 1) / 2
        flash_color = [int(40 + (60 * flash_alpha))] * 3 # Oscila entre cinza escuro e claro

        for i in range(3):
            # Calcula o deslocamento horizontal da linha (escada)
            row_x = self.x + (i * self.offset)
            row_y = self.y + (i * (self.row_height + 2))
            
            # 1. Desenha as extremidades "▤" (Piscantes)
            # Esquerda
            pygame.draw.rect(screen, flash_color, (row_x, row_y, self.edge_width, self.row_height))
            # Direita
            pygame.draw.rect(screen, flash_color, (row_x + self.width - self.edge_width, row_y, self.edge_width, self.row_height))
            
            # 2. Desenha o centro "■" (Preto sólido)
            center_x = row_x + self.edge_width
            center_width = self.width - (2 * self.edge_width)
            pygame.draw.rect(screen, self.COLOR_BLACK, (center_x, row_y, center_width, self.row_height))

        # 3. Texto Placeholder centralizado no topo
        text_surf = self.font.render(self.text, True, self.COLOR_WHITE)
        text_rect = text_surf.get_rect(center=(self.x + self.width // 2 + self.offset, self.y - 15))
        screen.blit(text_surf, text_rect)
