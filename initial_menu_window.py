import pygame
import sys
import math
import random
import logging
import re

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BACKGROUND_COLOR = (10, 10, 20)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('WarOfCellsGame')


def validate_ip_port(ip, port):
    ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if not re.match(ip_pattern, ip):
        return False, "Invalid IP format"

    parts = ip.split(".")
    if not all(0 <= int(part) <= 255 for part in parts):
        return False, "Each IP segment must be between 0–255"

    try:
        port = int(port)
        if not (1024 <= port <= 65535):
            return False, "Port must be in range 1024–65535"
    except ValueError:
        return False, "Port must be a number"

    return True, ""


class Cell:

    def __init__(self, x, y, size, is_player=True):
        self.x = x
        self.y = y
        self.size = size
        self.is_player = is_player
        self.color = (50, 100, 255) if is_player else (255, 50, 50)
        self.pulse_value = random.random() * math.pi * 2
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)

    def update(self):
        self.x += self.vx
        self.y += self.vy

        self.vx *= 0.99
        self.vy *= 0.99

        self.vx += random.uniform(-0.1, 0.1)
        self.vy += random.uniform(-0.1, 0.1)

        if self.x < -20:
            self.x = SCREEN_WIDTH + 20
        elif self.x > SCREEN_WIDTH + 20:
            self.x = -20

        if self.y < -20:
            self.y = SCREEN_HEIGHT + 20
        elif self.y > SCREEN_HEIGHT + 20:
            self.y = -20

        self.pulse_value = (self.pulse_value + 0.05) % (math.pi * 2)

    def draw(self, screen):
        pulse = (math.sin(self.pulse_value) + 1) / 2
        glow_size = self.size + 5 + pulse * 3

        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_color = (self.color[0], self.color[1], self.color[2], 150 + int(pulse * 60))
        pygame.draw.circle(glow_surface, glow_color, (glow_size, glow_size), glow_size)
        screen.blit(glow_surface, (self.x - glow_size, self.y - glow_size))

        pygame.draw.circle(screen, self.color, (self.x, self.y), self.size)

        highlight_size = self.size * 0.7
        highlight_color = (min(255, self.color[0] + 50),
                           min(255, self.color[1] + 50),
                           min(255, self.color[2] + 50))
        pygame.draw.circle(screen, highlight_color,
                           (self.x - self.size * 0.2, self.y - self.size * 0.2),
                           highlight_size)


class MenuWindow:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("War of Cells Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
        self.small_font = pygame.font.SysFont('Arial', 18)

        self.modes = ["Single player", "Local multiplayer", "Online game"]
        self.selected_mode = 0
        self.ip_input = "127.0.0.1"
        self.port_input = "12345"
        self.active_input = None
        self.error_message = ""

        self.background = self.create_background()
        self.cells = []
        self.create_background_cells()

        self.running = True
        self.config = None
        self.menu_loop()

    def create_background(self):
        gradient_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(10 + 20 * ratio)
            g = int(10 + 30 * ratio)
            b = int(20 + 40 * ratio)
            color = (r, g, b)
            pygame.draw.line(gradient_surface, color, (0, y), (SCREEN_WIDTH, y))

        for _ in range(100):
            x = random.randint(0, SCREEN_WIDTH - 1)
            y = random.randint(0, SCREEN_HEIGHT - 1)
            brightness = random.randint(100, 200)
            size = random.randint(1, 3)
            color = (brightness, brightness, brightness)
            pygame.draw.circle(gradient_surface, color, (x, y), size)

        return gradient_surface

    def create_background_cells(self):
        for _ in range(10):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(10, 25)
            is_player = random.choice([True, False])
            self.cells.append(Cell(x, y, size, is_player))

    def draw_text(self, text, x, y, selected=False, small=False, color=None):
        if color is None:
            color = (0, 255, 0) if selected else (255, 255, 255)
        font = self.small_font if small else self.font
        rendered = font.render(text, True, color)
        self.screen.blit(rendered, (x, y))
        return rendered

    def menu_loop(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            pygame.display.flip()
            self.clock.tick(FPS)

    def update(self):
        for cell in self.cells:
            cell.update()

    def render(self):
        self.screen.blit(self.background, (0, 0))

        for cell in self.cells:
            cell.draw(self.screen)

        title_text = "WAR OF CELLS"
        title_surface = self.title_font.render(title_text, True, (180, 200, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))

        glow_surface = pygame.Surface((title_rect.width + 20, title_rect.height + 20), pygame.SRCALPHA)
        pulse = (math.sin(pygame.time.get_ticks() * 0.003) + 1) / 2
        glow_color = (100, 120, 255, int(100 + pulse * 100))
        pygame.draw.rect(glow_surface, glow_color, (10, 10, title_rect.width, title_rect.height), 5)
        self.screen.blit(glow_surface, (title_rect.x - 10, title_rect.y - 10))

        self.screen.blit(title_surface, title_rect)

        self.draw_text("Select game mode:", SCREEN_WIDTH // 2 - 100, 150)

        panel_width = 300
        panel_height = 50

        for i, mode in enumerate(self.modes):
            y_pos = 200 + i * 60

            if i == self.selected_mode:
                panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - panel_width // 2, y_pos - 10, panel_width, panel_height)
                panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)

                pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
                alpha = int(100 + pulse * 100)

                if mode == "Single player":
                    panel_color = (50, 100, 255, alpha)
                elif mode == "Local multiplayer":
                    panel_color = (100, 180, 100, alpha)
                else:
                    panel_color = (200, 100, 100, alpha)

                panel_surface.fill(panel_color)
                self.screen.blit(panel_surface, panel_rect)

                pygame.draw.rect(self.screen, (255, 255, 255), panel_rect, 2)

            color = (255, 255, 255) if i == self.selected_mode else (200, 200, 200)
            text_surface = self.font.render(mode, True, color)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y_pos + 15))
            self.screen.blit(text_surface, text_rect)

        if self.modes[self.selected_mode] == "Online game":
            panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 380, 300, 120)
            panel_surface = pygame.Surface((300, 120), pygame.SRCALPHA)
            panel_surface.fill((30, 30, 60, 180))
            self.screen.blit(panel_surface, panel_rect)
            pygame.draw.rect(self.screen, (100, 100, 200), panel_rect, 2)

            self.draw_text("IP Address:", panel_rect.x + 20, panel_rect.y + 20)
            ip_box_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 45, 260, 30)
            pygame.draw.rect(self.screen, (50, 50, 80), ip_box_rect)
            pygame.draw.rect(self.screen, (150, 150, 255) if self.active_input == "ip" else (100, 100, 150),
                             ip_box_rect, 2)
            self.draw_text(self.ip_input, ip_box_rect.x + 10, ip_box_rect.y + 5)

            self.draw_text("Port:", panel_rect.x + 20, panel_rect.y + 80)
            port_box_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 105, 260, 30)
            pygame.draw.rect(self.screen, (50, 50, 80), port_box_rect)
            pygame.draw.rect(self.screen, (150, 150, 255) if self.active_input == "port" else (100, 100, 150),
                             port_box_rect, 2)
            self.draw_text(self.port_input, port_box_rect.x + 10, port_box_rect.y + 5)

            self.ip_box_rect = ip_box_rect
            self.port_box_rect = port_box_rect
        else:
            self.ip_box_rect = None
            self.port_box_rect = None

        help_surface = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA)
        help_surface.fill((0, 0, 0, 150))
        self.screen.blit(help_surface, (0, SCREEN_HEIGHT - 80))

        self.draw_text("ENTER = Confirm and start game", 50, SCREEN_HEIGHT - 70, small=True)
        self.draw_text("↑/↓ = Navigate menu", 50, SCREEN_HEIGHT - 45, small=True)

        if self.modes[self.selected_mode] == "Online game":
            self.draw_text("TAB = Switch input field", 50, SCREEN_HEIGHT - 20, small=True)

        if self.error_message:
            error_bg = pygame.Surface((300, 40), pygame.SRCALPHA)
            error_bg.fill((100, 0, 0, 180))
            error_rect = error_bg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            self.screen.blit(error_bg, error_rect)

            error_text = self.small_font.render(self.error_message, True, (255, 150, 150))
            error_text_rect = error_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            self.screen.blit(error_text, error_text_rect)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("Menu closed.")
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    self.selected_mode = (self.selected_mode + 1) % len(self.modes)
                elif event.key == pygame.K_UP:
                    self.selected_mode = (self.selected_mode - 1) % len(self.modes)

                elif event.key == pygame.K_TAB and self.modes[self.selected_mode] == "Online game":
                    if self.active_input == "ip":
                        self.active_input = "port"
                    elif self.active_input == "port" or self.active_input is None:
                        self.active_input = "ip"

                elif event.key == pygame.K_RETURN:
                    if self.modes[self.selected_mode] == "Online game":
                        is_valid, error = validate_ip_port(self.ip_input, self.port_input)
                        if not is_valid:
                            self.error_message = error
                            logger.warning(f"Validation error: {error}")
                        else:
                            self.config = {
                                "mode": self.modes[self.selected_mode],
                                "ip": self.ip_input,
                                "port": self.port_input
                            }
                            logger.info(f"Configuration saved: {self.config}")
                            self.error_message = ""
                            self.running = False
                    else:
                        self.config = {
                            "mode": self.modes[self.selected_mode]
                        }
                        logger.info(f"Configuration saved: {self.config}")
                        self.running = False

                elif self.active_input:
                    if event.key == pygame.K_BACKSPACE:
                        if self.active_input == "ip":
                            self.ip_input = self.ip_input[:-1]
                        elif self.active_input == "port":
                            self.port_input = self.port_input[:-1]
                    else:
                        if self.active_input == "ip":
                            if event.unicode.isdigit() or event.unicode == '.':
                                self.ip_input += event.unicode
                        elif self.active_input == "port" and event.unicode.isdigit():
                            self.port_input += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                if self.ip_box_rect and self.ip_box_rect.collidepoint(mouse_pos):
                    self.active_input = "ip"
                elif self.port_box_rect and self.port_box_rect.collidepoint(mouse_pos):
                    self.active_input = "port"
                else:
                    self.active_input = None


def main():
    menu = MenuWindow()

    if menu.config:
        try:
            print(f"Starting game with config: {menu.config}")

            #game = Game(menu.config)
            #game.run()
            pass
        except Exception as e:
            logger.error(f"Error starting game: {e}")

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
