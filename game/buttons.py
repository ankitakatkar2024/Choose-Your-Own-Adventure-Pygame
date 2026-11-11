
import pygame


class Button:

    def __init__(
        self,
        x,
        y,
        width,
        height,
        text,
        color,
        text_color=(255, 255, 255)
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color

    def draw(self, screen, font):

        mouse_position = pygame.mouse.get_pos()

        button_color = self.color

        # Hover effect
        if self.rect.collidepoint(mouse_position):
            button_color = tuple(
                min(value + 25, 255)
                for value in self.color
            )

        pygame.draw.rect(
            screen,
            button_color,
            self.rect,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            (255, 255, 255),
            self.rect,
            width=2,
            border_radius=12
        )

        text_surface = font.render(
            self.text,
            True,
            self.text_color
        )

        text_rect = text_surface.get_rect(
            center=self.rect.center
        )

        screen.blit(text_surface, text_rect)

    def is_clicked(self, event):

        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )
