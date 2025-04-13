import pygame
import sys
import math
import random
import colorsys
from enum import Enum, auto
from typing import List, Dict, Tuple, Optional
import logging
import json
from level_editor import *
from initial_menu_window import *
from game_recorder import *
from game_playback import *
#from client import *
#from server import *

pygame.init()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('WarOfCEllsGame')

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BACKGROUND_COLOR = (10, 10, 20)

CELL_RADIUS = 30
POINT_GROWTH_INTERVAL = 3000  # ms
POINT_GROWTH_INTERVAL_new = POINT_GROWTH_INTERVAL
BALL_SPEED = 2
BALL_RADIUS = 5
BRIDGE_WIDTH = 3

PLAYER_COLOR = (50, 100, 255)  # Blue
ENEMY_COLOR = (255, 50, 50)  # Red
EMPTY_COLOR = (50, 50, 50)  # Dark Gray
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class CellType(Enum):
    EMPTY = 0
    PLAYER = 1
    ENEMY = 2


class CellShape(Enum):
    CIRCLE = 0
    TRIANGLE = 1
    RECTANGLE = 2


class EvolutionLevel(Enum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3


class BridgeDirection(Enum):
    ONE_WAY = 0
    TWO_WAY = 1


class AIStrategy(Enum):
    AGGRESSIVE = 0  # focus on attacking enemy cells
    DEFENSIVE = 1  #focus on protecting and upgrading own cells
    EXPANSIVE = 2  # focus on capturing empty cells
    BALANCED = 3  #mix of all strategies

class GameType(Enum):
    SINGLE_PLAYER=0
    LOCAL_MULTI=1
    ONLINE=2

    @classmethod
    def from_string(cls, name):
        name_map = {
            "Single player": cls.SINGLE_PLAYER,
            "Local multiplayer": cls.LOCAL_MULTI,
            "Online game": cls.ONLINE
        }
        return name_map.get(name, cls.SINGLE_PLAYER)

    def to_string(self):
        string_map = {
            GameType.SINGLE_PLAYER: "Single player",
            GameType.LOCAL_MULTI: "Local multiplayer",
            GameType.ONLINE: "Online game"
        }
        return string_map.get(self, "Single player")


class Cell:
    def __init__(self, x: int, y: int, cell_type: CellType, shape: CellShape = CellShape.CIRCLE,
                 evolution: EvolutionLevel = EvolutionLevel.LEVEL_1):
        self.x = x
        self.y = y
        self.cell_type = cell_type
        self.shape = shape
        self.evolution = evolution
        self.points = 20 if cell_type != CellType.EMPTY else 0
        self.required_points = 6
        self.points_to_capture = 0
        self.enemy_points_to_capture = 0
        self.last_growth_time = pygame.time.get_ticks()
        self.outgoing_bridges = []
        self.incoming_bridges = []
        self.pulse_value = random.random() * math.pi * 2
        self.rotation = 0

    def get_color(self):
        if self.cell_type == CellType.PLAYER:
            return PLAYER_COLOR
        elif self.cell_type == CellType.ENEMY:
            return ENEMY_COLOR
        else:
            return EMPTY_COLOR

    def get_glow_color(self):
        base_color = self.get_color()
        r = min(255, base_color[0] + 100)
        g = min(255, base_color[1] + 100)
        b = min(255, base_color[2] + 100)
        return (r, g, b)

    def update(self, current_time):
        if self.cell_type != CellType.EMPTY:
            if current_time - self.last_growth_time >= POINT_GROWTH_INTERVAL_new:
                self.points += 1
                self.last_growth_time = current_time

        self.pulse_value = (self.pulse_value + 0.05) % (math.pi * 2)
        self.rotation = (self.rotation + 0.5) % 360

    def draw(self, screen, game):
        pulse = (math.sin(self.pulse_value) + 1) / 2

        glow_radius = CELL_RADIUS + 5 + pulse * 3
        glow_color = self.get_glow_color()
        glow_alpha = 150 + int(pulse * 60)

        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)

        pygame.draw.circle(glow_surface, (*glow_color, glow_alpha),
                           (glow_radius, glow_radius), glow_radius)

        screen.blit(glow_surface, (self.x - glow_radius, self.y - glow_radius))

        if self.shape == CellShape.CIRCLE:
            pygame.draw.circle(screen, self.get_color(), (self.x, self.y), CELL_RADIUS)

            highlight_radius = CELL_RADIUS * 0.7
            highlight_color = (min(255, self.get_color()[0] + 50),
                               min(255, self.get_color()[1] + 50),
                               min(255, self.get_color()[2] + 50))
            pygame.draw.circle(screen, highlight_color,
                               (self.x - CELL_RADIUS * 0.2, self.y - CELL_RADIUS * 0.2),
                               highlight_radius)

            pygame.draw.circle(screen, BLACK, (self.x, self.y), CELL_RADIUS, 2)

        elif self.shape == CellShape.TRIANGLE:
            angle_rad = math.radians(self.rotation)

            points = []
            for i in range(3):
                angle = angle_rad + i * 2 * math.pi / 3
                px = self.x + math.sin(angle) * CELL_RADIUS
                py = self.y + math.cos(angle) * CELL_RADIUS
                points.append((px, py))

            pygame.draw.polygon(screen, self.get_color(), points)

            inner_points = []
            for i in range(3):
                angle = angle_rad + i * 2 * math.pi / 3
                px = self.x + math.sin(angle) * CELL_RADIUS * 0.7
                py = self.y + math.cos(angle) * CELL_RADIUS * 0.7
                inner_points.append((px, py))

            highlight_color = (min(255, self.get_color()[0] + 50),
                               min(255, self.get_color()[1] + 50),
                               min(255, self.get_color()[2] + 50))
            pygame.draw.polygon(screen, highlight_color, inner_points)

            pygame.draw.polygon(screen, BLACK, points, 2)

        elif self.shape == CellShape.RECTANGLE:
            rect_surface = pygame.Surface((CELL_RADIUS * 2, CELL_RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.rect(rect_surface, self.get_color(),
                             (0, 0, CELL_RADIUS * 2, CELL_RADIUS * 2))

            highlight_color = (min(255, self.get_color()[0] + 50),
                               min(255, self.get_color()[1] + 50),
                               min(255, self.get_color()[2] + 50))
            pygame.draw.rect(rect_surface, highlight_color,
                             (CELL_RADIUS * 0.4, CELL_RADIUS * 0.4,
                              CELL_RADIUS * 1.2, CELL_RADIUS * 1.2))

            pygame.draw.rect(rect_surface, BLACK, (0, 0, CELL_RADIUS * 2, CELL_RADIUS * 2), 2)

            if self.cell_type != CellType.EMPTY:
                rotated = pygame.transform.rotate(rect_surface, self.rotation / 4)
                rotated_rect = rotated.get_rect(center=(self.x, self.y))
                screen.blit(rotated, rotated_rect)
            else:
                rect = pygame.Rect(self.x - CELL_RADIUS, self.y - CELL_RADIUS,
                                   CELL_RADIUS * 2, CELL_RADIUS * 2)
                pygame.draw.rect(screen, self.get_color(), rect)
                pygame.draw.rect(screen, BLACK, rect, 2)

        font = pygame.font.SysFont('Arial', 14)

        if self.cell_type == CellType.EMPTY:
            domination_ratio = 0
            total_points = self.points_to_capture + self.enemy_points_to_capture

            if total_points > 0:
                domination_ratio = self.points_to_capture / total_points

                base_gradient_radius = CELL_RADIUS + 5
                for i in range(3):
                    gradient_radius = base_gradient_radius + i * 3
                    thickness = 3 - i * 0.5

                    pulse = (math.sin(self.pulse_value + i) + 1) / 4 + 0.9  # 0.9-1.15 range
                    gradient_radius *= pulse

                    if domination_ratio > 0:
                        start_angle = 0
                        end_angle = domination_ratio * 2 * math.pi
                        player_color = (
                            PLAYER_COLOR[0],
                            min(255, PLAYER_COLOR[1] + i * 20),
                            min(255, PLAYER_COLOR[2] + i * 10)
                        )
                        pygame.draw.arc(screen, player_color,
                                        (self.x - gradient_radius, self.y - gradient_radius,
                                         gradient_radius * 2, gradient_radius * 2),
                                        start_angle, end_angle, int(thickness))

                    if domination_ratio < 1:
                        start_angle = domination_ratio * 2 * math.pi
                        end_angle = 2 * math.pi
                        enemy_color = (
                            min(255, ENEMY_COLOR[0] + i * 10),
                            ENEMY_COLOR[1],
                            ENEMY_COLOR[2]
                        )
                        pygame.draw.arc(screen, enemy_color,
                                        (self.x - gradient_radius, self.y - gradient_radius,
                                         gradient_radius * 2, gradient_radius * 2),
                                        start_angle, end_angle, int(thickness))
            if game.turn_based_mode:
                is_active_player = ((self.cell_type == CellType.PLAYER and game.current_player_turn) or
                                    (self.cell_type == CellType.ENEMY and not game.current_player_turn))

                if is_active_player:
                    highlight_pulse = (math.sin(game.current_time * 0.01) + 1) / 2
                    highlight_radius = CELL_RADIUS + 12 + highlight_pulse * 4
                    highlight_color = PLAYER_COLOR if self.cell_type == CellType.PLAYER else ENEMY_COLOR
                    highlight_alpha = 100 + int(highlight_pulse * 100)

                    highlight_surface = pygame.Surface((highlight_radius * 2, highlight_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(highlight_surface, (*highlight_color, highlight_alpha),
                                       (highlight_radius, highlight_radius), highlight_radius, 2)
                    screen.blit(highlight_surface, (self.x - highlight_radius, self.y - highlight_radius))

            progress_text = f"{self.points_to_capture - self.enemy_points_to_capture}/{self.required_points}"
            text_surface = font.render(progress_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(self.x, self.y))
            screen.blit(text_surface, text_rect)
        else:
            points_text = str(self.points)
            text_surface = font.render(points_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(self.x, self.y))
            screen.blit(text_surface, text_rect)

            evo_text = f"E{self.evolution.value}"
            if self.evolution.value == 1:
                evo_color = (220, 220, 220)
            elif self.evolution.value == 2:
                evo_color = (220, 220, 100)
            else:
                evo_color = (220, 150, 50)
            evo_surface = font.render(evo_text, True, evo_color)
            evo_rect = evo_surface.get_rect(center=(self.x, self.y + CELL_RADIUS + 10))
            screen.blit(evo_surface, evo_rect)
        supporting_cells = game.count_supporting_cells(self)
        if supporting_cells > 0:
            pulse = (math.sin(self.pulse_value * 2) + 1) / 2
            support_radius = CELL_RADIUS + 8 + pulse * 5
            support_alpha = 100 + int(pulse * 60)

            if self.cell_type == CellType.PLAYER:
                support_color = (100, 150, 255, support_alpha)
            else:
                support_color = (255, 100, 100, support_alpha)

            support_surface = pygame.Surface((support_radius * 2, support_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(support_surface, support_color,
                               (support_radius, support_radius), support_radius, 3)
            screen.blit(support_surface, (self.x - support_radius, self.y - support_radius))

            for i in range(min(3, supporting_cells)):
                angle = self.pulse_value + (i * math.pi * 2 / 3)
                icon_x = self.x + math.cos(angle) * (CELL_RADIUS + 15)
                icon_y = self.y + math.sin(angle) * (CELL_RADIUS + 15)

                icon_size = 5
                pygame.draw.circle(screen, support_color[:3], (int(icon_x), int(icon_y)), icon_size)

    def contains_point(self, pos_x, pos_y):
        distance = math.sqrt((pos_x - self.x) ** 2 + (pos_y - self.y) ** 2)
        return distance <= CELL_RADIUS

    def try_capture(self, points_gained, is_player):
        if self.cell_type != CellType.EMPTY:
            return False

        original_type = self.cell_type

        if is_player:
            self.points_to_capture += points_gained
        else:
            self.enemy_points_to_capture += points_gained

        net_points = self.points_to_capture - self.enemy_points_to_capture

        if abs(net_points) >= self.required_points:
            if net_points > 0:
                self.cell_type = CellType.PLAYER
                self.points = 20
                logger.info(f"Player captured cell at ({self.x}, {self.y})")
            else:
                self.cell_type = CellType.ENEMY
                self.points = 20
                logger.info(f"Enemy captured cell at ({self.x}, {self.y})")

            self.points_to_capture = 0
            self.enemy_points_to_capture = 0
            return True

        if original_type == CellType.EMPTY and self.cell_type != CellType.EMPTY:
            game = self.game
            if not game.playback_active:
                game.game_recorder.record_event("CELL_CAPTURED", {
                    "cellId": game.game_recorder.cell_id_map.get(Cell, -1),
                    "newType": self.cell_type.name,
                    "points": self.points,
                    "isPlayer": is_player
                })

        return False

    def get_attack_multiplier(self):
        if self.shape == CellShape.TRIANGLE:
            return 2
        elif self.shape == CellShape.RECTANGLE:
            return 3
        else:
            return 1


class Ball:
    def __init__(self, source_cell, target_cell, is_player):
        self.source_cell = source_cell

        self.source_x = source_cell.x
        self.source_y = source_cell.y
        self.target_x = target_cell.x
        self.target_y = target_cell.y

        self.is_player = is_player
        self.color = PLAYER_COLOR if is_player else ENEMY_COLOR

        dx = self.target_x - self.source_x
        dy = self.target_y - self.source_y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        self.direction_x = dx / distance if distance > 0 else 0
        self.direction_y = dy / distance if distance > 0 else 0

        offset = CELL_RADIUS + 5
        self.x = self.source_x + self.direction_x * offset
        self.y = self.source_y + self.direction_y * offset

        self.speed = BALL_SPEED
        self.trail = []
        self.age = 0

        self.is_support_ball = False
        self.attack_value = source_cell.get_attack_multiplier()

    def update(self):
        self.trail.append((self.x, self.y))

        if len(self.trail) > 10:
            self.trail.pop(0)

        self.x += self.direction_x * self.speed
        self.y += self.direction_y * self.speed
        self.age += 1

    def draw(self, screen):
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)) * 0.6)
            trail_radius = BALL_RADIUS * (i / len(self.trail)) * 0.8

            trail_surface = pygame.Surface((int(trail_radius * 2), int(trail_radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, (*self.color, alpha),
                               (int(trail_radius), int(trail_radius)), int(trail_radius))

            screen.blit(trail_surface,
                        (int(pos[0] - trail_radius), int(pos[1] - trail_radius)))

        pulse = (math.sin(self.age * 0.2) + 1) / 4 + 0.75  # 0.75-1.25 range

        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)),
                           int(BALL_RADIUS * pulse))

        highlight_color = (min(255, self.color[0] + 100),
                           min(255, self.color[1] + 100),
                           min(255, self.color[2] + 100))
        highlight_pos = (int(self.x - BALL_RADIUS * 0.3), int(self.y - BALL_RADIUS * 0.3))
        highlight_radius = BALL_RADIUS * 0.4 * pulse
        pygame.draw.circle(screen, highlight_color, highlight_pos, int(highlight_radius))

    def reached_target(self, target_cell):
        distance = math.sqrt((self.x - target_cell.x) ** 2 + (self.y - target_cell.y) ** 2)
        return distance <= CELL_RADIUS

    def check_collision(self, other_ball):
        if other_ball.is_player == self.is_player:
            return False

        distance = math.sqrt((self.x - other_ball.x) ** 2 + (self.y - other_ball.y) ** 2)
        return distance <= BALL_RADIUS * 2


class Bridge:
    def __init__(self, source_cell, target_cell):
        self.source_cell = source_cell
        self.target_cell = target_cell
        self.direction = BridgeDirection.ONE_WAY
        self.has_reverse = False
        self.particles = []
        self.animation_offset = random.random() * math.pi * 2

    def update(self):
        self.animation_offset = (self.animation_offset + 0.03) % (math.pi * 2)

        if random.random() < 0.3:
            self.add_particle()

        for particle in self.particles:
            particle['progress'] += 0.01

        self.particles = [p for p in self.particles if p['progress'] <= 1.0]

    def add_particle(self):
        is_forward = True
        if self.direction == BridgeDirection.TWO_WAY and random.random() < 0.5:
            is_forward = False

        if is_forward:
            if self.source_cell.cell_type == CellType.PLAYER:
                color = PLAYER_COLOR
            elif self.source_cell.cell_type == CellType.ENEMY:
                color = ENEMY_COLOR
            else:
                color = WHITE
        else:
            if self.target_cell.cell_type == CellType.PLAYER:
                color = PLAYER_COLOR
            elif self.target_cell.cell_type == CellType.ENEMY:
                color = ENEMY_COLOR
            else:
                color = WHITE

        r_offset = random.randint(-20, 20)
        g_offset = random.randint(-20, 20)
        b_offset = random.randint(-20, 20)

        color = (
            max(0, min(255, color[0] + r_offset)),
            max(0, min(255, color[1] + g_offset)),
            max(0, min(255, color[2] + b_offset))
        )

        particle = {
            'progress': 0.0,  # 0 to 1 along the bridge
            'is_forward': is_forward,
            'color': color,
            'size': random.uniform(1.5, 3.0)
        }

        self.particles.append(particle)

    def draw(self, screen):
        source_x, source_y = self.source_cell.x, self.source_cell.y
        target_x, target_y = self.target_cell.x, self.target_cell.y

        dx = target_x - source_x
        dy = target_y - source_y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance > 0:
            perp_x, perp_y = -dy / distance, dx / distance
        else:
            perp_x, perp_y = 0, 0

        num_segments = max(10, int(distance / 20))
        points = []

        for i in range(num_segments + 1):
            t = i / num_segments
            pos_x = source_x + dx * t
            pos_y = source_y + dy * t

            wave_amplitude = 2.0
            wave = math.sin(t * 10 + self.animation_offset) * wave_amplitude
            pos_x += perp_x * wave
            pos_y += perp_y * wave

            points.append((pos_x, pos_y))

        if len(points) >= 2:
            for i in range(len(points) - 1):
                t = i / (len(points) - 1)
                if self.source_cell.cell_type != CellType.EMPTY and self.target_cell.cell_type != CellType.EMPTY:
                    if self.source_cell.cell_type == self.target_cell.cell_type:
                        color = self.source_cell.get_color()
                    else:
                        src_color = self.source_cell.get_color()
                        tgt_color = self.target_cell.get_color()
                        color = (
                            int(src_color[0] * (1 - t) + tgt_color[0] * t),
                            int(src_color[1] * (1 - t) + tgt_color[1] * t),
                            int(src_color[2] * (1 - t) + tgt_color[2] * t)
                        )
                else:
                    color = WHITE

                pygame.draw.line(screen, color, points[i], points[i + 1], BRIDGE_WIDTH)

        for particle in self.particles:
            t = particle['progress']
            if not particle['is_forward']:
                t = 1.0 - t

            pos_x = source_x + dx * t
            pos_y = source_y + dy * t

            wave_amplitude = 2.0
            wave = math.sin(t * 10 + self.animation_offset) * wave_amplitude
            pos_x += perp_x * wave
            pos_y += perp_y * wave

            glow_surface = pygame.Surface((int(particle['size'] * 4), int(particle['size'] * 4)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*particle['color'], 150),
                               (int(particle['size'] * 2), int(particle['size'] * 2)),
                               int(particle['size'] * 2))
            screen.blit(glow_surface,
                        (int(pos_x - particle['size'] * 2), int(pos_y - particle['size'] * 2)))

            pygame.draw.circle(screen, particle['color'],
                               (int(pos_x), int(pos_y)),
                               int(particle['size']))

        if self.direction == BridgeDirection.ONE_WAY:
            self.draw_arrow(screen, (source_x, source_y), (target_x, target_y), WHITE)
        else:
            midpoint_x = (source_x + target_x) / 2
            midpoint_y = (source_y + target_y) / 2

            self.draw_arrow(screen, (source_x, source_y), (midpoint_x, midpoint_y), WHITE)
            self.draw_arrow(screen, (target_x, target_y), (midpoint_x, midpoint_y), WHITE)

    def draw_arrow(self, screen, start, end, color):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance == 0:
            return

        dx, dy = dx / distance, dy / distance

        arrow_pos_x = start[0] + dx * distance * 0.8
        arrow_pos_y = start[1] + dy * distance * 0.8

        perpendicular_x = -dy
        perpendicular_y = dx

        arrow_head_size = 8
        point1 = (arrow_pos_x + perpendicular_x * arrow_head_size - dx * arrow_head_size,
                  arrow_pos_y + perpendicular_y * arrow_head_size - dy * arrow_head_size)
        point2 = (arrow_pos_x - perpendicular_x * arrow_head_size - dx * arrow_head_size,
                  arrow_pos_y - perpendicular_y * arrow_head_size - dy * arrow_head_size)

        pygame.draw.polygon(screen, color, [(arrow_pos_x, arrow_pos_y), point1, point2])


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("War of Cells Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 14)

        self.cells = []
        self.bridges = []
        self.balls = []
        self.effects = []

        self.selected_cell = None
        self.last_ball_spawn_time = {}

        self.control_enemy = False
        self.show_context_menu = False
        self.context_menu_cell = None
        self.context_menu_options = ["Remove All Bridges"]

        self.turn_based_mode = False
        self.current_player_turn = True
        self.turn_time_remaining = 10.0
        self.turn_timer_active = False
        self.move_made_this_turn = False
        self.turn_status_message = ""

        self.running = True
        self.game_started = False
        self.game_over_state = False

        self.current_level = "level1"
        self.points = 0
        self.time_taken = 0
        self.start_time = 0

        self.ai_enabled = True
        self.ai_difficulty = "Medium"
        self.last_ai_move_time = 0
        self.ai_move_cooldown = 1000
        self.suggestions = []
        self.show_suggestions = False
        self.last_suggestion_time = 0

        self.game_type = GameType.SINGLE_PLAYER

        self.network_config = {
            "ip": "127.0.0.1",
            "port": 12345
        }

        self.game_recorder = GameRecorder(self)
        self.game_playback = None
        self.playback_active = False
        self.playback_controls_visible = False


        #user's move and enemy's move - depending on who is playing (like rx/tx connections - what is rx for another is tx)
        self.my_move = None
        self.enemy_move = None

        self.cell_id_map_reverse = {}  # Used for network event handling

        self.game_speed = 1




        self.game_data = load_game_data("game_data.json")
        self.show_first_menu()

        #self.show_menu()

        # load_level(self, self.current_level)

        # self.initialize_board()

    def show_first_menu(self):
        menu = MenuWindow()
        if menu.config:
            self.game_type = GameType.from_string(menu.config["mode"])

            if self.game_type == GameType.SINGLE_PLAYER:
                self.ai_enabled = True
                self.control_enemy = False
            elif self.game_type == GameType.LOCAL_MULTI:
                self.ai_enabled = False
                self.control_enemy = False
                self.turn_based_mode = True
            elif self.game_type == GameType.ONLINE:
                self.ai_enabled = False
                self.network_config["ip"] = menu.config.get("ip", "localhost")
                self.network_config["port"] = int(menu.config.get("port", 5555))
                logger.info(f"Network configuration: {self.network_config}")

            logger.info(f"Selected game mode: {self.game_type.to_string()}")

            self.show_menu()
        else:
            self.running = False

    def show_menu(self):
        if create_menu(self):
            self.start_game()
        else:
            self.running = False

    def start_game(self):
        saved_games = check_saved_games_for_level(self.current_level)
        if saved_games:
            if self.show_continue_dialog(saved_games[0]):
                if self.load_saved_game(saved_games[0]):
                    self.game_started = True
                    self.game_over_state = False
                    logger.info(f"Continuing saved game for level: {self.current_level}")
                    return
        
        # Initialize networking BEFORE loading level if online mode
        if self.game_type == GameType.ONLINE:
            logger.info("Initializing network connection...")
            
            # First make sure the GameNetworkClient class is imported
            if not hasattr(self, 'network_client') or self.network_client is None:
                try:
                    self.network_client = GameNetworkClient(self)
                    logger.info("Network client created")
                except Exception as e:
                    logger.error(f"Failed to create network client: {e}")
                    self.game_type = GameType.LOCAL_MULTI  # Fallback
            
            # Then attempt connection
            try:
                success = self.network_client.connect(
                    self.network_config["ip"],
                    self.network_config["port"]
                )
                
                if success:
                    logger.info("Successfully connected to game server")
                else:
                    logger.error("Failed to connect to game server - falling back to local mode")
                    self.game_type = GameType.LOCAL_MULTI
            except Exception as e:
                logger.error(f"Error during connection: {e}")
                self.game_type = GameType.LOCAL_MULTI
        
        # Now load the level
        load_level(self, self.current_level)

        self.game_started = True
        self.game_over_state = False
        self.points = 0
        self.time_taken = 0
        self.start_time = pygame.time.get_ticks() / 1000  # start time, seconds

        logger.info(f"Starting game with level: {self.current_level}")

        if not self.playback_active:
            self.game_recorder.start_recording()

    def initialize_board(self):
        player_cell = Cell(200, 300, CellType.PLAYER, CellShape.CIRCLE, EvolutionLevel.LEVEL_1)
        self.cells.append(player_cell)

        enemy_cell = Cell(600, 300, CellType.ENEMY, CellShape.CIRCLE, EvolutionLevel.LEVEL_1)
        self.cells.append(enemy_cell)

    def switch_turns(self):
        self.current_player_turn = not self.current_player_turn
        self.turn_time_remaining = 10.0
        self.move_made_this_turn = False

        if self.current_player_turn:
            self.turn_status_message = "Your Turn"
            self.control_enemy = False
        else:
            self.turn_status_message = "Enemy Turn"
            if self.ai_enabled:
                self.control_enemy = False
            else:
                self.control_enemy = True

        logger.info(f"Turn switched to {'Player' if self.current_player_turn else 'Enemy'}")

        if not self.playback_active:
            self.game_recorder.record_event("TURN_SWITCH", {
                "isPlayerTurn": self.current_player_turn
            })

    def toggle_turn_based_mode(self):
        self.turn_based_mode = not self.turn_based_mode

        if self.turn_based_mode:
            self.current_player_turn = True
            self.turn_time_remaining = 10.0
            self.turn_timer_active = True
            self.move_made_this_turn = False
            self.turn_status_message = "Your Turn"
            self.control_enemy = False
            logger.info("Turn-based mode activated")
        else:
            self.turn_timer_active = False
            self.turn_status_message = ""
            logger.info("Real-time mode activated")

    def toggle_ai(self):
        self.ai_enabled = not self.ai_enabled
        if self.ai_enabled:
            logger.info(f"AI enabled with {self.ai_difficulty} difficulty")
        else:
            logger.info("AI disabled")

    def cycle_ai_difficulty(self):
        difficulties = ["Easy", "Medium", "Hard"]
        current_index = difficulties.index(self.ai_difficulty)
        next_index = (current_index + 1) % len(difficulties)
        self.ai_difficulty = difficulties[next_index]
        logger.info(f"AI difficulty set to {self.ai_difficulty}")

        if self.ai_difficulty == "Easy":
            self.ai_move_cooldown = 1500
        elif self.ai_difficulty == "Medium":
            self.ai_move_cooldown = 1000
        else:  # Hard
            self.ai_move_cooldown = 500

    def create_collision_effect(self, x, y):
        num_particles = random.randint(8, 12)
        effect = {
            'type': 'collision',
            'x': x,
            'y': y,
            'particles': [],
            'age': 0,
            'lifetime': 30  # frames
        }

        for _ in range(num_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)
            size = random.uniform(2, 4)
            color = (
                random.randint(200, 255),
                random.randint(200, 255),
                random.randint(100, 200)
            )

            particle = {
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'size': size,
                'color': color
            }

            effect['particles'].append(particle)

        self.effects.append(effect)

    def create_impact_effect(self, x, y, is_player):
        color = PLAYER_COLOR if is_player else ENEMY_COLOR

        color = (
            min(255, color[0] + 50),
            min(255, color[1] + 50),
            min(255, color[2] + 50)
        )

        effect = {
            'type': 'impact',
            'x': x,
            'y': y,
            'color': color,
            'age': 0,
            'lifetime': 20,
            'size': 1.0
        }

        self.effects.append(effect)

    def update_effects(self):
        effects_to_remove = []

        for effect in self.effects:
            effect['age'] += 1

            if effect['age'] >= effect['lifetime']:
                effects_to_remove.append(effect)
                continue

            if effect['type'] == 'collision':
                for particle in effect['particles']:
                    particle['dx'] *= 0.95
                    particle['dy'] *= 0.95
                    particle['size'] *= 0.9

            elif effect['type'] == 'impact':
                progress = effect['age'] / effect['lifetime']
                if progress < 0.3:
                    effect['size'] = 1.0 + progress * 5  # to 2.5x
                else:
                    effect['size'] = 2.5 - (progress - 0.3) * 3  # shrink to 0

        for effect in effects_to_remove:
            if effect in self.effects:
                self.effects.remove(effect)

    def update_evolution_based_on_points(self, cell):
        old_evolution = cell.evolution.value

        if cell.points < 15:
            new_evolution = EvolutionLevel.LEVEL_1
        elif cell.points < 35:
            new_evolution = EvolutionLevel.LEVEL_2
        else:
            new_evolution = EvolutionLevel.LEVEL_3

        if new_evolution.value != old_evolution:
            cell.evolution = new_evolution
            logger.info(f"Cell at ({cell.x}, {cell.y}) evolved to level {new_evolution.value}")

            if cell.cell_type == CellType.PLAYER:
                self.create_impact_effect(cell.x, cell.y, True)
            else:
                self.create_impact_effect(cell.x, cell.y, False)
        """        
        #dont want to record evolution changes, as they dont have too much sense, as they have constant logic, and when replaying the game would be done automatically
        if new_evolution.value != old_evolution and not self.playback_active:
            self.game_recorder.record_event("CELL_EVOLVED", {
                "cellId": self.game_recorder.cell_id_map.get(cell, -1),
                "oldLevel": old_evolution,
                "newLevel": new_evolution.value
            }) """

    def next_level(self):
        if not self.game_data:
            return False

        if self.current_level.startswith("level"):
            level_num = int(self.current_level[5:])
            next_level_name = f"level{level_num + 1}"

            if next_level_name in self.game_data.get("levels", {}):
                self.current_level = next_level_name
                return load_level(self, self.current_level)

        return False

    def draw_effects(self, screen):
        for effect in self.effects:
            if effect['type'] == 'collision':
                for particle in effect['particles']:
                    px = effect['x'] + particle['dx'] * effect['age']
                    py = effect['y'] + particle['dy'] * effect['age']

                    alpha = int(255 * (1 - effect['age'] / effect['lifetime']))

                    particle_surface = pygame.Surface((int(particle['size'] * 2), int(particle['size'] * 2)),
                                                      pygame.SRCALPHA)
                    pygame.draw.circle(particle_surface, (*particle['color'], alpha),
                                       (int(particle['size']), int(particle['size'])),
                                       int(particle['size']))
                    screen.blit(particle_surface, (int(px - particle['size']), int(py - particle['size'])))

            elif effect['type'] == 'impact':
                alpha = int(255 * (1 - effect['age'] / effect['lifetime']))
                size = CELL_RADIUS * effect['size']

                ring_surface = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(ring_surface, (*effect['color'], alpha),
                                   (int(size), int(size)), int(size), max(1, int(size / 10)))
                screen.blit(ring_surface, (int(effect['x'] - size), int(effect['y'] - size)))

            elif effect['type'] == 'support':
                alpha = int(255 * (1 - effect['age'] / effect['lifetime']))
                size = CELL_RADIUS * 0.3 * (1 + effect['age'] / effect['lifetime'])

                plus_surface = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)

                pygame.draw.rect(plus_surface, (*effect['color'], alpha),
                                 (0, int(size * 0.8), int(size * 2), int(size * 0.4)))

                pygame.draw.rect(plus_surface, (*effect['color'], alpha),
                                 (int(size * 0.8), 0, int(size * 0.4), int(size * 2)))

                screen.blit(plus_surface, (int(effect['x'] - size), int(effect['y'] - size)))

    def draw_background_gradient(self):
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

    def calculate_distance(self, cell1, cell2):
        return math.sqrt((cell1.x - cell2.x) ** 2 + (cell1.y - cell2.y) ** 2)

    def get_bridge_at_position(self, x, y, threshold=10):
        for bridge in self.bridges:
            start_x, start_y = bridge.source_cell.x, bridge.source_cell.y
            end_x, end_y = bridge.target_cell.x, bridge.target_cell.y

            line_length = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
            if line_length == 0:
                continue

            u = ((x - start_x) * (end_x - start_x) + (y - start_y) * (end_y - start_y)) / (line_length ** 2)

            if 0 <= u <= 1:
                closest_x = start_x + u * (end_x - start_x)
                closest_y = start_y + u * (end_y - start_y)

                dist = math.sqrt((x - closest_x) ** 2 + (y - closest_y) ** 2)
                if dist <= threshold:
                    dist_to_start = math.sqrt((x - start_x) ** 2 + (y - start_y) ** 2)
                    dist_to_end = math.sqrt((x - end_x) ** 2 + (y - end_y) ** 2)

                    return bridge, dist_to_start < dist_to_end

        return None, False

    def count_supporting_cells(self, cell):
        supporting_cells = 0

        for bridge in self.bridges:
            if bridge.target_cell == cell:
                if bridge.source_cell.cell_type == cell.cell_type:
                    supporting_cells += 1

        return supporting_cells

    def get_support_bonus(self, cell):
        supporting_cells = self.count_supporting_cells(cell)

        # base multiplier is 1.0 (no bonus)
        #each supporting cell adds 0.2 to the multiplier, up to a maximum of 2.0
        multiplier = min(2.0, 1.0 + (supporting_cells * 0.2))

        return multiplier

    def create_support_effect(self, x, y, is_player):
        effect = {
            'type': 'support',
            'x': x,
            'y': y,
            'color': PLAYER_COLOR if is_player else ENEMY_COLOR,
            'age': 0,
            'lifetime': 15,
            'size': 1.0
        }

        self.effects.append(effect)

    def remove_bridge(self, bridge):
        for other_bridge in self.bridges:
            if other_bridge.source_cell == bridge.target_cell and other_bridge.target_cell == bridge.source_cell:
                other_bridge.direction = BridgeDirection.ONE_WAY
                other_bridge.has_reverse = False
                logger.info("Reverse bridge changed to one-way")

        if bridge in bridge.source_cell.outgoing_bridges:
            bridge.source_cell.outgoing_bridges.remove(bridge)

        if bridge in bridge.target_cell.incoming_bridges:
            bridge.target_cell.incoming_bridges.remove(bridge)

        if bridge in self.bridges:
            self.bridges.remove(bridge)

        if not self.playback_active:
            self.game_recorder.record_event("BRIDGE_REMOVED", {
                "sourceId": self.game_recorder.cell_id_map.get(bridge.source_cell, -1),
                "targetId": self.game_recorder.cell_id_map.get(bridge.target_cell, -1)
            })

    def run(self):
        running = True
        creating_bridge = False
        bridge_start_cell = None

        background = self.draw_background_gradient()

        #recalculate all speeds and frequences of balls sending and cell points updating
        #params - game speed for playback
        #dont forget about all rotation speeds

        if self.playback_active and self.game_playback:
            self.turn_time_remaining = self.turn_time_remaining/self.game_playback.playback_speed
            Ball.speed = BALL_SPEED*self.game_playback.playback_speed
            POINT_GROWTH_INTERVAL_new = POINT_GROWTH_INTERVAL/self.game_playback.playback_speed

        playback_events = [] 
        network_events = [] 

        while running:
            # Make sure to call tick at beginning so event handling works properly
            self.clock.tick(FPS)

            playback_events = [] 
            network_events = []  
            
            if not self.game_started:
                self.show_menu()
                continue
            if self.game_type == GameType.ONLINE:
                # Get network events
                network_events = self.get_network_events()
            for event in playback_events + network_events:
                self.apply_event(event)
                
            #want to create the same logic for playback and online game, so lets remove that playback part, and integrate it in the main game code
            """if self.playback_active and self.game_playback:
                self.game_playback.update()

                self.screen.blit(background, (0, 0))

                for bridge in self.bridges:
                    bridge.draw(self.screen)

                for cell in self.cells:
                    cell.draw(self.screen, self)

                for ball in self.balls:
                    ball.draw(self.screen)

                self.draw_playback_controls()

            else:"""

            if self.playback_active and self.game_playback:
                self.game_playback.update()  
                # Assuming game_playback.update() processes events internally
                # If it doesn't, add code to get pending events:
                if hasattr(self.game_playback, 'get_pending_events'):
                    playback_events = self.game_playback.get_pending_events()
            
            # Process events from network if online
            if self.game_type == GameType.ONLINE and hasattr(self, 'network_client') and self.network_client:
                # Get network events
                try:
                    network_events = self.get_network_events() 
                except Exception as e:
                    logger.error(f"Error getting network events: {e}")
                    network_events = []

            # Apply events from playback or network
            try:
                for event in playback_events + network_events:
                    self.apply_event(event)
            except Exception as e:
                logger.error(f"Error applying events: {e}")

            # Process events from playback if active
            playback_events = []
            if self.playback_active and self.game_playback:
                self.game_playback.update()  
                # Assuming game_playback.update() processes events internally
                # If it doesn't, add code to get pending events:
                playback_events = self.game_playback.get_pending_events()
            
            # Process events from network if online
            network_events = []
            if self.game_type == GameType.ONLINE:
                # Get network events
                network_events = self.get_network_events() 

            # Apply events from playback or network
            for event in playback_events + network_events:
                self.apply_event(event)

            if not self.game_over_state:
                current_time_sec = pygame.time.get_ticks() / 1000
                self.time_taken = current_time_sec - self.start_time

            current_time = pygame.time.get_ticks()
            if self.ai_enabled and not self.control_enemy:
                if self.turn_based_mode:
                    if not self.current_player_turn and current_time - self.last_ai_move_time >= self.ai_move_cooldown:
                        execute_ai_move(self, is_suggestion=False)
                        self.last_ai_move_time = current_time
                else:
                    if current_time - self.last_ai_move_time >= self.ai_move_cooldown:
                        execute_ai_move(self, is_suggestion=False)
                        self.last_ai_move_time = current_time

            if self.show_suggestions:
                if (self.turn_based_mode and self.current_player_turn) or (not self.control_enemy):
                    if not self.suggestions or current_time - self.last_suggestion_time >= 5000:
                        self.suggestions = suggest_moves(self, for_player=True)
                        self.last_suggestion_time = current_time

                    draw_suggestions(self, self.screen)

            # Handle events - important to put this earlier in the loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif self.playback_active and self.game_playback:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            if self.game_playback.is_playing:
                                self.game_playback.pause()
                            else:
                                self.game_playback.resume()
                        elif event.key == pygame.K_RIGHT:
                            self.game_playback.set_speed(self.game_playback.playback_speed + 0.25)
                        elif event.key == pygame.K_LEFT:
                            self.game_playback.set_speed(self.game_playback.playback_speed - 0.25)
                        elif event.key == pygame.K_ESCAPE:
                            self.playback_active = False
                            self.game_playback = None
                            self.game_started = False
                            continue

                elif event.type == pygame.KEYDOWN and not self.playback_active:
                    # Handle regular keypresses when not in playback mode
                    if event.key == pygame.K_SPACE and (self.game_type == GameType.LOCAL_MULTI or self.game_type == GameType.ONLINE):
                        self.control_enemy = not self.control_enemy
                        if self.control_enemy:
                            logger.info("Now controlling enemy (red) cells")
                            for cell in self.cells:
                                if cell.cell_type == CellType.ENEMY:
                                    self.create_impact_effect(cell.x, cell.y, False)
                        else:
                            logger.info("Now controlling player (blue) cells")
                            for cell in self.cells:
                                if cell.cell_type == CellType.PLAYER:
                                    self.create_impact_effect(cell.x, cell.y, True)
                        
                        # Record this action if recording
                        if hasattr(self, 'game_recorder') and self.game_recorder and self.game_recorder.recording:
                            self.game_recorder.record_event("CONTROL_SWITCH", {
                                "control_enemy": self.control_enemy
                            })
                        
                        # Notify network if in online mode
                        if self.game_type == GameType.ONLINE and hasattr(self, 'send_network_event'):
                            self.send_network_event("CONTROL_SWITCH", {
                                "control_enemy": self.control_enemy
                            })

                    elif event.key == pygame.K_t:
                        self.toggle_turn_based_mode()
                        # Record this action if recording
                        if hasattr(self, 'game_recorder') and self.game_recorder and self.game_recorder.recording:
                            self.game_recorder.record_event("TURN_BASED_TOGGLE", {
                                "turn_based": self.turn_based_mode
                            })

                    #commented that part, as ai is only available for single player, and makes no sense to other, and if it is single player it automatically playes against ai
                    # elif event.key == pygame.K_a:
                        # self.toggle_ai()

                    #same for game difficulty - if I want to save it in game history, it must be chosen at the beginning
                    #elif event.key == pygame.K_d:
                        #self.cycle_ai_difficulty()

                    #help is currently available only in single player mode, maybe later add it to others
                    elif event.key == pygame.K_h and self.game_type==GameType.SINGLE_PLAYER and not self.playback_active:
                        self.show_suggestions = not self.show_suggestions
                        if self.show_suggestions:
                            logger.info("Move suggestions enabled - generating suggestions")
                            self.suggestions = suggest_moves(self, for_player=True)
                            print(f"Generated {len(self.suggestions)} suggestions")
                            for s in self.suggestions:
                                print(f"Suggestion: {s.get('description')} ({s.get('type')})")
                        else:
                            logger.info("Move suggestions disabled")
                            self.suggestions = []

                    elif event.key == pygame.K_s:
                        if not self.playback_active:
                            self.save_game_progress()
                            continue

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_pos = pygame.mouse.get_pos()
                        clicked_cell = self.get_cell_at_position(mouse_pos[0], mouse_pos[1])

                        if clicked_cell:
                            if not creating_bridge:
                                if (self.control_enemy and clicked_cell.cell_type == CellType.ENEMY) or \
                                        (not self.control_enemy and clicked_cell.cell_type == CellType.PLAYER):
                                    creating_bridge = True
                                    bridge_start_cell = clicked_cell
                                    self.create_impact_effect(clicked_cell.x, clicked_cell.y,
                                                                not self.control_enemy)
                            else:
                                if clicked_cell != bridge_start_cell:
                                    if self.create_bridge(bridge_start_cell, clicked_cell):
                                        self.create_impact_effect(clicked_cell.x, clicked_cell.y,
                                                                    not self.control_enemy)
                                        
                                        # Record this bridge creation
                                        if hasattr(self, 'game_recorder') and self.game_recorder and self.game_recorder.recording:
                                            self.game_recorder.record_event("BRIDGE_CREATED", {
                                                "source_cell_id": id(bridge_start_cell),
                                                "target_cell_id": id(clicked_cell)
                                            })
                                        
                                        # Send to network if online
                                        if self.game_type == GameType.ONLINE and hasattr(self, 'send_network_event'):
                                            self.send_network_event("BRIDGE_CREATED", {
                                                "source_cell_id": id(bridge_start_cell),
                                                "target_cell_id": id(clicked_cell)
                                            })
                                        
                                        if self.turn_based_mode:
                                            self.move_made_this_turn = True
                                            self.switch_turns()
                                
                                creating_bridge = False
                                bridge_start_cell = None
                        else:
                            clicked_bridge, refund_to_source = self.get_bridge_at_position(mouse_pos[0], mouse_pos[1])

                            if clicked_bridge:
                                refund_cell = clicked_bridge.source_cell if refund_to_source else clicked_bridge.target_cell
                                can_remove = False

                                if (self.control_enemy and refund_cell.cell_type == CellType.ENEMY) or \
                                        (not self.control_enemy and refund_cell.cell_type == CellType.PLAYER):
                                    can_remove = True

                                if can_remove:
                                    bridge_cost = getattr(clicked_bridge, 'creation_cost', 1)
                                    
                                    # Record before removing
                                    if hasattr(self, 'game_recorder') and self.game_recorder and self.game_recorder.recording:
                                        self.game_recorder.record_event("BRIDGE_REMOVED", {
                                            "source_cell_id": id(clicked_bridge.source_cell),
                                            "target_cell_id": id(clicked_bridge.target_cell)
                                        })
                                    
                                    self.remove_bridge(clicked_bridge)
                                    refund_cell.points += bridge_cost

                                    self.create_impact_effect(refund_cell.x, refund_cell.y,
                                                                refund_cell.cell_type == CellType.PLAYER)
                                    logger.info(
                                        f"Bridge removed. Refunded {bridge_cost} points to cell at ({refund_cell.x}, {refund_cell.y})")
                                    
                                    # Send to network if online
                                    if self.game_type == GameType.ONLINE and hasattr(self, 'send_network_event'):
                                        self.send_network_event("BRIDGE_REMOVED", {
                                            "source_cell_id": id(clicked_bridge.source_cell),
                                            "target_cell_id": id(clicked_bridge.target_cell)
                                        })

                                    continue

                        if self.show_context_menu:
                            if self.menu_rect.collidepoint(mouse_pos):
                                option_index = (mouse_pos[1] - self.menu_rect.y) // 30
                                if option_index == 0:
                                    logger.info(f"All connections are removed")
                                    self.remove_all_bridges_from_cell(self.context_menu_cell)

                            self.show_context_menu = False
                            self.context_menu_cell = None
                            continue

                    elif event.button == 3:  # Right click
                        mouse_pos = pygame.mouse.get_pos()
                        clicked_cell = self.get_cell_at_position(mouse_pos[0], mouse_pos[1])

                        if clicked_cell:
                            if (self.control_enemy and clicked_cell.cell_type == CellType.ENEMY) or \
                                    (not self.control_enemy and clicked_cell.cell_type == CellType.PLAYER):
                                self.show_context_menu = True
                                self.context_menu_cell = clicked_cell
                                logger.info(f"Context menu opened for cell at ({clicked_cell.x}, {clicked_cell.y})")

            # Turn-based mode timer
            if self.turn_based_mode and self.turn_timer_active:
                dt = self.clock.get_time() / 1000.0  # ms to s
                self.turn_time_remaining -= dt

                if self.turn_time_remaining <= 0 or self.move_made_this_turn:
                    self.switch_turns()
                    
                    # Record turn switch
                    if hasattr(self, 'game_recorder') and self.game_recorder and self.game_recorder.recording:
                        self.game_recorder.record_event("TURN_SWITCH", {
                            "is_player_turn": self.current_player_turn
                        })
                    
                    # Send to network if online
                    if self.game_type == GameType.ONLINE and hasattr(self, 'send_network_event'):
                        self.send_network_event("TURN_SWITCH", {
                            "is_player_turn": self.current_player_turn
                        })

            # Update all cells
            for cell in self.cells:
                old_points = cell.points
                old_evolution = cell.evolution.value if hasattr(cell.evolution, 'value') else 0
                
                cell.update(current_time)
                if cell.cell_type != CellType.EMPTY:
                    self.update_evolution_based_on_points(cell)
                
                # Record cell updates if significant changes occurred
                if (hasattr(self, 'game_recorder') and self.game_recorder and self.game_recorder.recording and 
                    (old_points != cell.points or 
                    (hasattr(cell.evolution, 'value') and old_evolution != cell.evolution.value))):
                    
                    self.game_recorder.record_event("CELL_UPDATED", {
                        "cell_id": id(cell),
                        "points": cell.points,
                        "evolution": cell.evolution.value if hasattr(cell.evolution, 'value') else 0
                    })

            # AI difficulty settings
            if self.ai_enabled:
                if self.ai_difficulty == "Easy":
                    self.ai_move_cooldown = 1500
                elif self.ai_difficulty == "Medium":
                    self.ai_move_cooldown = 1000
                else:  # Hard
                    self.ai_move_cooldown = 500

                #self.ai.update(current_time)

                #if current_time % 20000 < 50:
                    #   self.ai.adapt_strategy()

            # Spawn new balls
            self.spawn_balls(current_time)

            # Update bridges
            for bridge in self.bridges:
                bridge.update()

            # Process balls movement and collisions
            balls_to_remove = []
            for ball in self.balls:
                ball.update()

                for other_ball in self.balls:
                    if ball != other_ball and ball.check_collision(other_ball):
                        if ball not in balls_to_remove:
                            balls_to_remove.append(ball)
                        if other_ball not in balls_to_remove:
                            balls_to_remove.append(other_ball)

                        self.create_collision_effect(ball.x, ball.y)
                        
                        # Record collision
                        if hasattr(self, 'game_recorder') and self.game_recorder and self.game_recorder.recording:
                            self.game_recorder.record_event("BALL_COLLISION", {
                                "x": ball.x,
                                "y": ball.y
                            })

                target_cell = self.get_cell_at_position(ball.target_x, ball.target_y)
                if target_cell and ball.reached_target(target_cell):
                    balls_to_remove.append(ball)
                    old_points = target_cell.points
                    old_type = target_cell.cell_type
                    
                    self.create_impact_effect(target_cell.x, target_cell.y, ball.is_player)

                    if target_cell.cell_type == CellType.EMPTY:
                        captured = target_cell.try_capture(ball.attack_value, ball.is_player)
                        if captured and ball.is_player:
                            self.points += 50
                            
                            # Record empty cell capture
                            if hasattr(self, 'game_recorder') and self.game_recorder and self.game_recorder.recording:
                                self.game_recorder.record_event("CELL_CAPTURED", {
                                    "cell_id": id(target_cell),
                                    "new_type": target_cell.cell_type.name,
                                    "points": target_cell.points
                                })
                                
                    elif (target_cell.cell_type == CellType.PLAYER and ball.is_player) or \
                            (target_cell.cell_type == CellType.ENEMY and not ball.is_player):
                        target_cell.points += ball.attack_value
                        if ball.is_player:
                            self.points += 5
                        
                        # Record reinforcement
                        if hasattr(self, 'game_recorder') and self.game_recorder and self.game_recorder.recording:
                            self.game_recorder.record_event("CELL_REINFORCED", {
                                "cell_id": id(target_cell),
                                "points_added": ball.attack_value,
                                "total_points": target_cell.points
                            })
                    else:
                        damage = ball.attack_value

                        if not getattr(ball, 'is_support_ball', False):
                            support_multiplier = self.get_support_bonus(ball.source_cell)
                            damage = int(damage * support_multiplier)

                        old_points = target_cell.points
                        target_cell.points = max(0, target_cell.points - damage)
                        points_reduced = old_points - target_cell.points

                        if ball.is_player:
                            self.points += points_reduced * 10

                        if damage > ball.attack_value and ball.is_player:
                            self.create_support_effect(target_cell.x, target_cell.y, ball.is_player)

                        # Record attack
                        if hasattr(self, 'game_recorder') and self.game_recorder and self.game_recorder.recording:
                            self.game_recorder.record_event("CELL_ATTACKED", {
                                "cell_id": id(target_cell),
                                "damage": damage,
                                "remaining_points": target_cell.points
                            })

                        if target_cell.points == 0:
                            self.remove_all_bridges_from_cell(target_cell)
                            old_type = target_cell.cell_type
                            target_cell.cell_type = CellType.PLAYER if ball.is_player else CellType.ENEMY
                            target_cell.points = 10

                            if ball.is_player:
                                self.points += 100

                            logger.info(
                                f"Cell at ({target_cell.x}, {target_cell.y}) captured: {old_type} -> {target_cell.cell_type}")

                            # Record capture
                            if hasattr(self, 'game_recorder') and self.game_recorder and self.game_recorder.recording:
                                self.game_recorder.record_event("CELL_CAPTURED", {
                                    "cell_id": id(target_cell),
                                    "previous_type": old_type.name,
                                    "new_type": target_cell.cell_type.name
                                })

                            for _ in range(5):
                                self.create_impact_effect(target_cell.x, target_cell.y, ball.is_player)
            
            # Remove processed balls
            for ball in balls_to_remove:
                if ball in self.balls:
                    self.balls.remove(ball)

            # Draw everything
            self.screen.blit(background, (0, 0))

            for bridge in self.bridges:
                bridge.draw(self.screen)

            if creating_bridge:
                mouse_pos = pygame.mouse.get_pos()
                pygame.draw.line(self.screen, (100, 100, 100),
                                    (bridge_start_cell.x, bridge_start_cell.y),
                                    mouse_pos, BRIDGE_WIDTH)

            for cell in self.cells:
                cell.draw(self.screen, self)

            for ball in self.balls:
                ball.draw(self.screen)

            self.draw_game_info()

            if self.show_suggestions:
                draw_suggestions(self, self.screen)

            self.draw_context_menu(self.screen)
            
            # Check win condition
            if self.check_win_condition():
                continue
                
            pygame.display.flip()

        if hasattr(self, 'network_client') and self.network_client:
            self.network_client.disconnect()
        
        pygame.quit()
        sys.exit()

    def get_cell_at_position(self, x, y):
        for cell in self.cells:
            if cell.contains_point(x, y):
                return cell
        return None

    def count_outgoing_bridges(self, cell):
        return len(cell.outgoing_bridges)

    def create_bridge(self, source_cell, target_cell):
        existing_bridge = None
        if self.count_outgoing_bridges(source_cell) >= source_cell.evolution.value:
            logger.info(f"Cell can't create more bridges. Evolution level: {source_cell.evolution.value}")
            return False

        distance = self.calculate_distance(source_cell, target_cell)
        bridge_cost = max(1, int(distance / 30))

        if source_cell.points < bridge_cost:
            logger.info(f"Not enough points to create bridge. Need {bridge_cost}, have {source_cell.points}")
            return False

        for bridge in self.bridges:
            if (bridge.source_cell == source_cell and bridge.target_cell == target_cell) or \
                    (bridge.source_cell == target_cell and bridge.target_cell == source_cell and
                     source_cell.cell_type == target_cell.cell_type):
                logger.info(f"Bridge already exists between these cells")
                return False
            if bridge.source_cell == source_cell and bridge.target_cell == target_cell:
                return False
            elif bridge.source_cell == target_cell and bridge.target_cell == source_cell:
                existing_bridge = bridge

        new_bridge = Bridge(source_cell, target_cell)
        self.bridges.append(new_bridge)
        logger.info(f"Bridge created from ({source_cell.x}, {source_cell.y}) to ({target_cell.x}, {target_cell.y})")

        source_cell.points -= bridge_cost
        logger.info(f"Bridge created. Cost: {bridge_cost} points. Remaining: {source_cell.points}")

        # new_bridge = Bridge(source_cell, target_cell)
        new_bridge.creation_cost = bridge_cost
        # self.bridges.append(new_bridge)

        source_cell.outgoing_bridges.append(new_bridge)
        target_cell.incoming_bridges.append(new_bridge)

        if existing_bridge:
            new_bridge.direction = BridgeDirection.TWO_WAY
            existing_bridge.direction = BridgeDirection.TWO_WAY
            new_bridge.has_reverse = True
            existing_bridge.has_reverse = True

        if self.turn_based_mode and not self.move_made_this_turn:
            self.move_made_this_turn = True
            logger.info(f"{'Player' if not self.control_enemy else 'Enemy'} made a move")

        if new_bridge and not self.playback_active:
            self.game_recorder.record_event("BRIDGE_CREATED", {
                "sourceId": self.game_recorder.cell_id_map.get(source_cell, -1),
                "targetId": self.game_recorder.cell_id_map.get(target_cell, -1),
                "direction": "TWO_WAY" if existing_bridge else "ONE_WAY",
                "cost": bridge_cost
            })

        if self.game_type == GameType.ONLINE:
            self.send_network_event("BRIDGE_CREATED", {
                "source_cell_id": id(source_cell),
                "target_cell_id": id(target_cell)
            })

        return True

    def spawn_balls(self, current_time):
        for bridge in self.bridges:
            source_spawn_interval = 3000 // bridge.source_cell.evolution.value

            bridge_key = (id(bridge.source_cell), id(bridge.target_cell))
            if bridge_key not in self.last_ball_spawn_time or \
                    current_time - self.last_ball_spawn_time[bridge_key] >= source_spawn_interval:

                if bridge.source_cell.cell_type != CellType.EMPTY and bridge.source_cell.points > 0:
                    is_player = bridge.source_cell.cell_type == CellType.PLAYER

                    self.balls.append(Ball(bridge.source_cell, bridge.target_cell, is_player))

                    is_combat = (bridge.target_cell.cell_type != CellType.EMPTY and
                                 bridge.target_cell.cell_type != bridge.source_cell.cell_type)

                    if is_combat:
                        support_multiplier = self.get_support_bonus(bridge.source_cell)

                        if support_multiplier > 1.0:
                            extra_balls = int((support_multiplier - 1.0) * 5)

                            for _ in range(min(extra_balls, 3)):
                                if random.random() < 0.5:
                                    support_ball = Ball(bridge.source_cell, bridge.target_cell, is_player)
                                    support_ball.is_support_ball = True
                                    if is_player:
                                        support_ball.color = (100, 150, 255)
                                    else:
                                        support_ball.color = (255, 100, 100)
                                    self.balls.append(support_ball)

                                    logger.debug(f"Support ball spawned ({support_multiplier:.1f}x bonus)")

                    bridge.source_cell.points -= 1

                    self.last_ball_spawn_time[bridge_key] = current_time

            if bridge.direction == BridgeDirection.TWO_WAY and bridge.has_reverse:
                target_spawn_interval = 3000 // bridge.target_cell.evolution.value
                reverse_bridge_key = (id(bridge.target_cell), id(bridge.source_cell))

                if reverse_bridge_key not in self.last_ball_spawn_time or \
                        current_time - self.last_ball_spawn_time[reverse_bridge_key] >= target_spawn_interval:

                    if bridge.target_cell.cell_type != CellType.EMPTY and bridge.target_cell.points > 0:
                        is_player = bridge.target_cell.cell_type == CellType.PLAYER

                        self.balls.append(Ball(bridge.target_cell, bridge.source_cell, is_player))

                        is_combat = (bridge.source_cell.cell_type != CellType.EMPTY and
                                     bridge.source_cell.cell_type != bridge.target_cell.cell_type)

                        if is_combat:
                            support_multiplier = self.get_support_bonus(bridge.target_cell)

                            if support_multiplier > 1.0:
                                extra_balls = int((support_multiplier - 1.0) * 5)

                                for _ in range(min(extra_balls, 3)):
                                    if random.random() < 0.5:
                                        support_ball = Ball(bridge.target_cell, bridge.source_cell, is_player)
                                        support_ball.is_support_ball = True
                                        if is_player:
                                            support_ball.color = (100, 150, 255)
                                        else:
                                            support_ball.color = (255, 100, 100)
                                        self.balls.append(support_ball)

                        bridge.target_cell.points -= 1

                        self.last_ball_spawn_time[reverse_bridge_key] = current_time

    def draw_context_menu(self, screen):
        if not self.show_context_menu or not self.context_menu_cell:
            return

        menu_width = 180
        menu_height = 30 * len(self.context_menu_options)
        menu_x = min(self.context_menu_cell.x + 40, SCREEN_WIDTH - menu_width)
        menu_y = min(self.context_menu_cell.y + 40, SCREEN_HEIGHT - menu_height)

        menu_surface = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        menu_surface.fill((40, 40, 50, 220))
        pygame.draw.rect(menu_surface, WHITE, (0, 0, menu_width, menu_height), 1)

        for i, option in enumerate(self.context_menu_options):
            text_surface = self.font.render(option, True, WHITE)
            text_rect = text_surface.get_rect(midleft=(10, 15 + i * 30))
            menu_surface.blit(text_surface, text_rect)

        screen.blit(menu_surface, (menu_x, menu_y))

        self.menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)

    def show_replay_menu(self):
        MENU_BG_COLOR = (20, 20, 40)
        TITLE_COLOR = (220, 220, 255)

        menu_running = True
        clock = pygame.time.Clock()

        json_files = []
        xml_files = []

        if os.path.exists("saved_games/json"):
            json_files = sorted([f for f in os.listdir("saved_games/json") if f.endswith(".json")], reverse=True)

        if os.path.exists("saved_games/xml"):
            xml_files = sorted([f for f in os.listdir("saved_games/xml") if f.endswith(".xml")], reverse=True)

        formats = ["JSON", "XML", "MongoDB"]
        current_format = 0

        mongodb_games = []
        try:
            mongodb_games = get_saved_games_from_mongodb(20)  #limit up to 20 games
        except:
            logger.error("Failed to fetch games from MongoDB")

        scroll_offset = 0
        max_items = 8
        selected_index = 0

        def get_active_list():
            if formats[current_format] == "JSON":
                return json_files
            elif formats[current_format] == "XML":
                return xml_files
            elif formats[current_format] == "MongoDB":
                return mongodb_games
            else:
                return []

        while menu_running:
            active_list = get_active_list()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    elif event.key == pygame.K_UP:
                        selected_index = max(0, selected_index - 1)
                        if selected_index < scroll_offset:
                            scroll_offset = selected_index
                    elif event.key == pygame.K_DOWN:
                        selected_index = min(len(active_list) - 1, selected_index + 1)
                        if selected_index >= scroll_offset + max_items:
                            scroll_offset = selected_index - max_items + 1
                    elif event.key == pygame.K_LEFT:
                        current_format = (current_format - 1) % len(formats)
                        selected_index = 0
                        scroll_offset = 0
                    elif event.key == pygame.K_RIGHT:
                        current_format = (current_format + 1) % len(formats)
                        selected_index = 0
                        scroll_offset = 0
                    elif event.key == pygame.K_RETURN:
                        if active_list and 0 <= selected_index < len(active_list):
                            if formats[current_format] == "JSON":
                                filename = f"saved_games/json/{active_list[selected_index]}"
                                if self.start_playback(filename, "json"):
                                    return True
                            elif formats[current_format] == "XML":
                                filename = f"saved_games/xml/{active_list[selected_index]}"
                                if self.start_playback(filename, "xml"):
                                    return True
                            elif formats[current_format] == "MongoDB" and mongodb_games and 0 <= selected_index < len(
                                    mongodb_games):
                                game_id = str(mongodb_games[selected_index]["_id"])
                                if self.start_playback(game_id, "mongodb"):
                                    self.game_started = True
                                    return True

                    if formats[current_format] == "JSON":
                        filename = f"saved_games/json/{active_list[selected_index]}"
                        if self.start_playback(filename, "json"):
                            return True
                    elif formats[current_format] == "XML":
                        filename = f"saved_games/xml/{active_list[selected_index]}"
                        if self.start_playback(filename, "xml"):
                            return True
                    elif formats[current_format] == "MongoDB":
                        if not active_list:
                            no_files_font = pygame.font.SysFont('Arial', 20)
                            no_files_text = "No MongoDB saved games found"
                            no_files_surface = no_files_font.render(no_files_text, True, (180, 180, 180))
                            no_files_rect = no_files_surface.get_rect(center=(SCREEN_WIDTH / 2, 200))
                            self.screen.blit(no_files_surface, no_files_rect)
                        else:
                            item_font = pygame.font.SysFont('Arial', 18)
                            for i in range(min(max_items, len(active_list) - scroll_offset)):
                                idx = scroll_offset + i
                                item = active_list[idx]

                                try:
                                    timestamp = item.get("timestamp", None)
                                    if timestamp:
                                        formatted_date = timestamp.strftime("%Y-%m-%d")
                                        formatted_time = timestamp.strftime("%H:%M:%S")
                                        display_text = f"{formatted_date} {formatted_time}"
                                    else:
                                        display_text = f"Game {idx + 1}"
                                except:
                                    display_text = f"Game {idx + 1}"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_pos = pygame.mouse.get_pos()

                        tab_width = SCREEN_WIDTH / len(formats)
                        for i, fmt in enumerate(formats):
                            tab_rect = pygame.Rect(tab_width * i, 0, tab_width, 50)
                            if tab_rect.collidepoint(mouse_pos):
                                current_format = i
                                selected_index = 0
                                scroll_offset = 0

                        item_height = 50
                        for i in range(min(max_items, len(active_list) - scroll_offset)):
                            item_rect = pygame.Rect(100, 100 + i * item_height, SCREEN_WIDTH - 200, item_height)
                            if item_rect.collidepoint(mouse_pos):
                                selected_index = scroll_offset + i

                                if formats[current_format] == "JSON":
                                    filename = f"saved_games/json/{active_list[selected_index]}"
                                    success = self.start_playback(filename, "json")
                                    if success:
                                        self.game_started = True
                                        return True
                                elif formats[current_format] == "XML":
                                    filename = f"saved_games/xml/{active_list[selected_index]}"
                                    success = self.start_playback(filename, "xml")
                                    if success:
                                        self.game_started = True
                                        return True
                    elif event.button == 4:  # Scroll up
                        scroll_offset = max(0, scroll_offset - 1)
                    elif event.button == 5:  # Scroll down
                        scroll_offset = min(max(0, len(active_list) - max_items), scroll_offset + 1)

            self.screen.fill(MENU_BG_COLOR)

            title_font = pygame.font.SysFont('Arial', 36, bold=True)
            title_text = "REPLAY SAVED GAMES"
            title_surface = title_font.render(title_text, True, TITLE_COLOR)
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH / 2, 30))
            self.screen.blit(title_surface, title_rect)

            tab_font = pygame.font.SysFont('Arial', 24, bold=True)
            tab_width = SCREEN_WIDTH / len(formats)
            for i, fmt in enumerate(formats):
                tab_color = (80, 100, 180) if i == current_format else (50, 50, 70)
                pygame.draw.rect(self.screen, tab_color, (tab_width * i, 60, tab_width, 40))
                pygame.draw.rect(self.screen, (100, 100, 150), (tab_width * i, 60, tab_width, 40), 1)

                fmt_surface = tab_font.render(fmt, True, (255, 255, 255))
                fmt_rect = fmt_surface.get_rect(center=(tab_width * i + tab_width / 2, 80))
                self.screen.blit(fmt_surface, fmt_rect)

            if not active_list:
                no_files_font = pygame.font.SysFont('Arial', 20)
                no_files_text = f"No {formats[current_format]} replay files found"
                no_files_surface = no_files_font.render(no_files_text, True, (180, 180, 180))
                no_files_rect = no_files_surface.get_rect(center=(SCREEN_WIDTH / 2, 200))
                self.screen.blit(no_files_surface, no_files_rect)
            else:
                item_font = pygame.font.SysFont('Arial', 18)
                for i in range(min(max_items, len(active_list) - scroll_offset)):
                    idx = scroll_offset + i
                    item = active_list[idx]

                    # extract date and time from filename
                    # format: game_20240406_123456_789.json
                    try:
                        date_str = item.split("_")[1]
                        time_str = item.split("_")[2]
                        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                        formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
                        display_text = f"{formatted_date} {formatted_time}"
                    except:
                        display_text = item

                    item_y = 120 + i * 50
                    item_rect = pygame.Rect(100, item_y, SCREEN_WIDTH - 200, 40)

                    highlight_color = (60, 100, 180) if idx == selected_index else (40, 40, 60)
                    pygame.draw.rect(self.screen, highlight_color, item_rect)
                    pygame.draw.rect(self.screen, (100, 100, 150), item_rect, 1)

                    item_surface = item_font.render(display_text, True, (255, 255, 255))
                    self.screen.blit(item_surface, (120, item_y + 12))

            instructions_font = pygame.font.SysFont('Arial', 16)
            instructions = [
                "↑/↓: Navigate files   ←/→: Change format",
                "ENTER: Load selected replay   ESC: Back to menu"
            ]

            for i, instruction in enumerate(instructions):
                inst_surface = instructions_font.render(instruction, True, (180, 180, 180))
                inst_rect = inst_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50 + i * 20))
                self.screen.blit(inst_surface, inst_rect)

            pygame.display.flip()
            clock.tick(30)

        return False

    def remove_all_bridges_from_cell(self, cell):
        logger.info(f"Removing all bridges from cell at ({cell.x}, {cell.y})")

        bridges_to_remove = []
        bridges_to_modify = []

        for bridge in self.bridges:
            if bridge.source_cell == cell:
                has_reverse = False
                for other_bridge in self.bridges:
                    if other_bridge.source_cell == bridge.target_cell and other_bridge.target_cell == cell:
                        has_reverse = True
                        if bridge.direction == BridgeDirection.TWO_WAY:
                            bridges_to_modify.append(other_bridge)

                bridges_to_remove.append(bridge)

        for bridge in bridges_to_remove:
            if bridge in self.bridges:
                self.bridges.remove(bridge)
                if bridge in cell.outgoing_bridges:
                    cell.outgoing_bridges.remove(bridge)
                if bridge in bridge.target_cell.incoming_bridges:
                    bridge.target_cell.incoming_bridges.remove(bridge)

        for bridge in bridges_to_modify:
            bridge.direction = BridgeDirection.ONE_WAY
            bridge.has_reverse = False
            logger.info(f"Bridge direction changed to one-way")

    def draw_game_info(self):
        player_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.PLAYER)
        enemy_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.ENEMY)
        empty_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.EMPTY)

        if empty_cells == 0:
            if enemy_cells == 0:
                self.game_over_state = True
                save_level_stats(self)
                self.game_over("Blue Wins!")
            elif player_cells == 0:
                self.game_over_state = True
                self.game_over("Red Wins!")

        player_points = sum(cell.points for cell in self.cells if cell.cell_type == CellType.PLAYER)
        enemy_points = sum(cell.points for cell in self.cells if cell.cell_type == CellType.ENEMY)

        info_surface = pygame.Surface((350, 90), pygame.SRCALPHA)
        info_surface.fill((0, 0, 0, 150))
        self.screen.blit(info_surface, (10, 10))

        title_font = pygame.font.SysFont('Arial', 16, bold=True)
        title_text = "WAR OF CELLS"
        title_surface = title_font.render(title_text, True, (200, 200, 255))
        self.screen.blit(title_surface, (20, 15))

        info_text = f"Player Cells: {player_cells} | Enemy Cells: {enemy_cells} | Empty Cells: {empty_cells}"
        info_surface = self.font.render(info_text, True, WHITE)
        self.screen.blit(info_surface, (20, 35))

        points_text = f"Player Points: {player_points} | Enemy Points: {enemy_points}"
        points_surface = self.font.render(points_text, True, WHITE)
        self.screen.blit(points_surface, (20, 55))

        controls_text = "Click cells to create bridges | Press E to select + SPACE to evolve"
        controls_surface = self.font.render(controls_text, True, (200, 200, 200))
        self.screen.blit(controls_surface, (20, 75))

        points_text = f"Points: {self.points}"
        points_surface = self.font.render(points_text, True, WHITE)
        self.screen.blit(points_surface, (20, SCREEN_HEIGHT - 60))

        time_text = f"Time: {format_time(self.time_taken)}"
        time_surface = self.font.render(time_text, True, WHITE)
        self.screen.blit(time_surface, (20, SCREEN_HEIGHT - 40))

        level_text = f"Level: {self.current_level.replace('level', '')}"
        level_surface = self.font.render(level_text, True, WHITE)
        self.screen.blit(level_surface, (20, SCREEN_HEIGHT - 80))

        if self.turn_based_mode:
            turn_bg = pygame.Surface((200, 60), pygame.SRCALPHA)
            turn_bg.fill((0, 0, 0, 150))
            self.screen.blit(turn_bg, (SCREEN_WIDTH - 210, 10))

            mode_text = "TURN-BASED MODE"
            mode_font = pygame.font.SysFont('Arial', 14, bold=True)
            mode_surface = mode_font.render(mode_text, True, (200, 200, 255))
            self.screen.blit(mode_surface, (SCREEN_WIDTH - 200, 15))

            turn_color = PLAYER_COLOR if self.current_player_turn else ENEMY_COLOR
            turn_text = f"{self.turn_status_message}: {int(self.turn_time_remaining)}s"
            turn_font = pygame.font.SysFont('Arial', 18, bold=True)
            turn_surface = turn_font.render(turn_text, True, turn_color)
            self.screen.blit(turn_surface, (SCREEN_WIDTH - 200, 35))

            hint_text = "Press T to toggle mode"
            hint_font = pygame.font.SysFont('Arial', 12)
            hint_surface = hint_font.render(hint_text, True, (150, 150, 150))
            self.screen.blit(hint_surface, (SCREEN_WIDTH - 200, 55))
        if self.ai_enabled:
            ai_text = f"AI: ON ({self.ai_difficulty})"
            ai_color = (200, 255, 200)
        else:
            ai_text = "AI: OFF"
            ai_color = (255, 200, 200)

        ai_surface = self.font.render(ai_text, True, ai_color)
        self.screen.blit(ai_surface, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 20))

        if self.ai_enabled and self.turn_based_mode and not self.current_player_turn:
            thinking_text = "AI thinking..."
            thinking_surface = self.font.render(thinking_text, True, (255, 255, 100))
            self.screen.blit(thinking_surface, (SCREEN_WIDTH / 2 - 50, 15))

        if self.show_suggestions:
            hint_text = "Suggestions: ON (Press H to hide)"
            hint_color = (200, 255, 200)
        else:
            hint_text = "Press H for move suggestions"
            hint_color = (200, 200, 200)

        hint_surface = self.font.render(hint_text, True, hint_color)
        self.screen.blit(hint_surface, (20, SCREEN_HEIGHT - 20))

    def check_win_condition(self):
        player_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.PLAYER)
        enemy_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.ENEMY)
        empty_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.EMPTY)

        if empty_cells == 0:
            if player_cells == 0:
                # self.game_over("Enemy wins! All cells are captured.")
                return True
            elif enemy_cells == 0:
                # self.game_over("Player wins! All cells are captured.")
                return True

        return False

    def game_over(self, message):
        logger.info(f"Game over: {message}")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        font = pygame.font.SysFont('Arial', 48, bold=True)
        text_surface = font.render(message, True, WHITE)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 60))
        self.screen.blit(text_surface, text_rect)

        if "Player Wins" in message:
            stars = calculate_stars(self.points, self.time_taken)

            stats_font = pygame.font.SysFont('Arial', 24)

            points_text = f"Points: {self.points}"
            points_surface = stats_font.render(points_text, True, WHITE)
            points_rect = points_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 10))
            self.screen.blit(points_surface, points_rect)

            time_text = f"Time: {format_time(self.time_taken)}"
            time_surface = stats_font.render(time_text, True, WHITE)
            time_rect = time_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20))
            self.screen.blit(time_surface, time_rect)

            star_font = pygame.font.SysFont('Arial', 20)
            star_text = f"Stars: "
            star_surface = star_font.render(star_text, True, WHITE)
            star_rect = star_surface.get_rect(midright=(SCREEN_WIDTH / 2 - 30, SCREEN_HEIGHT / 2 + 50))
            self.screen.blit(star_surface, star_rect)

            for i in range(3):
                star_color = (255, 255, 0) if i < stars else (80, 80, 80)
                star_rect = pygame.Rect(SCREEN_WIDTH / 2 - 20 + i * 30, SCREEN_HEIGHT / 2 + 40, 20, 20)
                points = []
                for j in range(5):
                    angle = math.pi * 2 * j / 5 - math.pi / 2
                    points.append((star_rect.centerx + math.cos(angle) * 10,
                                   star_rect.centery + math.sin(angle) * 10))
                    angle += math.pi / 5
                    points.append((star_rect.centerx + math.cos(angle) * 5,
                                   star_rect.centery + math.sin(angle) * 5))
                pygame.draw.polygon(self.screen, star_color, points)

            options_font = pygame.font.SysFont('Arial', 24)

            if self.current_level.startswith("level"):
                level_num = int(self.current_level[5:])
                next_level = f"level{level_num + 1}"

                if next_level in self.game_data.get("levels", {}):
                    next_text = "Press N for next level"
                    next_surface = options_font.render(next_text, True, (100, 255, 100))
                    next_rect = next_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 90))
                    self.screen.blit(next_surface, next_rect)

        options_font = pygame.font.SysFont('Arial', 24)

        menu_text = "Press M to return to menu"
        menu_surface = options_font.render(menu_text, True, (255, 200, 100))
        menu_rect = menu_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 120))
        self.screen.blit(menu_surface, menu_rect)

        quit_text = "Press ESC to quit game"
        quit_surface = options_font.render(quit_text, True, (255, 100, 100))
        quit_rect = quit_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150))
        self.screen.blit(quit_surface, quit_rect)

        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_m:
                        self.game_started = False
                        waiting = False
                    elif event.key == pygame.K_n and "Player Wins" in message:
                        if self.current_level.startswith("level"):
                            level_num = int(self.current_level[5:])
                            next_level = f"level{level_num + 1}"

                            if next_level in self.game_data.get("levels", {}):
                                self.current_level = next_level
                                self.start_game()
                                waiting = False
        if not self.playback_active:
            result = "Player Wins" if "Blue Wins" in message else "Enemy Wins"
            self.game_recorder.game_id = generate_game_id(self.current_level, completed=True)

            self.game_recorder.stop_recording(result)

            json_file = self.game_recorder.save_to_json()
            xml_file = self.game_recorder.save_to_xml()
            mongo_id = self.game_recorder.save_to_mongodb()

            logger.info(f"Game history saved to JSON: {json_file}")
            logger.info(f"Game history saved to XML: {xml_file}")
            try:
                mongodb_id = self.game_recorder.save_to_mongodb()
                if mongodb_id:
                    logger.info(f"Game history saved to MongoDB with ID: {mongodb_id}")
            except Exception as e:
                logger.error(f"Failed to save to MongoDB: {e}")
            except ImportError:
                pass

    def reset_game(self):
        self.cells = []
        self.bridges = []
        self.balls = []
        self.effects = []
        self.selected_cell = None
        self.last_ball_spawn_time = {}
        self.control_enemy = False

        self.initialize_board()
        logger.info("Game reset")

    def start_playback(self, filename, format_type="json"):
        self.playback_active = True
        self.game_playback = GamePlayback(
            self,
            cell_class=Cell,
            cell_type_class=CellType,
            cell_shape_class=CellShape,
            evolution_level_class=EvolutionLevel
        )

        success = False
        if format_type.lower() == "json":
            success = self.game_playback.load_json_history(filename)
        elif format_type.lower() == "xml":
            success = self.game_playback.load_xml_history(filename)
        elif format_type.lower() == "mongodb":
            success = self.game_playback.load_mongodb_history(filename)

        if success:
            self.game_playback.start_playback()
            self.playback_controls_visible = True
            return True
        else:
            self.playback_active = False
            self.game_playback = None
            return False

    def show_continue_dialog(self, saved_game):
        dialog_bg = pygame.Surface((500, 200), pygame.SRCALPHA)
        dialog_bg.fill((30, 30, 50, 220))

        dialog_x = (SCREEN_WIDTH - 500) // 2
        dialog_y = (SCREEN_HEIGHT - 200) // 2

        font_title = pygame.font.SysFont('Arial', 24, bold=True)
        font_text = pygame.font.SysFont('Arial', 18)

        timestamp = saved_game["timestamp"].replace("_", " ")
        points = saved_game["data"]["events"][-1]["data"].get("points", 0)
        time_taken = saved_game["data"]["events"][-1]["data"].get("time_taken", 0)

        title_surface = font_title.render("Continue Game", True, (255, 255, 255))
        text1 = font_text.render(f"Found saved game from: {timestamp}", True, (220, 220, 220))
        text2 = font_text.render(f"Points: {points}, Time: {format_time(time_taken)}", True, (220, 220, 220))
        text3 = font_text.render("Do you want to continue this game?", True, (220, 220, 220))

        continue_button = pygame.Rect(dialog_x + 80, dialog_y + 150, 150, 30)
        new_game_button = pygame.Rect(dialog_x + 270, dialog_y + 150, 150, 30)

        continue_text = font_text.render("Continue", True, (255, 255, 255))
        new_game_text = font_text.render("New Game", True, (255, 255, 255))

        screen_backup = self.screen.copy()

        dialog_active = True
        result = False

        while dialog_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if continue_button.collidepoint(mouse_pos):
                        result = True
                        dialog_active = False
                    elif new_game_button.collidepoint(mouse_pos):
                        result = False
                        dialog_active = False

            self.screen.blit(screen_backup, (0, 0))
            self.screen.blit(dialog_bg, (dialog_x, dialog_y))

            self.screen.blit(title_surface, (dialog_x + 250 - title_surface.get_width() // 2, dialog_y + 20))
            self.screen.blit(text1, (dialog_x + 250 - text1.get_width() // 2, dialog_y + 60))
            self.screen.blit(text2, (dialog_x + 250 - text2.get_width() // 2, dialog_y + 90))
            self.screen.blit(text3, (dialog_x + 250 - text3.get_width() // 2, dialog_y + 120))

            pygame.draw.rect(self.screen, (50, 150, 50), continue_button)
            pygame.draw.rect(self.screen, (150, 50, 50), new_game_button)

            self.screen.blit(continue_text, (continue_button.centerx - continue_text.get_width() // 2,
                                             continue_button.centery - continue_text.get_height() // 2))
            self.screen.blit(new_game_text, (new_game_button.centerx - new_game_text.get_width() // 2,
                                             new_game_button.centery - new_game_text.get_height() // 2))

            pygame.display.flip()

        return result

    def draw_playback_controls(self):
        if not self.game_playback:
            return

        control_height = 40
        control_bg = pygame.Surface((SCREEN_WIDTH, control_height), pygame.SRCALPHA)
        control_bg.fill((0, 0, 0, 180))
        self.screen.blit(control_bg, (0, SCREEN_HEIGHT - control_height))

        font = pygame.font.SysFont('Arial', 16)

        status_text = "⏸ PAUSED" if not self.game_playback.is_playing else "▶ PLAYING"
        status_surface = font.render(status_text, True, WHITE)
        self.screen.blit(status_surface, (20, SCREEN_HEIGHT - control_height + 10))

        speed_text = f"{self.game_playback.playback_speed:.2f}x"
        speed_surface = font.render(speed_text, True, WHITE)
        self.screen.blit(speed_surface, (150, SCREEN_HEIGHT - control_height + 10))

        if self.game_playback.history and len(self.game_playback.history["events"]) > 0:
            total_duration = self.game_playback.history["metadata"].get("duration", 0)
            progress = min(1.0, self.game_playback.current_time / total_duration) if total_duration > 0 else 0

            pygame.draw.rect(self.screen, (80, 80, 80),
                             (200, SCREEN_HEIGHT - control_height + 15, 400, 10))

            pygame.draw.rect(self.screen, (200, 200, 255),
                             (200, SCREEN_HEIGHT - control_height + 15, int(400 * progress), 10))

        help_text = "SPACE: Play/Pause | ←→: Speed | ESC: Exit"
        help_surface = font.render(help_text, True, (200, 200, 200))
        self.screen.blit(help_surface, (SCREEN_WIDTH - 280, SCREEN_HEIGHT - control_height + 10))

    def save_to_mongodb(self, connection_string=None):
        try:
            import pymongo
            MONGODB_AVAILABLE = True
        except ImportError:
            print("MongoDB support not available. Install pymongo package with 'pip install pymongo'")
            return None

        if not self.events:
            return None

        try:
            conn_str = connection_string or "mongodb://localhost:27017/"
            client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)  # 5 second timeout

            client.server_info()

            db = client["war_of_cells"]
            collection = db["game_history"]

            game_history = {
                "metadata": self.metadata,
                "events": self.events
            }

            result = collection.insert_one(game_history)
            print(f"Game history saved to MongoDB with ID: {result.inserted_id}")
            return str(result.inserted_id)

        except pymongo.errors.ServerSelectionTimeoutError:
            print("Could not connect to MongoDB server. Is it running?")
            return None
        except Exception as e:
            print(f"MongoDB error: {e}")
            return None

    def load_saved_game(self, saved_game):
        save_events = [event for event in saved_game["data"]["events"] if event["eventType"] == "GAME_SAVE"]
        if not save_events:
            return False

        save_data = save_events[-1]["data"]

        self.cells = []
        self.bridges = []
        self.balls = []
        self.effects = []
        self.selected_cell = None
        self.last_ball_spawn_time = {}

        cell_id_map = {}
        for cell_data in save_data["cells"]:
            cell_type = getattr(CellType, cell_data["type"])
            shape = getattr(CellShape, cell_data["shape"])
            evolution = EvolutionLevel(cell_data["evolution"])

            new_cell = Cell(cell_data["x"], cell_data["y"], cell_type, shape, evolution)
            new_cell.points = cell_data["points"]
            new_cell.points_to_capture = cell_data["points_to_capture"]
            new_cell.enemy_points_to_capture = cell_data["enemy_points_to_capture"]

            self.cells.append(new_cell)
            cell_id_map[cell_data["id"]] = new_cell

        for bridge_data in save_data.get("bridges", []):
            source_cell = cell_id_map.get(bridge_data["source_cell_id"])
            target_cell = cell_id_map.get(bridge_data["target_cell_id"])

            if source_cell and target_cell:
                new_bridge = Bridge(source_cell, target_cell)
                new_bridge.direction = getattr(BridgeDirection, bridge_data["direction"])
                new_bridge.has_reverse = bridge_data["has_reverse"]
                new_bridge.creation_cost = bridge_data.get("creation_cost", 1)

                self.bridges.append(new_bridge)
                source_cell.outgoing_bridges.append(new_bridge)
                target_cell.incoming_bridges.append(new_bridge)

        for ball_data in save_data.get("balls", []):
            source_cell = cell_id_map.get(ball_data["source_cell_id"])
            if source_cell:
                target_cell = min(self.cells,
                                  key=lambda c: (
                                              (c.x - ball_data["target_x"]) ** 2 + (c.y - ball_data["target_y"]) ** 2))

                new_ball = Ball(source_cell, target_cell, ball_data["is_player"])
                new_ball.x = ball_data["x"]
                new_ball.y = ball_data["y"]
                new_ball.is_support_ball = ball_data.get("is_support_ball", False)
                new_ball.attack_value = ball_data["attack_value"]

                self.balls.append(new_ball)

        self.turn_based_mode = save_data.get("turn_based_mode", False)
        self.current_player_turn = save_data.get("current_player_turn", True)
        self.control_enemy = save_data.get("control_enemy", False)
        self.points = save_data.get("points", 0)
        self.time_taken = save_data.get("time_taken", 0)
        self.start_time = pygame.time.get_ticks() / 1000 - self.time_taken

        return True

    def show_save_dialog(self):
        dialog_bg = pygame.Surface((400, 150), pygame.SRCALPHA)
        dialog_bg.fill((30, 30, 50, 220))

        dialog_x = (SCREEN_WIDTH - 400) // 2
        dialog_y = (SCREEN_HEIGHT - 150) // 2

        font_title = pygame.font.SysFont('Arial', 24, bold=True)
        font_text = pygame.font.SysFont('Arial', 18)

        title_surface = font_title.render("Save Game", True, (255, 255, 255))
        text_surface = font_text.render("Do you want to save your current progress?", True, (220, 220, 220))

        yes_button = pygame.Rect(dialog_x + 80, dialog_y + 100, 100, 30)
        no_button = pygame.Rect(dialog_x + 220, dialog_y + 100, 100, 30)

        yes_text = font_text.render("Yes", True, (255, 255, 255))
        no_text = font_text.render("No", True, (255, 255, 255))

        screen_backup = self.screen.copy()

        dialog_active = True
        result = False

        while dialog_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if yes_button.collidepoint(mouse_pos):
                        result = True
                        dialog_active = False
                    elif no_button.collidepoint(mouse_pos):
                        result = False
                        dialog_active = False

            self.screen.blit(screen_backup, (0, 0))
            self.screen.blit(dialog_bg, (dialog_x, dialog_y))

            self.screen.blit(title_surface, (dialog_x + 200 - title_surface.get_width() // 2, dialog_y + 20))
            self.screen.blit(text_surface, (dialog_x + 200 - text_surface.get_width() // 2, dialog_y + 60))

            pygame.draw.rect(self.screen, (50, 100, 200), yes_button)
            pygame.draw.rect(self.screen, (200, 50, 50), no_button)

            self.screen.blit(yes_text, (yes_button.centerx - yes_text.get_width() // 2,
                                        yes_button.centery - yes_text.get_height() // 2))
            self.screen.blit(no_text, (no_button.centerx - no_text.get_width() // 2,
                                       no_button.centery - no_text.get_height() // 2))

            pygame.display.flip()

        return result

    def show_save_confirmation(self):
        font = pygame.font.SysFont('Arial', 20)
        text_surface = font.render("Game saved successfully!", True, (100, 255, 100))

        bg_width = text_surface.get_width() + 40
        bg_height = 50
        bg_x = (SCREEN_WIDTH - bg_width) // 2
        bg_y = 100

        bg = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg.fill((30, 30, 50, 220))

        self.screen.blit(bg, (bg_x, bg_y))
        self.screen.blit(text_surface, (bg_x + 20, bg_y + 15))
        pygame.display.flip()

        pygame.time.wait(2000)

    def save_game_progress(self):
        save_confirmed = self.show_save_dialog()
        if not save_confirmed:
            return

        original_running_state = self.running
        self.running = False

        game_id = generate_game_id(self.current_level, completed=False)
        self.game_recorder.game_id = game_id

        self.game_recorder.record_event("GAME_SAVE", {
            "level": self.current_level,
            "time_taken": self.time_taken,
            "points": self.points,
            "cells": [self._serialize_cell(cell) for cell in self.cells],
            "bridges": [self._serialize_bridge(bridge) for bridge in self.bridges],
            "balls": [self._serialize_ball(ball) for ball in self.balls],
            "turn_based_mode": self.turn_based_mode,
            "current_player_turn": self.current_player_turn,
            "control_enemy": self.control_enemy
        })

        json_file = self.game_recorder.save_to_json()
        xml_file = self.game_recorder.save_to_xml()

        try:
            mongodb_id = self.game_recorder.save_to_mongodb()
            if mongodb_id:
                logger.info(f"Game history saved to MongoDB with ID: {mongodb_id}")
        except Exception as e:
            logger.error(f"Failed to save to MongoDB: {e}")

        self.show_save_confirmation()

        self.game_started = False
        logger.info("Game saved successfully. Returning to menu.")

    def apply_event(self, event):
        """Apply an event from playback or network to the game state"""
        event_type = event.get("eventType")
        data = event.get("data")
        
        if event_type == "BRIDGE_CREATED":
            source_id = data.get("source_cell_id")
            target_id = data.get("target_cell_id")
            
            source_cell = self.cell_id_map_reverse.get(source_id)
            target_cell = self.cell_id_map_reverse.get(target_id)
            
            if source_cell and target_cell:
                self.create_bridge(source_cell, target_cell)
        
        elif event_type == "BRIDGE_REMOVED":
            source_id = data.get("source_cell_id")
            target_id = data.get("target_cell_id")
            
            source_cell = self.cell_id_map_reverse.get(source_id)
            target_cell = self.cell_id_map_reverse.get(target_id)
            
            if source_cell and target_cell:
                for bridge in self.bridges:
                    if bridge.source_cell == source_cell and bridge.target_cell == target_cell:
                        self.remove_bridge(bridge)
                        break
        
        elif event_type == "CELL_CAPTURED":
            cell_id = data.get("cell_id")
            new_type = data.get("new_type")
            points = data.get("points", 10)
            
            cell = self.cell_id_map_reverse.get(cell_id)
            if cell and new_type:
                cell.cell_type = getattr(CellType, new_type)
                cell.points = points
        
        elif event_type == "CELL_EVOLVED":
            cell_id = data.get("cell_id")
            new_level = data.get("new_level")
            
            cell = self.cell_id_map_reverse.get(cell_id)
            if cell and new_level:
                cell.evolution = EvolutionLevel(new_level)
        
        elif event_type == "CONTROL_SWITCH":
            self.control_enemy = data.get("control_enemy", False)
        
        elif event_type == "TURN_SWITCH":
            self.current_player_turn = data.get("is_player_turn", True)
            self.turn_time_remaining = self.turn_time_max
        
        # Add any other event types your game uses

    def init_network(self):
        if self.game_type == GameType.ONLINE:
            self.network_client = GameNetworkClient(self)
            success = self.network_client.connect(
                self.network_config["ip"],
                self.network_config["port"]
            )
            if not success:
                logger.error("Failed to connect to game server")
                return False
            return True
        return False

    def get_network_events(self):
        if hasattr(self, 'network_client') and self.network_client and self.game_type == GameType.ONLINE:
            return self.network_client.get_pending_events()
        return []

    def send_network_event(self, event_type, data):
        if hasattr(self, 'network_client') and self.network_client and self.game_type == GameType.ONLINE:
            return self.network_client.send_event(event_type, data)
        return False

    def _serialize_cell(self, cell):
        return {
            "id": id(cell),
            "x": cell.x,
            "y": cell.y,
            "type": cell.cell_type.name,
            "shape": cell.shape.name,
            "evolution": cell.evolution.value,
            "points": cell.points,
            "points_to_capture": cell.points_to_capture,
            "enemy_points_to_capture": cell.enemy_points_to_capture
        }

    def _serialize_bridge(self, bridge):
        return {
            "source_cell_id": id(bridge.source_cell),
            "target_cell_id": id(bridge.target_cell),
            "direction": bridge.direction.name,
            "has_reverse": bridge.has_reverse,
            "creation_cost": getattr(bridge, 'creation_cost', 1)
        }

    def _serialize_ball(self, ball):
        return {
            "source_cell_id": id(ball.source_cell),
            "source_x": ball.source_x,
            "source_y": ball.source_y,
            "target_x": ball.target_x,
            "target_y": ball.target_y,
            "x": ball.x,
            "y": ball.y,
            "is_player": ball.is_player,
            "is_support_ball": getattr(ball, 'is_support_ball', False),
            "attack_value": ball.attack_value
        }
    
    def deserialize_cell(self, cell_data):
        cell_type = getattr(self.CellType, cell_data.get("type", "EMPTY"))
        shape = getattr(self.CellShape, cell_data.get("shape", "CIRCLE"))
        evolution = self.EvolutionLevel(cell_data.get("evolution", 1))
        
        cell = self.Cell(
            cell_data.get("x", 0),
            cell_data.get("y", 0),
            cell_type,
            shape,
            evolution
        )
        cell.points = cell_data.get("points", 0)
        return cell

    def deserialize_bridge(self, bridge_data):
        source_id = bridge_data.get("source_cell_id")  # match your serializer field name
        target_id = bridge_data.get("target_cell_id") 
        
        if source_id in self.cell_id_map and target_id in self.cell_id_map:
            source_cell = self.cell_id_map[source_id]
            target_cell = self.cell_id_map[target_id]
            
            bridge = Bridge(source_cell, target_cell)  # Assuming you have a Bridge class
            bridge.creation_cost = bridge_data.get("creation_cost", 1)
            return bridge
        return None

    def deserialize_ball(self, ball_data):
        source_id = ball_data.get("sourceId")
        target_id = ball_data.get("targetId")
        
        source_cell = self.cell_id_map.get(source_id)
        target_cell = self.cell_id_map.get(target_id) if target_id != -1 else None
        
        ball = Ball(
            ball_data.get("x", 0),
            ball_data.get("y", 0),
            ball_data.get("target_x", 0),
            ball_data.get("target_y", 0),
            ball_data.get("attack_value", 1),
            ball_data.get("is_player", True)
        )
        ball.source_cell = source_cell
        ball.target_cell = target_cell
        ball.is_support_ball = ball_data.get("is_support_ball", False)
        return ball


class GameNetworkClient:
    def __init__(self, game):
        self.game = game
        self.socket = None
        self.connected = False
        self.receiver_thread = None
        self.pending_events = []
    
    def connect(self, host='localhost', port=5555):
        """Connect to the game server"""
        try:
            logger.info(f"Creating socket connection to {host}:{port}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # 5 second timeout
            self.socket.connect((host, port))
            self.socket.settimeout(None)  # Reset to blocking mode
            self.connected = True
            logger.info(f"Connected to server at {host}:{port}")
            
            # Start receiver thread
            self.receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receiver_thread.start()
            
            # Send initial role message
            role = "ENEMY" if self.game.control_enemy else "PLAYER"
            initial_msg = json.dumps({"type": "CONNECT", "role": role})
            encrypted_msg = self.encrypt_message(initial_msg)
            self.socket.send(encrypted_msg.encode('utf-8'))
            
            return True
        except socket.error as e:
            logger.error(f"Socket error: {e}")
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def encrypt_message(self, message, key='X'):
        """Encrypt a message using XOR with the given key"""
        return ''.join(chr(ord(c) ^ ord(key)) for c in message)
    
    def decrypt_message(self, message, key='X'):
        """Decrypt a message using XOR with the given key"""
        return ''.join(chr(ord(c) ^ ord(key)) for c in message)
    
    def receive_messages(self):
        """Background thread to receive messages from the server"""
        while self.connected:
            try:
                encrypted_message = self.socket.recv(4096).decode('utf-8')
                if not encrypted_message:
                    logger.info("Server closed connection")
                    self.connected = False
                    break
                
                message = self.decrypt_message(encrypted_message)
                
                try:
                    event = json.loads(message)
                    self.pending_events.append(event)
                    logger.info(f"Received event: {event['type']}")
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {message}")
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                self.connected = False
                break
        
        logger.info("Receiver thread ended")
    
    def get_pending_events(self):
        """Get and clear pending events"""
        events = self.pending_events.copy()
        self.pending_events = []
        return events
    
    def send_event(self, event_type, data):
        """Send an event to the server"""
        if not self.connected:
            return False
        
        try:
            event = {
                "type": event_type,
                "data": data,
                "timestamp": time.time()
            }
            
            json_data = json.dumps(event)
            encrypted_data = self.encrypt_message(json_data)
            self.socket.send(encrypted_data.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Error sending event: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            
def check_saved_games_for_level(level_name):
    saved_games = []

    if os.path.exists("saved_games/json"):
        json_files = [f for f in os.listdir("saved_games/json") if
                      f.startswith(f"{level_name}_") and f.endswith(".json")]
        for file in json_files:
            if "in_progress" in file:
                try:
                    with open(os.path.join("saved_games/json", file), "r") as f:
                        data = json.load(f)
                        timestamp = file.split("_")[1] + "_" + file.split("_")[2]
                        saved_games.append({
                            "file": file,
                            "format": "json",
                            "timestamp": timestamp,
                            "data": data
                        })
                except Exception as e:
                    logger.error(f"Error loading JSON save file {file}: {e}")

    if os.path.exists("saved_games/xml"):
        try:
            import xml.etree.ElementTree as ET
            xml_files = [f for f in os.listdir("saved_games/xml") if
                         f.startswith(f"{level_name}_") and f.endswith(".xml")]
            for file in xml_files:
                if "in_progress" in file:
                    try:
                        tree = ET.parse(os.path.join("saved_games/xml", file))
                        root = tree.getroot()

                        data = {"metadata": {}, "events": []}

                        metadata_elem = root.find("Metadata")
                        if metadata_elem:
                            for child in metadata_elem:
                                data["metadata"][child.tag] = child.text

                        events_elem = root.find("Events")
                        if events_elem:
                            for event_elem in events_elem.findall("Event"):
                                event = {
                                    "timestamp": float(event_elem.get("timestamp")),
                                    "eventType": event_elem.get("type"),
                                    "data": {}
                                }

                                for child in event_elem:
                                    if len(child) > 0:
                                        items = []
                                        for item_elem in child:
                                            if len(item_elem) > 0:
                                                item_dict = {}
                                                for attr in item_elem:
                                                    if attr.tag in ["id", "x", "y", "evolution", "points",
                                                                    "points_to_capture", "enemy_points_to_capture"]:
                                                        try:
                                                            item_dict[attr.tag] = int(attr.text)
                                                        except:
                                                            item_dict[attr.tag] = attr.text
                                                    else:
                                                        item_dict[attr.tag] = attr.text
                                                items.append(item_dict)
                                            else:
                                                items.append(item_elem.text)
                                        event["data"][child.tag] = items
                                    else:
                                        if child.tag in ["points", "time_taken"]:
                                            try:
                                                event["data"][child.tag] = float(child.text)
                                            except:
                                                event["data"][child.tag] = child.text
                                        elif child.tag in ["turn_based_mode", "current_player_turn",
                                                           "control_enemy"]:
                                            event["data"][child.tag] = child.text.lower() == "true"
                                        else:
                                            event["data"][child.tag] = child.text

                                data["events"].append(event)

                        timestamp = file.split("_")[1] + "_" + file.split("_")[2]
                        saved_games.append({
                            "file": file,
                            "format": "xml",
                            "timestamp": timestamp,
                            "data": data
                        })
                    except Exception as e:
                        logger.error(f"Error loading XML save file {file}: {e}")
        except ImportError:
            logger.error("XML parsing not available")

    try:
        import pymongo
        from mongodb_config import DEFAULT_CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME

        client = pymongo.MongoClient(DEFAULT_CONNECTION_STRING, serverSelectionTimeoutMS=2000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        query = {
            "metadata.gameId": {"$regex": f"^{level_name}_.*_in_progress$"}
        }

        mongo_saves = list(collection.find(query).sort("metadata.timestamp", pymongo.DESCENDING))

        for save in mongo_saves:
            save["_id"] = str(save["_id"])

            game_id = save["metadata"].get("gameId", "")
            parts = game_id.split("_")
            if len(parts) >= 3:
                timestamp = parts[1] + "_" + parts[2]
            else:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

            saved_games.append({
                "file": str(save["_id"]),
                "format": "mongodb",
                "timestamp": timestamp,
                "data": save
            })
    except Exception as e:
        logger.error(f"Error checking MongoDB saves: {e}")

    saved_games.sort(key=lambda x: x["timestamp"], reverse=True)

    return saved_games if saved_games else None


def load_game_data(file_path):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        logger.error(f"Game data file not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in game data file: {file_path}")
        return {}


def create_menu(game):
    MENU_BG_COLOR = (20, 20, 40)
    TITLE_COLOR = (220, 220, 255)
    LEVEL_WIDTH = 150
    LEVEL_HEIGHT = 180
    STAR_SIZE = 25
    LEVELS_PER_ROW = 3
    SPACING = 30
    BUTTON_WIDTH = 160
    BUTTON_HEIGHT = 40

    menu_running = True
    clock = pygame.time.Clock()

    star_img = pygame.Surface((STAR_SIZE, STAR_SIZE), pygame.SRCALPHA)
    star_points = []

    for i in range(5):
        angle = math.pi * 2 * i / 5 - math.pi / 2
        star_points.append((STAR_SIZE / 2 + math.cos(angle) * STAR_SIZE / 2,
                            STAR_SIZE / 2 + math.sin(angle) * STAR_SIZE / 2))
        angle += math.pi / 5
        star_points.append((STAR_SIZE / 2 + math.cos(angle) * STAR_SIZE / 4,
                            STAR_SIZE / 2 + math.sin(angle) * STAR_SIZE / 4))
    pygame.draw.polygon(star_img, (255, 255, 0), star_points)

    lock_img = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.rect(lock_img, (150, 150, 150), (15, 20, 20, 20))
    pygame.draw.rect(lock_img, (150, 150, 150), (10, 10, 30, 15))
    pygame.draw.circle(lock_img, (100, 100, 100), (25, 20), 8)

    editor_font = pygame.font.SysFont('Arial', 22, bold=True)
    editor_text = "Level Editor"
    editor_surface = editor_font.render(editor_text, True, (255, 255, 255))

    replay_font = pygame.font.SysFont('Arial', 22, bold=True)
    replay_text = "View Replays"
    replay_surface = replay_font.render(replay_text, True, (255, 255, 255))

    editor_rect = pygame.Rect(SCREEN_WIDTH / 2 - BUTTON_WIDTH - 10, 100, BUTTON_WIDTH, BUTTON_HEIGHT)
    replay_rect = pygame.Rect(SCREEN_WIDTH / 2 + 10, 100, BUTTON_WIDTH, BUTTON_HEIGHT)

    START_Y_LEVELS = 170

    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()

                    if editor_rect.collidepoint(mouse_pos):
                        editor = LevelEditor() #(game)
                        editor.run()
                        pygame.event.clear()
                        game.game_data = load_game_data("game_data.json")
                    elif replay_rect.collidepoint(mouse_pos):
                        if game.show_replay_menu():
                            return True
                        pygame.event.clear()
                    else:
                        level_clicked = check_level_click(mouse_pos, game.game_data, START_Y_LEVELS)
                        if level_clicked:
                            if is_level_unlocked(game.game_data, level_clicked):
                                game.current_level = level_clicked
                                return True

        game.screen.fill(MENU_BG_COLOR)

        title_font = pygame.font.SysFont('Arial', 48, bold=True)
        title_text = "WAR OF CELLS"
        title_surface = title_font.render(title_text, True, TITLE_COLOR)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH / 2, 50))
        game.screen.blit(title_surface, title_rect)

        pygame.draw.rect(game.screen, (100, 100, 200), editor_rect)
        text_rect = editor_surface.get_rect(center=editor_rect.center)
        game.screen.blit(editor_surface, text_rect)

        pygame.draw.rect(game.screen, (100, 150, 100), replay_rect)
        text_rect = replay_surface.get_rect(center=replay_rect.center)
        game.screen.blit(replay_surface, text_rect)

        level_count = len(game.game_data.get("levels", {}))
        start_x = (SCREEN_WIDTH - (LEVELS_PER_ROW * LEVEL_WIDTH + (LEVELS_PER_ROW - 1) * SPACING)) / 2
        start_y = START_Y_LEVELS

        font = pygame.font.SysFont('Arial', 22, bold=True)
        small_font = pygame.font.SysFont('Arial', 14)

        for i, level_name in enumerate(sorted(game.game_data.get("levels", {}).keys())):
            row = i // LEVELS_PER_ROW
            col = i % LEVELS_PER_ROW

            x = start_x + col * (LEVEL_WIDTH + SPACING)
            y = start_y + row * (LEVEL_HEIGHT + SPACING)

            level_info = game.game_data.get("summary", {}).get("levels", {}).get(level_name, {})
            unlocked = is_level_unlocked(game.game_data, level_name)

            level_color = (60, 80, 120) if unlocked else (60, 60, 60)
            pygame.draw.rect(game.screen, level_color, (x, y, LEVEL_WIDTH, LEVEL_HEIGHT))
            pygame.draw.rect(game.screen, (200, 200, 255), (x, y, LEVEL_WIDTH, LEVEL_HEIGHT), 2)

            level_text = f"Level {level_name.replace('level', '')}"
            level_surface = font.render(level_text, True, (255, 255, 255))
            level_rect = level_surface.get_rect(center=(x + LEVEL_WIDTH / 2, y + 25))
            game.screen.blit(level_surface, level_rect)

            if unlocked:
                stars = level_info.get("stars", 0)
                star_y = y + 55
                for s in range(3):
                    star_color = (255, 255, 0) if s < stars else (70, 70, 70)
                    star_x = x + LEVEL_WIDTH / 2 - (STAR_SIZE * 3) / 2 + s * STAR_SIZE
                    pygame.draw.polygon(game.screen, star_color,
                                        [(p[0] + star_x, p[1] + star_y) for p in star_points])

                if "time" in level_info:
                    time_text = f"Time: {level_info['time']}"
                    time_surface = small_font.render(time_text, True, (200, 200, 200))
                    time_rect = time_surface.get_rect(center=(x + LEVEL_WIDTH / 2, y + 90))
                    game.screen.blit(time_surface, time_rect)

                if "score" in level_info:
                    score_text = f"Score: {level_info['score']}"
                    score_surface = small_font.render(score_text, True, (200, 200, 200))
                    score_rect = score_surface.get_rect(center=(x + LEVEL_WIDTH / 2, y + 110))
                    game.screen.blit(score_surface, score_rect)
            else:
                game.screen.blit(lock_img, (x + LEVEL_WIDTH / 2 - 25, y + 60))

        inst_font = pygame.font.SysFont('Arial', 18)
        inst_text = "Click on a level to play. Press ESC to exit."
        inst_surface = inst_font.render(inst_text, True, (180, 180, 180))
        inst_rect = inst_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 40))
        game.screen.blit(inst_surface, inst_rect)

        pygame.display.flip()
        clock.tick(30)

    return False


def check_level_click(mouse_pos, game_data, start_y=170):
    LEVEL_WIDTH = 150
    LEVEL_HEIGHT = 180
    LEVELS_PER_ROW = 3
    SPACING = 30

    level_count = len(game_data.get("levels", {}))
    start_x = (SCREEN_WIDTH - (LEVELS_PER_ROW * LEVEL_WIDTH + (LEVELS_PER_ROW - 1) * SPACING)) / 2

    for i, level_name in enumerate(sorted(game_data.get("levels", {}).keys())):
        row = i // LEVELS_PER_ROW
        col = i % LEVELS_PER_ROW

        x = start_x + col * (LEVEL_WIDTH + SPACING)
        y = start_y + row * (LEVEL_HEIGHT + SPACING)

        if (x <= mouse_pos[0] <= x + LEVEL_WIDTH and
                y <= mouse_pos[1] <= y + LEVEL_HEIGHT):
            return level_name

    return None


def is_level_unlocked(game_data, level_name):
    if level_name == "level1":
        return True

    if level_name.startswith("level"):
        level_num = int(level_name[5:])
        prev_level_name = f"level{level_num - 1}"

        prev_level_stars = game_data.get("summary", {}).get("levels", {}).get(prev_level_name, {}).get("stars", 0)
        return prev_level_stars > 0

    return False


def calculate_stars(points, time_taken):
    if points >= 1500:
        stars = 3
    elif points >= 1000:
        stars = 2
    elif points > 0:
        stars = 1
    else:
        stars = 0

    minutes = time_taken / 60  # time_taken is in seconds
    if minutes > 5:
        stars = max(0, stars - 1)

    return stars


def format_time(seconds):
    # format seconds into MM:SS
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def save_level_stats(game):
    if not game.game_data:
        return

    if "summary" not in game.game_data:
        game.game_data["summary"] = {"total_levels": len(game.game_data.get("levels", {})), "levels": {}}

    if "levels" not in game.game_data["summary"]:
        game.game_data["summary"]["levels"] = {}

    stars = calculate_stars(game.points, game.time_taken)

    game.game_data["summary"]["levels"][game.current_level] = {
        "stars": stars,
        "time": format_time(game.time_taken),
        "score": game.points
    }

    try:
        with open("game_data.json", "w") as file:
            json.dump(game.game_data, file, indent=4)
        logger.info(
            f"Saved stats for {game.current_level}: {stars} stars, time: {format_time(game.time_taken)}, score: {game.points}")
    except Exception as e:
        logger.error(f"Error saving game data: {str(e)}")


def load_level(game, level_name):
    game.cells = []
    game.bridges = []
    game.balls = []
    game.effects = []
    game.selected_cell = None
    game.last_ball_spawn_time = {}

    try:
        if not hasattr(game, 'game_data') or not game.game_data:
            game.game_data = load_game_data("game_data.json")

        if level_name not in game.game_data.get("levels", {}):
            logger.error(f"Level '{level_name}' not found")
            return False

        level_data = game.game_data["levels"][level_name]
        game_map = level_data.get("map", [])
        description = level_data.get("description", {})

        grid_width = SCREEN_WIDTH // len(game_map[0])
        grid_height = SCREEN_HEIGHT // len(game_map)

        type_counters = {cell_type: 0 for cell_type in description}

        for y, row in enumerate(game_map):
            for x, cell_char in enumerate(row):
                if cell_char == '#' or cell_char == ' ':
                    continue

                if cell_char in description:
                    if type_counters[cell_char] < len(description[cell_char]):
                        cell_info = description[cell_char][type_counters[cell_char]]
                        type_counters[cell_char] += 1

                        cell_x = x * grid_width + grid_width // 2
                        cell_y = y * grid_height + grid_height // 2

                        if cell_info["color"] == "blue":
                            cell_type = CellType.PLAYER
                        elif cell_info["color"] == "red":
                            cell_type = CellType.ENEMY
                        else:
                            cell_type = CellType.EMPTY

                        if cell_info["kind"] == "c":
                            shape = CellShape.CIRCLE
                        elif cell_info["kind"] == "t":
                            shape = CellShape.TRIANGLE
                        else:
                            shape = CellShape.RECTANGLE

                        evolution = EvolutionLevel(cell_info["evolution"])

                        new_cell = Cell(cell_x, cell_y, cell_type, shape, evolution)
                        new_cell.points = cell_info["points"]
                        game.cells.append(new_cell)
                    else:
                        logger.warning(f"Too many cells of type {cell_char} in map")

        for cell_type, counter in type_counters.items():
            if counter != len(description[cell_type]):
                logger.warning(
                    f"Not all cells of type {cell_type} were placed. Used {counter}/{len(description[cell_type])}")

        logger.info(f"Loaded level: {level_name}")
        return True

    except Exception as e:
        logger.error(f"Error loading level {level_name}: {str(e)}")
        return False


def suggest_moves(game, for_player=True):
    suggestions = []

    if for_player:
        my_cells = [cell for cell in game.cells if cell.cell_type == CellType.PLAYER]
        enemy_cells = [cell for cell in game.cells if cell.cell_type == CellType.ENEMY]
    else:
        my_cells = [cell for cell in game.cells if cell.cell_type == CellType.ENEMY]
        enemy_cells = [cell for cell in game.cells if cell.cell_type == CellType.PLAYER]

    empty_cells = [cell for cell in game.cells if cell.cell_type == CellType.EMPTY]

    #print(f"Generating suggestions for {'player' if for_player else 'AI'}")
    #print(f"My cells: {len(my_cells)}, Enemy cells: {len(enemy_cells)}, Empty cells: {len(empty_cells)}")

    # 1. Find cells under attack
    under_attack = []
    for bridge in game.bridges:
        if bridge.target_cell in my_cells and bridge.source_cell in enemy_cells:
            under_attack.append(bridge.target_cell)

    # 2. Counterattack enemies attacking you
    for attacked_cell in under_attack:
        for my_cell in my_cells:
            if my_cell != attacked_cell:
                for bridge in game.bridges:
                    if bridge.target_cell == attacked_cell and bridge.source_cell in enemy_cells:
                        attacker = bridge.source_cell
                        if can_create_bridge(game, my_cell, attacker):
                            suggestions.append({
                                'type': 'attack',
                                'source': my_cell,
                                'target': attacker,
                                'score': 100,
                                'description': f"Counter-attack enemy cell that's attacking you"
                            })

    # 3. Capture closest empty cells
    for my_cell in my_cells:
        if can_create_more_bridges(game, my_cell):
            #sort by distance, empty cells
            empty_cells_by_distance = sorted(empty_cells,
                                             key=lambda e: game.calculate_distance(my_cell, e))

            #take into consideration 3 closest empty cells
            for empty_cell in empty_cells_by_distance[:3]:
                if can_create_bridge(game, my_cell, empty_cell):
                    suggestions.append({
                        'type': 'capture',
                        'source': my_cell,
                        'target': empty_cell,
                        'score': 80,
                        'description': f"Capture empty cell"
                    })

    # 4. Attack enemy cells - prioritize cells with better attack multiplier
    attacking_cells = []
    for my_cell in my_cells:
        if can_create_more_bridges(game, my_cell):
            multiplier = 1
            if my_cell.shape == CellShape.TRIANGLE:
                multiplier = 2
            elif my_cell.shape == CellShape.RECTANGLE:
                multiplier = 3

            if multiplier > 1:
                weak_enemies = sorted(enemy_cells, key=lambda e: e.points)

                for enemy in weak_enemies[:2]:
                    if can_create_bridge(game, my_cell, enemy):
                        suggestions.append({
                            'type': 'attack',
                            'source': my_cell,
                            'target': enemy,
                            'score': 70 + (multiplier * 10),
                            'description': f"Attack enemy cell with {multiplier}x multiplier"
                        })

    # 5. Support cells that are under attack
    for attacked_cell in under_attack:
        for my_cell in my_cells:
            if my_cell != attacked_cell and can_create_bridge(game, my_cell, attacked_cell):
                suggestions.append({
                    'type': 'support',
                    'source': my_cell,
                    'target': attacked_cell,
                    'score': 90,
                    'description': f"Support your cell under attack"
                })

    suggestions.sort(key=lambda x: x['score'], reverse=True)

    #logger.info(f"Generated {len(suggestions)} suggestions")
    for i, s in enumerate(suggestions[:3]):
        logger.info(f"  {i + 1}: {s['description']} (Score: {s['score']})")

    return suggestions[:3]


def can_create_more_bridges(game, cell):
    return game.count_outgoing_bridges(cell) < cell.evolution.value


def can_create_bridge(game, source, target):
    for bridge in game.bridges:
        if bridge.source_cell == source and bridge.target_cell == target:
            return False

    if not can_create_more_bridges(game, source):
        return False

    distance = game.calculate_distance(source, target)
    bridge_cost = max(1, int(distance / 30))

    return source.points >= bridge_cost


def execute_ai_move(game, is_suggestion=False):
    suggestions = suggest_moves(game, for_player=is_suggestion)

    if not suggestions:
        if game.turn_based_mode and not game.current_player_turn:
            game.move_made_this_turn = True
        return

    best_move = suggestions[0]

    if is_suggestion:
        game.suggestions = suggestions
        return

    if best_move['type'] in ['attack', 'capture', 'support']:
        game.create_bridge(best_move['source'], best_move['target'])
        logger.info(
            f"AI executed {best_move['type']} move: {best_move['source'].x},{best_move['source'].y} -> {best_move['target'].x},{best_move['target'].y}")

    elif best_move['type'] == 'remove':
        game.remove_bridge(best_move['bridge'])
        logger.info(
            f"AI removed bridge: {best_move['bridge'].source_cell.x},{best_move['bridge'].source_cell.y} -> {best_move['bridge'].target_cell.x},{best_move['bridge'].target_cell.y}")

    if game.turn_based_mode and not game.current_player_turn:
        game.move_made_this_turn = True


def draw_suggestions(game, screen):
    if not game.suggestions or not game.show_suggestions:
        #logger.info("Not showing suggestions: empty suggestions or show_suggestions is False")
        return

    print(f"Drawing {len(game.suggestions)} suggestions")

    font = pygame.font.SysFont('Arial', 16, bold=True)
    highlight_color = (255, 255, 0)

    for i, suggestion in enumerate(game.suggestions):
        if suggestion.get('type') in ['attack', 'capture', 'support']:
            source = suggestion['source']
            target = suggestion['target']

            pygame.draw.line(screen, highlight_color,
                             (source.x, source.y),
                             (target.x, target.y), 6)

            pygame.draw.circle(screen, highlight_color, (source.x, source.y), 15, 4)
            pygame.draw.circle(screen, highlight_color, (target.x, target.y), 15, 4)

            rank_text = str(i + 1)
            text_surf = font.render(rank_text, True, (0, 0, 0))

            circle_radius = 15
            circle_surf = pygame.Surface((circle_radius * 2, circle_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, highlight_color, (circle_radius, circle_radius), circle_radius)

            text_rect = text_surf.get_rect(center=(circle_radius, circle_radius))
            circle_surf.blit(text_surf, text_rect)

            mid_x = (source.x + target.x) // 2
            mid_y = (source.y + target.y) // 2

            screen.blit(circle_surf, (mid_x - circle_radius, mid_y - circle_radius))

        elif suggestion.get('type') == 'remove':
            bridge = suggestion['bridge']
            source_x, source_y = bridge.source_cell.x, bridge.source_cell.y
            target_x, target_y = bridge.target_cell.x, bridge.target_cell.y

            mid_x = (source_x + target_x) // 2
            mid_y = (source_y + target_y) // 2

            size = 20

            pygame.draw.line(screen, highlight_color,
                             (mid_x - size, mid_y - size),
                             (mid_x + size, mid_y + size), 6)
            pygame.draw.line(screen, highlight_color,
                             (mid_x - size, mid_y + size),
                             (mid_x + size, mid_y - size), 6)

            pygame.draw.circle(screen, highlight_color, (mid_x, mid_y), size + 5, 3)

            rank_text = str(i + 1)
            text_surf = font.render(rank_text, True, (0, 0, 0))

            circle_radius = 15
            circle_surf = pygame.Surface((circle_radius * 2, circle_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, highlight_color, (circle_radius, circle_radius), circle_radius)

            text_rect = text_surf.get_rect(center=(circle_radius, circle_radius))
            circle_surf.blit(text_surf, text_rect)

            screen.blit(circle_surf, (mid_x - circle_radius, mid_y - size - circle_radius * 2))


def get_saved_games_from_mongodb(limit=20):
    try:
        import pymongo
        from mongodb_config import DEFAULT_CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME
    except ImportError:
        logger.error("MongoDB support not available. Install pymongo package.")
        return []

    try:
        client = pymongo.MongoClient(DEFAULT_CONNECTION_STRING, serverSelectionTimeoutMS=2000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        games = list(collection.find({},
                                     {"metadata": 1, "timestamp": 1})
                     .sort("timestamp", pymongo.DESCENDING)
                     .limit(limit))

        return games
    except Exception as e:
        logger.error(f"Error fetching games from MongoDB: {e}")
        return []


def safe_mongodb_operation(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"MongoDB operation failed: {e}")
            return None if not kwargs.get('default') else kwargs.get('default')
    return wrapper


if __name__ == "__main__":
    game = Game()
    game.run()
