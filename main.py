import pygame
import sys
import math
import random
import colorsys
from enum import Enum
from typing import List, Dict, Tuple, Optional
import logging
import json

# Initialize pygame
pygame.init()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('WarOfCEllsGame')

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BACKGROUND_COLOR = (10, 10, 20)  # Darker background

# Cell properties
CELL_RADIUS = 30
POINT_GROWTH_INTERVAL = 3000  # milliseconds
BALL_SPEED = 2
BALL_RADIUS = 5
BRIDGE_WIDTH = 3

# Colors
PLAYER_COLOR = (50, 100, 255)  # Blue
ENEMY_COLOR = (255, 50, 50)  # Red
EMPTY_COLOR = (50, 50, 50)  # Dark Gray
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# Enums
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


class Cell:
    def __init__(self, x: int, y: int, cell_type: CellType, shape: CellShape = CellShape.CIRCLE,
                 evolution: EvolutionLevel = EvolutionLevel.LEVEL_1):
        self.x = x
        self.y = y
        self.cell_type = cell_type
        self.shape = shape
        self.evolution = evolution
        self.points = 20 if cell_type != CellType.EMPTY else 0
        self.required_points = 6  # Points needed to capture an empty cell
        self.points_to_capture = 0  # Current points accumulated by player
        self.enemy_points_to_capture = 0  # Current points accumulated by enemy
        self.last_growth_time = pygame.time.get_ticks()
        self.outgoing_bridges = []
        self.incoming_bridges = []
        self.pulse_value = random.random() * math.pi * 2  # Random start for pulsing effect
        self.rotation = 0  # For rotation animations

    def get_color(self):
        if self.cell_type == CellType.PLAYER:
            return PLAYER_COLOR
        elif self.cell_type == CellType.ENEMY:
            return ENEMY_COLOR
        else:
            return EMPTY_COLOR

    def get_glow_color(self):
        """Return a lighter version of the cell color for glow effects"""
        base_color = self.get_color()
        # Make a lighter version
        r = min(255, base_color[0] + 100)
        g = min(255, base_color[1] + 100)
        b = min(255, base_color[2] + 100)
        return (r, g, b)

    def update(self, current_time):
        # Grow points over time for non-empty cells
        if self.cell_type != CellType.EMPTY:
            if current_time - self.last_growth_time >= POINT_GROWTH_INTERVAL:
                self.points += 1
                self.last_growth_time = current_time

        # Update animation values
        self.pulse_value = (self.pulse_value + 0.05) % (math.pi * 2)
        self.rotation = (self.rotation + 0.5) % 360


    def draw(self, screen):
        # Calculate pulse effect (0-1 range)
        pulse = (math.sin(self.pulse_value) + 1) / 2

        # Base glow effect
        glow_radius = CELL_RADIUS + 5 + pulse * 3
        glow_color = self.get_glow_color()
        glow_alpha = 150 + int(pulse * 60)

        # Create a surface for the glow with alpha
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)

        # Draw the glow
        pygame.draw.circle(glow_surface, (*glow_color, glow_alpha),
                           (glow_radius, glow_radius), glow_radius)

        # Blit the glow surface
        screen.blit(glow_surface, (self.x - glow_radius, self.y - glow_radius))

        # Draw cell based on shape with more interesting styling
        if self.shape == CellShape.CIRCLE:
            # Main circle
            pygame.draw.circle(screen, self.get_color(), (self.x, self.y), CELL_RADIUS)

            # Inner circle highlight
            highlight_radius = CELL_RADIUS * 0.7
            highlight_color = (min(255, self.get_color()[0] + 50),
                               min(255, self.get_color()[1] + 50),
                               min(255, self.get_color()[2] + 50))
            pygame.draw.circle(screen, highlight_color,
                               (self.x - CELL_RADIUS * 0.2, self.y - CELL_RADIUS * 0.2),
                               highlight_radius)

            # Border
            pygame.draw.circle(screen, BLACK, (self.x, self.y), CELL_RADIUS, 2)

        elif self.shape == CellShape.TRIANGLE:
            # Rotate the triangle based on animation
            angle_rad = math.radians(self.rotation)

            # Calculate triangle points with rotation
            points = []
            for i in range(3):
                angle = angle_rad + i * 2 * math.pi / 3
                px = self.x + math.sin(angle) * CELL_RADIUS
                py = self.y + math.cos(angle) * CELL_RADIUS
                points.append((px, py))

            # Main triangle
            pygame.draw.polygon(screen, self.get_color(), points)

            # Inner triangle highlight
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

            # Border
            pygame.draw.polygon(screen, BLACK, points, 2)

        elif self.shape == CellShape.RECTANGLE:
            # Main rectangle with slight rotation
            rect_surface = pygame.Surface((CELL_RADIUS * 2, CELL_RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.rect(rect_surface, self.get_color(),
                             (0, 0, CELL_RADIUS * 2, CELL_RADIUS * 2))

            # Inner rectangle highlight
            highlight_color = (min(255, self.get_color()[0] + 50),
                               min(255, self.get_color()[1] + 50),
                               min(255, self.get_color()[2] + 50))
            pygame.draw.rect(rect_surface, highlight_color,
                             (CELL_RADIUS * 0.4, CELL_RADIUS * 0.4,
                              CELL_RADIUS * 1.2, CELL_RADIUS * 1.2))

            # Border
            pygame.draw.rect(rect_surface, BLACK, (0, 0, CELL_RADIUS * 2, CELL_RADIUS * 2), 2)

            # Rotate and blit the rectangle
            if self.cell_type != CellType.EMPTY:  # Only rotate non-empty cells
                rotated = pygame.transform.rotate(rect_surface, self.rotation / 4)  # Slower rotation
                rotated_rect = rotated.get_rect(center=(self.x, self.y))
                screen.blit(rotated, rotated_rect)
            else:
                rect = pygame.Rect(self.x - CELL_RADIUS, self.y - CELL_RADIUS,
                                   CELL_RADIUS * 2, CELL_RADIUS * 2)
                pygame.draw.rect(screen, self.get_color(), rect)
                pygame.draw.rect(screen, BLACK, rect, 2)

        # Draw points or capture progress for the cell
        font = pygame.font.SysFont('Arial', 14)

        if self.cell_type == CellType.EMPTY:
            # Draw gradient to show which side is dominating
            domination_ratio = 0
            total_points = self.points_to_capture + self.enemy_points_to_capture

            if total_points > 0:
                domination_ratio = self.points_to_capture / total_points

                # Draw more impressive gradient indicator with multiple rings
                base_gradient_radius = CELL_RADIUS + 5
                for i in range(3):  # Draw multiple rings
                    gradient_radius = base_gradient_radius + i * 3
                    thickness = 3 - i * 0.5  # Thinner outer rings

                    # Calculate pulse effect based on current time
                    pulse = (math.sin(self.pulse_value + i) + 1) / 4 + 0.9  # 0.9-1.15 range
                    gradient_radius *= pulse

                    # Player's portion of the ring
                    if domination_ratio > 0:
                        start_angle = 0
                        end_angle = domination_ratio * 2 * math.pi
                        # Use a gradient of blues
                        player_color = (
                            PLAYER_COLOR[0],
                            min(255, PLAYER_COLOR[1] + i * 20),
                            min(255, PLAYER_COLOR[2] + i * 10)
                        )
                        pygame.draw.arc(screen, player_color,
                                        (self.x - gradient_radius, self.y - gradient_radius,
                                         gradient_radius * 2, gradient_radius * 2),
                                        start_angle, end_angle, int(thickness))

                    # Enemy's portion of the ring
                    if domination_ratio < 1:
                        start_angle = domination_ratio * 2 * math.pi
                        end_angle = 2 * math.pi
                        # Use a gradient of reds
                        enemy_color = (
                            min(255, ENEMY_COLOR[0] + i * 10),
                            ENEMY_COLOR[1],
                            ENEMY_COLOR[2]
                        )
                        pygame.draw.arc(screen, enemy_color,
                                        (self.x - gradient_radius, self.y - gradient_radius,
                                         gradient_radius * 2, gradient_radius * 2),
                                        start_angle, end_angle, int(thickness))

            # Draw progress text
            progress_text = f"{self.points_to_capture - self.enemy_points_to_capture}/{self.required_points}"
            text_surface = font.render(progress_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(self.x, self.y))
            screen.blit(text_surface, text_rect)
        else:
            # Draw points for player/enemy cells
            points_text = str(self.points)
            text_surface = font.render(points_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(self.x, self.y))
            screen.blit(text_surface, text_rect)

            # Draw evolution level
            evo_text = f"E{self.evolution.value}"
            if self.evolution.value == 1:
                evo_color = (220, 220, 220)  # White-ish for level 1
            elif self.evolution.value == 2:
                evo_color = (220, 220, 100)  # Yellowish for level 2
            else:
                evo_color = (220, 150, 50)  # Orange for level 3
            evo_surface = font.render(evo_text, True, evo_color)
            evo_rect = evo_surface.get_rect(center=(self.x, self.y + CELL_RADIUS + 10))
            screen.blit(evo_surface, evo_rect)

    def contains_point(self, pos_x, pos_y):
        """Check if the given point is inside the cell"""
        distance = math.sqrt((pos_x - self.x) ** 2 + (pos_y - self.y) ** 2)
        return distance <= CELL_RADIUS

    def try_capture(self, points_gained, is_player):
        """Try to capture an empty cell with points"""
        if self.cell_type != CellType.EMPTY:
            return False

        if is_player:
            self.points_to_capture += points_gained
        else:
            self.enemy_points_to_capture += points_gained

        # Calculate net points (player points - enemy points)
        net_points = self.points_to_capture - self.enemy_points_to_capture

        # Check if the cell can be captured
        if abs(net_points) >= self.required_points:
            if net_points > 0:
                self.cell_type = CellType.PLAYER
                self.points = 20
                logger.info(f"Player captured cell at ({self.x}, {self.y})")
            else:
                self.cell_type = CellType.ENEMY
                self.points = 20
                logger.info(f"Enemy captured cell at ({self.x}, {self.y})")

            # Reset capture points
            self.points_to_capture = 0
            self.enemy_points_to_capture = 0
            return True

        return False

    def get_attack_multiplier(self):
        """Return the attack multiplier based on cell shape"""
        if self.shape == CellShape.TRIANGLE:
            return 2  # Triangle has 2x attack
        elif self.shape == CellShape.RECTANGLE:
            return 3  # Rectangle has 3x attack
        else:
            return 1  # Circle has normal attack


class Ball:
    def __init__(self, source_cell, target_cell, is_player):
        self.source_x = source_cell.x
        self.source_y = source_cell.y
        self.target_x = target_cell.x
        self.target_y = target_cell.y
        self.is_player = is_player
        self.color = PLAYER_COLOR if is_player else ENEMY_COLOR

        # Calculate normalized direction vector
        dx = self.target_x - self.source_x
        dy = self.target_y - self.source_y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        self.direction_x = dx / distance if distance > 0 else 0
        self.direction_y = dy / distance if distance > 0 else 0

        # Set initial position slightly away from the source cell
        offset = CELL_RADIUS + 5
        self.x = self.source_x + self.direction_x * offset
        self.y = self.source_y + self.direction_y * offset

        # Set speed based on evolution level
        self.speed = BALL_SPEED
        self.trail = []  # For trail effect
        self.age = 0  # For animation effects
        self.attack_value = source_cell.get_attack_multiplier()

    def update(self):
        # Add current position to trail before moving
        self.trail.append((self.x, self.y))

        # Keep trail at a reasonable length
        if len(self.trail) > 10:
            self.trail.pop(0)

        # Move ball
        self.x += self.direction_x * self.speed
        self.y += self.direction_y * self.speed
        self.age += 1

    def draw(self, screen):
        # Draw trail with fading effect
        for i, pos in enumerate(self.trail):
            # Calculate alpha based on position in trail (older = more transparent)
            alpha = int(255 * (i / len(self.trail)) * 0.6)
            # Calculate smaller radius for trail points
            trail_radius = BALL_RADIUS * (i / len(self.trail)) * 0.8

            # Create a surface with alpha for the trail point
            trail_surface = pygame.Surface((int(trail_radius * 2), int(trail_radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, (*self.color, alpha),
                               (int(trail_radius), int(trail_radius)), int(trail_radius))

            # Blit the trail surface
            screen.blit(trail_surface,
                        (int(pos[0] - trail_radius), int(pos[1] - trail_radius)))

        # Draw the main ball with a pulsing effect
        pulse = (math.sin(self.age * 0.2) + 1) / 4 + 0.75  # 0.75-1.25 range

        # Main ball
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)),
                           int(BALL_RADIUS * pulse))

        # Highlight on the ball
        highlight_color = (min(255, self.color[0] + 100),
                           min(255, self.color[1] + 100),
                           min(255, self.color[2] + 100))
        highlight_pos = (int(self.x - BALL_RADIUS * 0.3), int(self.y - BALL_RADIUS * 0.3))
        highlight_radius = BALL_RADIUS * 0.4 * pulse
        pygame.draw.circle(screen, highlight_color, highlight_pos, int(highlight_radius))

    def reached_target(self, target_cell):
        # Check if ball has reached the target cell
        distance = math.sqrt((self.x - target_cell.x) ** 2 + (self.y - target_cell.y) ** 2)
        return distance <= CELL_RADIUS

    def check_collision(self, other_ball):
        """Check if this ball collides with another ball"""
        if other_ball.is_player == self.is_player:
            return False  # Balls of same color don't collide

        distance = math.sqrt((self.x - other_ball.x) ** 2 + (self.y - other_ball.y) ** 2)
        return distance <= BALL_RADIUS * 2


class Bridge:
    def __init__(self, source_cell, target_cell):
        self.source_cell = source_cell
        self.target_cell = target_cell
        self.direction = BridgeDirection.ONE_WAY  # Always start with one-way bridges
        self.has_reverse = False  # Flag to track if there's a reverse bridge
        self.particles = []  # For energy particles effect
        self.animation_offset = random.random() * math.pi * 2  # Random start for animations

    def update(self):
        # Update animation offset
        self.animation_offset = (self.animation_offset + 0.03) % (math.pi * 2)

        # Update particles
        if random.random() < 0.3:  # 30% chance each frame to add a particle
            self.add_particle()

        # Move particles along the bridge
        for particle in self.particles:
            particle['progress'] += 0.01

        # Remove particles that have completed their journey
        self.particles = [p for p in self.particles if p['progress'] <= 1.0]

    def add_particle(self):
        # Add energy particle flowing along the bridge
        is_forward = True
        if self.direction == BridgeDirection.TWO_WAY and random.random() < 0.5:
            is_forward = False

        # Determine color based on source/target cells
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

        # Add slight variation to color
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

        # Draw an energy bridge instead of a simple line
        dx = target_x - source_x
        dy = target_y - source_y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Calculate normalized perpendicular vector for the wave effect
        if distance > 0:
            perp_x, perp_y = -dy / distance, dx / distance
        else:
            perp_x, perp_y = 0, 0

        # Create points for a wavy line effect
        num_segments = max(10, int(distance / 20))
        points = []

        for i in range(num_segments + 1):
            # Position along the line
            t = i / num_segments
            pos_x = source_x + dx * t
            pos_y = source_y + dy * t

            # Add wave effect
            wave_amplitude = 2.0
            wave = math.sin(t * 10 + self.animation_offset) * wave_amplitude
            pos_x += perp_x * wave
            pos_y += perp_y * wave

            points.append((pos_x, pos_y))

        # Draw the wavy line with a gradient
        if len(points) >= 2:
            for i in range(len(points) - 1):
                t = i / (len(points) - 1)
                # Blend colors based on the cells
                if self.source_cell.cell_type != CellType.EMPTY and self.target_cell.cell_type != CellType.EMPTY:
                    if self.source_cell.cell_type == self.target_cell.cell_type:
                        # Same color, uniform line
                        color = self.source_cell.get_color()
                    else:
                        # Different colors, blend
                        src_color = self.source_cell.get_color()
                        tgt_color = self.target_cell.get_color()
                        color = (
                            int(src_color[0] * (1 - t) + tgt_color[0] * t),
                            int(src_color[1] * (1 - t) + tgt_color[1] * t),
                            int(src_color[2] * (1 - t) + tgt_color[2] * t)
                        )
                else:
                    # If either end is empty, use white with alpha
                    color = WHITE

                # Draw segment
                pygame.draw.line(screen, color, points[i], points[i + 1], BRIDGE_WIDTH)

        # Draw particles along the bridge
        for particle in self.particles:
            t = particle['progress']
            if not particle['is_forward']:
                t = 1.0 - t

            # Position along the bridge with wave effect
            pos_x = source_x + dx * t
            pos_y = source_y + dy * t

            wave_amplitude = 2.0
            wave = math.sin(t * 10 + self.animation_offset) * wave_amplitude
            pos_x += perp_x * wave
            pos_y += perp_y * wave

            # Draw particle glow
            glow_surface = pygame.Surface((int(particle['size'] * 4), int(particle['size'] * 4)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*particle['color'], 150),
                               (int(particle['size'] * 2), int(particle['size'] * 2)),
                               int(particle['size'] * 2))
            screen.blit(glow_surface,
                        (int(pos_x - particle['size'] * 2), int(pos_y - particle['size'] * 2)))

            # Draw particle center
            pygame.draw.circle(screen, particle['color'],
                               (int(pos_x), int(pos_y)),
                               int(particle['size']))

        # Draw direction indicators
        if self.direction == BridgeDirection.ONE_WAY:
            # Draw arrow from source to target
            self.draw_arrow(screen, (source_x, source_y), (target_x, target_y), WHITE)
        else:
            # Draw arrows both ways
            midpoint_x = (source_x + target_x) / 2
            midpoint_y = (source_y + target_y) / 2

            # Draw half-arrows
            self.draw_arrow(screen, (source_x, source_y), (midpoint_x, midpoint_y), WHITE)
            self.draw_arrow(screen, (target_x, target_y), (midpoint_x, midpoint_y), WHITE)

    def draw_arrow(self, screen, start, end, color):
        # Calculate direction vector
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance == 0:
            return

        # Normalize
        dx, dy = dx / distance, dy / distance

        # Calculate arrow head position (80% along the line)
        arrow_pos_x = start[0] + dx * distance * 0.8
        arrow_pos_y = start[1] + dy * distance * 0.8

        # Calculate perpendicular vector
        perpendicular_x = -dy
        perpendicular_y = dx

        # Create arrow head points
        arrow_head_size = 8
        point1 = (arrow_pos_x + perpendicular_x * arrow_head_size - dx * arrow_head_size,
                  arrow_pos_y + perpendicular_y * arrow_head_size - dy * arrow_head_size)
        point2 = (arrow_pos_x - perpendicular_x * arrow_head_size - dx * arrow_head_size,
                  arrow_pos_y - perpendicular_y * arrow_head_size - dy * arrow_head_size)

        # Draw arrow head
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
        self.effects = []  # For visual effects

        self.selected_cell = None
        self.last_ball_spawn_time = {}  # Track when balls were last spawned for each bridge

        self.control_enemy = False
        self.show_context_menu = False
        self.context_menu_cell = None
        self.context_menu_options = ["Remove All Bridges"]

        # Add level-related attributes
        self.running = True
        self.game_started = False
        self.game_over_state = False

        # Level tracking
        self.current_level = "level1"
        self.points = 0
        self.time_taken = 0
        self.start_time = 0

        # Load game data
        self.game_data = load_game_data("game_data.json")

        # Initialize the menu
        self.show_menu()

        # Load the first level
        #load_level(self, self.current_level)

        # Initialize the game board
        #self.initialize_board()

    def show_menu(self):
        """Show the level selection menu"""
        # If the menu returns True, a level was selected
        if create_menu(self):
            self.start_game()
        else:
            self.running = False

    def start_game(self):
        """Start the game with the current level"""
        # Load the selected level
        load_level(self, self.current_level)

        # Reset game state
        self.game_started = True
        self.game_over_state = False
        self.points = 0
        self.time_taken = 0
        self.start_time = pygame.time.get_ticks() / 1000  # Start time in seconds

        logger.info(f"Starting game with level: {self.current_level}")

    def initialize_board(self):
        # Create initial cells
        # Player's starting cell
        player_cell = Cell(200, 300, CellType.PLAYER, CellShape.CIRCLE, EvolutionLevel.LEVEL_1)
        self.cells.append(player_cell)

        # Enemy's starting cell
        enemy_cell = Cell(600, 300, CellType.ENEMY, CellShape.CIRCLE, EvolutionLevel.LEVEL_1)
        self.cells.append(enemy_cell)

        # Add some empty cells
        """
        for _ in range(8):
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = random.randint(100, SCREEN_HEIGHT - 100)
            shape = random.choice(list(CellShape))
            empty_cell = Cell(x, y, CellType.EMPTY, shape)
            self.cells.append(empty_cell)
        """

    def create_collision_effect(self, x, y):
        """Create a visual effect for ball collisions"""
        # Add several particles that expand outward
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
        """Create a visual effect for ball impact on cells"""
        color = PLAYER_COLOR if is_player else ENEMY_COLOR

        # Make color slightly brighter
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
            'lifetime': 20,  # frames
            'size': 1.0  # will grow and fade
        }

        self.effects.append(effect)

    def update_effects(self):
        """Update all visual effects"""
        effects_to_remove = []

        for effect in self.effects:
            effect['age'] += 1

            # Check if effect has expired
            if effect['age'] >= effect['lifetime']:
                effects_to_remove.append(effect)
                continue

            # Update based on effect type
            if effect['type'] == 'collision':
                # Update particle positions
                for particle in effect['particles']:
                    particle['dx'] *= 0.95  # Slow down
                    particle['dy'] *= 0.95
                    particle['size'] *= 0.9  # Shrink

            elif effect['type'] == 'impact':
                # Grow then shrink
                progress = effect['age'] / effect['lifetime']
                if progress < 0.3:
                    effect['size'] = 1.0 + progress * 5  # Grow to 2.5x
                else:
                    effect['size'] = 2.5 - (progress - 0.3) * 3  # Shrink to 0

        # Remove expired effects
        for effect in effects_to_remove:
            if effect in self.effects:
                self.effects.remove(effect)

    def update_evolution_based_on_points(self, cell):
        """Update a cell's evolution level based on its points"""
        old_evolution = cell.evolution.value

        # Determine evolution level based on points
        if cell.points < 15:
            new_evolution = EvolutionLevel.LEVEL_1
        elif cell.points < 35:
            new_evolution = EvolutionLevel.LEVEL_2
        else:
            new_evolution = EvolutionLevel.LEVEL_3

        # Update if changed
        if new_evolution.value != old_evolution:
            cell.evolution = new_evolution
            logger.info(f"Cell at ({cell.x}, {cell.y}) evolved to level {new_evolution.value}")

            # Visual feedback for evolution change
            if cell.cell_type == CellType.PLAYER:
                self.create_impact_effect(cell.x, cell.y, True)
            else:
                self.create_impact_effect(cell.x, cell.y, False)

    def next_level(self):
        """Load the next level"""
        if not self.game_data:
            return False

        # Get current level number
        if self.current_level.startswith("level"):
            level_num = int(self.current_level[5:])
            next_level_name = f"level{level_num + 1}"

            if next_level_name in self.game_data.get("levels", {}):
                self.current_level = next_level_name
                return load_level(self, self.current_level)

        return False

    def draw_effects(self, screen):
        """Draw all visual effects"""
        for effect in self.effects:
            if effect['type'] == 'collision':
                # Draw expanding particles
                for particle in effect['particles']:
                    # Calculate position
                    px = effect['x'] + particle['dx'] * effect['age']
                    py = effect['y'] + particle['dy'] * effect['age']

                    # Calculate alpha (fade out)
                    alpha = int(255 * (1 - effect['age'] / effect['lifetime']))

                    # Draw particle
                    particle_surface = pygame.Surface((int(particle['size'] * 2), int(particle['size'] * 2)),
                                                      pygame.SRCALPHA)
                    pygame.draw.circle(particle_surface, (*particle['color'], alpha),
                                       (int(particle['size']), int(particle['size'])),
                                       int(particle['size']))
                    screen.blit(particle_surface, (int(px - particle['size']), int(py - particle['size'])))

            elif effect['type'] == 'impact':
                # Draw expanding/contracting ring
                alpha = int(255 * (1 - effect['age'] / effect['lifetime']))
                size = CELL_RADIUS * effect['size']

                ring_surface = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(ring_surface, (*effect['color'], alpha),
                                   (int(size), int(size)), int(size), max(1, int(size / 10)))
                screen.blit(ring_surface, (int(effect['x'] - size), int(effect['y'] - size)))

    def draw_background_gradient(self):
        # Create a background with a subtle gradient
        gradient_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        for y in range(SCREEN_HEIGHT):
            # Calculate gradient color (dark blue to slightly lighter blue)
            ratio = y / SCREEN_HEIGHT
            r = int(10 + 20 * ratio)
            g = int(10 + 30 * ratio)
            b = int(20 + 40 * ratio)
            color = (r, g, b)

            # Draw horizontal line with this color
            pygame.draw.line(gradient_surface, color, (0, y), (SCREEN_WIDTH, y))

        # Add some subtle "stars" or points of light
        for _ in range(100):
            x = random.randint(0, SCREEN_WIDTH - 1)
            y = random.randint(0, SCREEN_HEIGHT - 1)
            brightness = random.randint(100, 200)
            size = random.randint(1, 3)
            color = (brightness, brightness, brightness)
            pygame.draw.circle(gradient_surface, color, (x, y), size)

        return gradient_surface

    def calculate_distance(self, cell1, cell2):
        """Calculate Euclidean distance between two cells"""
        return math.sqrt((cell1.x - cell2.x) ** 2 + (cell1.y - cell2.y) ** 2)

    def get_bridge_at_position(self, x, y, threshold=10):
        """Find a bridge close to the given position"""
        for bridge in self.bridges:
            # Get bridge start and end points
            start_x, start_y = bridge.source_cell.x, bridge.source_cell.y
            end_x, end_y = bridge.target_cell.x, bridge.target_cell.y

            # Calculate distance from point to line segment
            # Using the formula for point-line distance
            line_length = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
            if line_length == 0:
                continue

            # Calculate perpendicular distance to line
            u = ((x - start_x) * (end_x - start_x) + (y - start_y) * (end_y - start_y)) / (line_length ** 2)

            # Check if projection is on the line segment
            if 0 <= u <= 1:
                # Calculate closest point on line
                closest_x = start_x + u * (end_x - start_x)
                closest_y = start_y + u * (end_y - start_y)

                # Check if close enough
                dist = math.sqrt((x - closest_x) ** 2 + (y - closest_y) ** 2)
                if dist <= threshold:
                    # Calculate which end is closer for refund
                    dist_to_start = math.sqrt((x - start_x) ** 2 + (y - start_y) ** 2)
                    dist_to_end = math.sqrt((x - end_x) ** 2 + (y - end_y) ** 2)

                    # Return bridge and which end is closer
                    return bridge, dist_to_start < dist_to_end

        return None, False

    def remove_bridge(self, bridge):
        """Remove a bridge and handle any bidirectional relationships"""
        # Check if there's a reverse bridge that needs modification
        for other_bridge in self.bridges:
            if other_bridge.source_cell == bridge.target_cell and other_bridge.target_cell == bridge.source_cell:
                # Reverse bridge exists, set it to one-way
                other_bridge.direction = BridgeDirection.ONE_WAY
                other_bridge.has_reverse = False
                logger.info("Reverse bridge changed to one-way")

        # Remove the bridge from all collections
        if bridge in bridge.source_cell.outgoing_bridges:
            bridge.source_cell.outgoing_bridges.remove(bridge)

        if bridge in bridge.target_cell.incoming_bridges:
            bridge.target_cell.incoming_bridges.remove(bridge)

        if bridge in self.bridges:
            self.bridges.remove(bridge)

    def run(self):
        running = True
        creating_bridge = False
        bridge_start_cell = None

        # Create the background gradient surface once
        background = self.draw_background_gradient()

        while running:
            if not self.game_started:
                self.show_menu()
                continue

            # Update time if game is in progress
            if not self.game_over_state:
                current_time_sec = pygame.time.get_ticks() / 1000
                self.time_taken = current_time_sec - self.start_time

            current_time = pygame.time.get_ticks()

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Toggle between controlling player and enemy
                        self.control_enemy = not self.control_enemy
                        # Show visual feedback
                        if self.control_enemy:
                            logger.info("Now controlling enemy (red) cells")
                            # Show effect on enemy cells
                            for cell in self.cells:
                                if cell.cell_type == CellType.ENEMY:
                                    self.create_impact_effect(cell.x, cell.y, False)
                        else:
                            logger.info("Now controlling player (blue) cells")
                            # Show effect on player cells
                            for cell in self.cells:
                                if cell.cell_type == CellType.PLAYER:
                                    self.create_impact_effect(cell.x, cell.y, True)

                    elif event.key == pygame.K_e:
                        # Select a cell to evolve
                        mouse_pos = pygame.mouse.get_pos()
                        clicked_cell = self.get_cell_at_position(mouse_pos[0], mouse_pos[1])

                        # Modified to work with both player and enemy cells based on control mode
                        if clicked_cell:
                            if (self.control_enemy and clicked_cell.cell_type == CellType.ENEMY) or \
                                    (not self.control_enemy and clicked_cell.cell_type == CellType.PLAYER):
                                self.selected_cell = clicked_cell
                                # Highlight selected cell
                                self.create_impact_effect(self.selected_cell.x, self.selected_cell.y,
                                                          not self.control_enemy)
                                logger.info(f"Selected cell at ({clicked_cell.x}, {clicked_cell.y})")



                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_pos = pygame.mouse.get_pos()
                        clicked_cell = self.get_cell_at_position(mouse_pos[0], mouse_pos[1])

                        if clicked_cell:
                            if not creating_bridge:
                                # Start creating a bridge if it's the right cell type based on control mode
                                if (self.control_enemy and clicked_cell.cell_type == CellType.ENEMY) or \
                                        (not self.control_enemy and clicked_cell.cell_type == CellType.PLAYER):
                                    creating_bridge = True
                                    bridge_start_cell = clicked_cell
                                    # Sound/visual feedback
                                    self.create_impact_effect(clicked_cell.x, clicked_cell.y,
                                                              not self.control_enemy)
                            else:
                                # Complete bridge creation
                                if clicked_cell != bridge_start_cell:
                                    if self.create_bridge(bridge_start_cell, clicked_cell):
                                        # Success feedback
                                        self.create_impact_effect(clicked_cell.x, clicked_cell.y,
                                                                  not self.control_enemy)
                                creating_bridge = False
                                bridge_start_cell = None
                        else:  # INSERT HERE - If didn't click on a cell, check for bridges
                            clicked_bridge, refund_to_source = self.get_bridge_at_position(mouse_pos[0], mouse_pos[1])

                            if clicked_bridge:
                                # Check if user controls the cell receiving the refund
                                refund_cell = clicked_bridge.source_cell if refund_to_source else clicked_bridge.target_cell
                                can_remove = False

                                if (self.control_enemy and refund_cell.cell_type == CellType.ENEMY) or \
                                        (not self.control_enemy and refund_cell.cell_type == CellType.PLAYER):
                                    can_remove = True

                                if can_remove:
                                    # Get bridge cost for refund
                                    bridge_cost = getattr(clicked_bridge, 'creation_cost',
                                                          1)  # Default to 1 if not stored

                                    # Remove the bridge
                                    self.remove_bridge(clicked_bridge)

                                    # Refund points to the cell closer to the click
                                    refund_cell.points += bridge_cost

                                    # Visual and logging feedback
                                    self.create_impact_effect(refund_cell.x, refund_cell.y,
                                                              refund_cell.cell_type == CellType.PLAYER)
                                    logger.info(
                                        f"Bridge removed. Refunded {bridge_cost} points to cell at ({refund_cell.x}, {refund_cell.y})")

                                    # Skip further processing
                                    continue

                        if self.show_context_menu:
                            # Check if click was inside menu
                            if self.menu_rect.collidepoint(mouse_pos):
                                # Handle menu option selection
                                option_index = (mouse_pos[1] - self.menu_rect.y) // 30
                                if option_index == 0:  # "Remove All Bridges"
                                    logger.info(f"All connections are removed")
                                    self.remove_all_bridges_from_cell(self.context_menu_cell)

                            # Close the menu regardless
                            self.show_context_menu = False
                            self.context_menu_cell = None
                            continue

                    elif event.button == 3:  # Right click
                        # Show context menu for the cell
                        mouse_pos = pygame.mouse.get_pos()
                        clicked_cell = self.get_cell_at_position(mouse_pos[0], mouse_pos[1])

                        if clicked_cell:
                            # Only show menu if cell is player's or enemy's based on control mode
                            if (self.control_enemy and clicked_cell.cell_type == CellType.ENEMY) or \
                                    (not self.control_enemy and clicked_cell.cell_type == CellType.PLAYER):
                                self.show_context_menu = True
                                self.context_menu_cell = clicked_cell
                                logger.info(f"Context menu opened for cell at ({clicked_cell.x}, {clicked_cell.y})")


                            # Update cells
            for cell in self.cells:
                cell.update(current_time)
                # Check if evolution should change based on points
                if cell.cell_type != CellType.EMPTY:
                    self.update_evolution_based_on_points(cell)

            # Spawn balls on bridges
            self.spawn_balls(current_time)

            # Update bridges
            for bridge in self.bridges:
                bridge.update()

            # Update balls
            balls_to_remove = []
            for ball in self.balls:
                ball.update()

                # Check for ball-ball collisions
                for other_ball in self.balls:
                    if ball != other_ball and ball.check_collision(other_ball):
                        if ball not in balls_to_remove:
                            balls_to_remove.append(ball)
                        if other_ball not in balls_to_remove:
                            balls_to_remove.append(other_ball)

                        # Create collision effect
                        self.create_collision_effect(ball.x, ball.y)

                # Check if ball reached target
                target_cell = self.get_cell_at_position(ball.target_x, ball.target_y)
                if target_cell and ball.reached_target(target_cell):
                    balls_to_remove.append(ball)

                    # Create impact effect
                    self.create_impact_effect(target_cell.x, target_cell.y, ball.is_player)

                    # Handle ball effect on target cell
                    if target_cell.cell_type == CellType.EMPTY:
                        # Try to capture empty cell with multiplied attack
                        captured = target_cell.try_capture(ball.attack_value, ball.is_player)
                        if captured and ball.is_player:
                            self.points += 50  # Award points for capturing empty cell
                    elif (target_cell.cell_type == CellType.PLAYER and ball.is_player) or \
                            (target_cell.cell_type == CellType.ENEMY and not ball.is_player):
                        # Add points to allied cell
                        target_cell.points += ball.attack_value
                        if ball.is_player:
                            self.points += 5  # Small points for strengthening own cell
                    else:
                        # Remove points from enemy cell with multiplied attack
                        old_points = target_cell.points
                        target_cell.points = max(0, target_cell.points - ball.attack_value)
                        points_reduced = old_points - target_cell.points

                        # Award points to the player for reducing enemy points
                        if ball.is_player:
                            self.points += points_reduced * 10

                        # Check if cell has 0 points and convert it
                        if target_cell.points == 0:
                            self.remove_all_bridges_from_cell(target_cell)
                            # Convert cell to attacker's color
                            old_type = target_cell.cell_type
                            target_cell.cell_type = CellType.PLAYER if ball.is_player else CellType.ENEMY
                            target_cell.points = 10  # Give some starting points

                            # Award bonus points for capturing cell
                            if ball.is_player:
                                self.points += 100  # Big bonus for capturing enemy cell

                            # Log the capture
                            logger.info(
                                f"Cell at ({target_cell.x}, {target_cell.y}) captured: {old_type} -> {target_cell.cell_type}")

                            # Create multiple impact effects for visual feedback
                            for _ in range(5):  # Create 5 effects for emphasis
                                self.create_impact_effect(target_cell.x, target_cell.y, ball.is_player)

            # Remove balls that have reached their target or collided
            for ball in balls_to_remove:
                if ball in self.balls:
                    self.balls.remove(ball)

            # Drawing
            self.screen.blit(background, (0, 0))  # Draw background gradient

            # Draw bridges
            for bridge in self.bridges:
                bridge.draw(self.screen)

            # Draw bridge being created
            if creating_bridge:
                mouse_pos = pygame.mouse.get_pos()
                pygame.draw.line(self.screen, (100, 100, 100),
                                 (bridge_start_cell.x, bridge_start_cell.y),
                                 mouse_pos, BRIDGE_WIDTH)

            # Draw cells
            for cell in self.cells:
                cell.draw(self.screen)

            # Draw balls
            for ball in self.balls:
                ball.draw(self.screen)

            # Draw game info
            self.draw_game_info()

            self.draw_context_menu(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
            if self.check_win_condition():
                continue

        pygame.quit()
        sys.exit()

    def get_cell_at_position(self, x, y):
        for cell in self.cells:
            if cell.contains_point(x, y):
                return cell
        return None

    def count_outgoing_bridges(self, cell):
        """Count how many outgoing bridges a cell has"""
        return len(cell.outgoing_bridges)

    def create_bridge(self, source_cell, target_cell):
        # Check if bridge already exists in this direction
        existing_bridge = None
        if self.count_outgoing_bridges(source_cell) >= source_cell.evolution.value:
            logger.info(f"Cell can't create more bridges. Evolution level: {source_cell.evolution.value}")
            return False

        # Calculate bridge cost based on distance
        distance = self.calculate_distance(source_cell, target_cell)
        bridge_cost = max(1, int(distance / 30))  # Adjust divisor as needed for balance

        # Check if source cell has enough points
        if source_cell.points < bridge_cost:
            logger.info(f"Not enough points to create bridge. Need {bridge_cost}, have {source_cell.points}")
            return False

        for bridge in self.bridges:
            if (bridge.source_cell == source_cell and bridge.target_cell == target_cell) or \
                    (bridge.source_cell == target_cell and bridge.target_cell == source_cell and
                     source_cell.cell_type == target_cell.cell_type):
                # The second condition only applies if cells are the same color
                # Between different colors, we allow bridges in both directions
                logger.info(f"Bridge already exists between these cells")
                return False
            if bridge.source_cell == source_cell and bridge.target_cell == target_cell:
                return False  # Bridge already exists in this direction
            elif bridge.source_cell == target_cell and bridge.target_cell == source_cell:
                existing_bridge = bridge  # Found a reverse bridge

        # Create new bridge
        new_bridge = Bridge(source_cell, target_cell)
        self.bridges.append(new_bridge)
        logger.info(f"Bridge created from ({source_cell.x}, {source_cell.y}) to ({target_cell.x}, {target_cell.y})")

        # Deduct points for bridge creation
        source_cell.points -= bridge_cost
        logger.info(f"Bridge created. Cost: {bridge_cost} points. Remaining: {source_cell.points}")

        # Create new bridge and store the cost for potential refund later
        #new_bridge = Bridge(source_cell, target_cell)
        new_bridge.creation_cost = bridge_cost  # Store cost for potential refund
        #self.bridges.append(new_bridge)

        # Add bridge to cells
        source_cell.outgoing_bridges.append(new_bridge)
        target_cell.incoming_bridges.append(new_bridge)

        # If there's a reverse bridge, make both bidirectional
        if existing_bridge:
            new_bridge.direction = BridgeDirection.TWO_WAY
            existing_bridge.direction = BridgeDirection.TWO_WAY
            new_bridge.has_reverse = True
            existing_bridge.has_reverse = True

        return True

    def spawn_balls(self, current_time):
        # Iterate through bridges
        for bridge in self.bridges:
            # Set spawn interval based on evolution level
            source_spawn_interval = 3000 // bridge.source_cell.evolution.value

            # Check if it's time to spawn a ball from source
            bridge_key = (id(bridge.source_cell), id(bridge.target_cell))
            if bridge_key not in self.last_ball_spawn_time or \
                    current_time - self.last_ball_spawn_time[bridge_key] >= source_spawn_interval:

                # Only spawn ball if source cell has points to send
                if bridge.source_cell.cell_type != CellType.EMPTY and bridge.source_cell.points > 0:
                    is_player = bridge.source_cell.cell_type == CellType.PLAYER

                    # Spawn ball
                    self.balls.append(Ball(bridge.source_cell, bridge.target_cell, is_player))

                    # Deduct a point from source cell
                    #bridge.source_cell.points -= 1

                    # Update spawn time
                    self.last_ball_spawn_time[bridge_key] = current_time

            # For two-way bridges, also spawn from target to source if there's a reverse bridge
            if bridge.direction == BridgeDirection.TWO_WAY and bridge.has_reverse:
                target_spawn_interval = 3000 // bridge.target_cell.evolution.value
                reverse_bridge_key = (id(bridge.target_cell), id(bridge.source_cell))

                if reverse_bridge_key not in self.last_ball_spawn_time or \
                        current_time - self.last_ball_spawn_time[reverse_bridge_key] >= target_spawn_interval:

                    # Only spawn ball if target cell has points to send
                    if bridge.target_cell.cell_type != CellType.EMPTY and bridge.target_cell.points > 0:
                        is_player = bridge.target_cell.cell_type == CellType.PLAYER

                        # Spawn ball
                        self.balls.append(Ball(bridge.target_cell, bridge.source_cell, is_player))

                        # Deduct a point from target cell
                        bridge.target_cell.points -= 1

                        # Update spawn time
                        self.last_ball_spawn_time[reverse_bridge_key] = current_time

    def draw_context_menu(self, screen):
        """Draw context menu for cell actions"""
        if not self.show_context_menu or not self.context_menu_cell:
            return

        # Create menu background
        menu_width = 180
        menu_height = 30 * len(self.context_menu_options)
        menu_x = min(self.context_menu_cell.x + 40, SCREEN_WIDTH - menu_width)
        menu_y = min(self.context_menu_cell.y + 40, SCREEN_HEIGHT - menu_height)

        menu_surface = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        menu_surface.fill((40, 40, 50, 220))  # Semi-transparent background
        pygame.draw.rect(menu_surface, WHITE, (0, 0, menu_width, menu_height), 1)  # Border

        # Draw menu options
        for i, option in enumerate(self.context_menu_options):
            text_surface = self.font.render(option, True, WHITE)
            text_rect = text_surface.get_rect(midleft=(10, 15 + i * 30))
            menu_surface.blit(text_surface, text_rect)

        # Draw the menu
        screen.blit(menu_surface, (menu_x, menu_y))

        # Store the menu area for detecting clicks
        self.menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)

    def remove_all_bridges_from_cell(self, cell):
        """Remove all outgoing bridges from a cell, and modify bidirectional bridges"""
        logger.info(f"Removing all bridges from cell at ({cell.x}, {cell.y})")

        bridges_to_remove = []
        bridges_to_modify = []

        # Find all outgoing bridges for this cell
        for bridge in self.bridges:
            if bridge.source_cell == cell:
                # Check if there's a reverse bridge that would need modification
                has_reverse = False
                for other_bridge in self.bridges:
                    if other_bridge.source_cell == bridge.target_cell and other_bridge.target_cell == cell:
                        has_reverse = True
                        # If bidirectional, the reverse bridge needs to be modified
                        if bridge.direction == BridgeDirection.TWO_WAY:
                            bridges_to_modify.append(other_bridge)

                bridges_to_remove.append(bridge)

        # Remove the bridges
        for bridge in bridges_to_remove:
            if bridge in self.bridges:
                self.bridges.remove(bridge)
                # Also remove from cell's outgoing bridges list
                if bridge in cell.outgoing_bridges:
                    cell.outgoing_bridges.remove(bridge)
                # And from target's incoming bridges
                if bridge in bridge.target_cell.incoming_bridges:
                    bridge.target_cell.incoming_bridges.remove(bridge)

        # Modify bidirectional bridges to be one-way
        for bridge in bridges_to_modify:
            bridge.direction = BridgeDirection.ONE_WAY
            bridge.has_reverse = False
            logger.info(f"Bridge direction changed to one-way")

    def draw_game_info(self):
        # Count cells by type
        player_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.PLAYER)
        enemy_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.ENEMY)
        empty_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.EMPTY)

        # Check for win
        if empty_cells == 0:
            if enemy_cells == 0:
                # Player has all cells
                self.game_over_state = True
                save_level_stats(self)
                self.game_over("Player Wins!")
            elif player_cells == 0:
                # Enemy has all cells
                self.game_over_state = True
                self.game_over("Enemy Wins!")

        # Count total points for each side
        player_points = sum(cell.points for cell in self.cells if cell.cell_type == CellType.PLAYER)
        enemy_points = sum(cell.points for cell in self.cells if cell.cell_type == CellType.ENEMY)

        # Create a semi-transparent background for the info panel
        info_surface = pygame.Surface((350, 90), pygame.SRCALPHA)
        info_surface.fill((0, 0, 0, 150))
        self.screen.blit(info_surface, (10, 10))

        # Draw info text with colored highlighting
        title_font = pygame.font.SysFont('Arial', 16, bold=True)
        title_text = "WAR OF CELLS"
        title_surface = title_font.render(title_text, True, (200, 200, 255))
        self.screen.blit(title_surface, (20, 15))

        # Draw cells count
        info_text = f"Player Cells: {player_cells} | Enemy Cells: {enemy_cells} | Empty Cells: {empty_cells}"
        info_surface = self.font.render(info_text, True, WHITE)
        self.screen.blit(info_surface, (20, 35))

        # Draw points count
        points_text = f"Player Points: {player_points} | Enemy Points: {enemy_points}"
        points_surface = self.font.render(points_text, True, WHITE)
        self.screen.blit(points_surface, (20, 55))

        # Draw controls help
        controls_text = "Click cells to create bridges | Press E to select + SPACE to evolve"
        controls_surface = self.font.render(controls_text, True, (200, 200, 200))
        self.screen.blit(controls_surface, (20, 75))

        # Draw points and time
        points_text = f"Points: {self.points}"
        points_surface = self.font.render(points_text, True, WHITE)
        self.screen.blit(points_surface, (20, SCREEN_HEIGHT - 60))

        time_text = f"Time: {format_time(self.time_taken)}"
        time_surface = self.font.render(time_text, True, WHITE)
        self.screen.blit(time_surface, (20, SCREEN_HEIGHT - 40))

        # Draw level name
        level_text = f"Level: {self.current_level.replace('level', '')}"
        level_surface = self.font.render(level_text, True, WHITE)
        self.screen.blit(level_surface, (20, SCREEN_HEIGHT - 80))

    def check_win_condition(self):
        """Check if all cells are occupied by one player"""
        player_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.PLAYER)
        enemy_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.ENEMY)
        empty_cells = sum(1 for cell in self.cells if cell.cell_type == CellType.EMPTY)

        # If no empty cells and one side has all cells
        if empty_cells == 0:
            if player_cells == 0:
                #self.game_over("Enemy wins! All cells are captured.")
                return True
            elif enemy_cells == 0:
                #self.game_over("Player wins! All cells are captured.")
                return True

        return False

    def game_over(self, message):
        """Handle game over state"""
        logger.info(f"Game over: {message}")

        # Create a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))

        # Render game over message
        font = pygame.font.SysFont('Arial', 48, bold=True)
        text_surface = font.render(message, True, WHITE)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 60))
        self.screen.blit(text_surface, text_rect)

        # If player won, show stats
        if "Player Wins" in message:
            # Calculate stars
            stars = calculate_stars(self.points, self.time_taken)

            # Show stats
            stats_font = pygame.font.SysFont('Arial', 24)

            # Show points
            points_text = f"Points: {self.points}"
            points_surface = stats_font.render(points_text, True, WHITE)
            points_rect = points_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 10))
            self.screen.blit(points_surface, points_rect)

            # Show time
            time_text = f"Time: {format_time(self.time_taken)}"
            time_surface = stats_font.render(time_text, True, WHITE)
            time_rect = time_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20))
            self.screen.blit(time_surface, time_rect)

            # Draw stars
            star_font = pygame.font.SysFont('Arial', 20)
            star_text = f"Stars: "
            star_surface = star_font.render(star_text, True, WHITE)
            star_rect = star_surface.get_rect(midright=(SCREEN_WIDTH / 2 - 30, SCREEN_HEIGHT / 2 + 50))
            self.screen.blit(star_surface, star_rect)

            # Draw star icons
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

            # Show options
            options_font = pygame.font.SysFont('Arial', 24)

            # Next level option
            if self.current_level.startswith("level"):
                level_num = int(self.current_level[5:])
                next_level = f"level{level_num + 1}"

                if next_level in self.game_data.get("levels", {}):
                    next_text = "Press N for next level"
                    next_surface = options_font.render(next_text, True, (100, 255, 100))
                    next_rect = next_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 90))
                    self.screen.blit(next_surface, next_rect)

        # General options
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

        # Wait for player input
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
                        # Return to menu
                        self.game_started = False
                        waiting = False
                    elif event.key == pygame.K_n and "Player Wins" in message:
                        # Try to load next level
                        if self.current_level.startswith("level"):
                            level_num = int(self.current_level[5:])
                            next_level = f"level{level_num + 1}"

                            if next_level in self.game_data.get("levels", {}):
                                self.current_level = next_level
                                self.start_game()
                                waiting = False
    def reset_game(self):
        """Reset the game to initial state"""
        self.cells = []
        self.bridges = []
        self.balls = []
        self.effects = []
        self.selected_cell = None
        self.last_ball_spawn_time = {}
        self.control_enemy = False

        # Re-initialize the game board
        self.initialize_board()
        logger.info("Game reset")


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
    """Create and show the level selection menu"""
    # Constants for menu
    MENU_BG_COLOR = (20, 20, 40)
    TITLE_COLOR = (220, 220, 255)
    LEVEL_WIDTH = 150
    LEVEL_HEIGHT = 180
    STAR_SIZE = 25
    LEVELS_PER_ROW = 4
    SPACING = 30

    # Initialize menu
    menu_running = True
    clock = pygame.time.Clock()

    # Load star image
    star_img = pygame.Surface((STAR_SIZE, STAR_SIZE), pygame.SRCALPHA)
    # Draw a star shape
    star_points = []
    for i in range(5):
        angle = math.pi * 2 * i / 5 - math.pi / 2
        star_points.append((STAR_SIZE / 2 + math.cos(angle) * STAR_SIZE / 2,
                            STAR_SIZE / 2 + math.sin(angle) * STAR_SIZE / 2))
        angle += math.pi / 5
        star_points.append((STAR_SIZE / 2 + math.cos(angle) * STAR_SIZE / 4,
                            STAR_SIZE / 2 + math.sin(angle) * STAR_SIZE / 4))
    pygame.draw.polygon(star_img, (255, 255, 0), star_points)

    # Load lock image
    lock_img = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.rect(lock_img, (150, 150, 150), (15, 20, 20, 20))
    pygame.draw.rect(lock_img, (150, 150, 150), (10, 10, 30, 15))
    pygame.draw.circle(lock_img, (100, 100, 100), (25, 20), 8)

    while menu_running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False  # Exit game
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    # Check if clicked on a level
                    level_clicked = check_level_click(mouse_pos, game.game_data)
                    if level_clicked:
                        # Check if level is unlocked
                        if is_level_unlocked(game.game_data, level_clicked):
                            game.current_level = level_clicked
                            return True  # Start game with selected level

        # Draw menu
        game.screen.fill(MENU_BG_COLOR)

        # Draw title
        title_font = pygame.font.SysFont('Arial', 48, bold=True)
        title_text = "WAR OF CELLS"
        title_surface = title_font.render(title_text, True, TITLE_COLOR)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH / 2, 50))
        game.screen.blit(title_surface, title_rect)

        # Draw levels
        level_count = len(game.game_data.get("levels", {}))
        start_x = (SCREEN_WIDTH - (LEVELS_PER_ROW * LEVEL_WIDTH + (LEVELS_PER_ROW - 1) * SPACING)) / 2
        start_y = 120

        font = pygame.font.SysFont('Arial', 22, bold=True)
        small_font = pygame.font.SysFont('Arial', 14)

        for i, level_name in enumerate(sorted(game.game_data.get("levels", {}).keys())):
            row = i // LEVELS_PER_ROW
            col = i % LEVELS_PER_ROW

            x = start_x + col * (LEVEL_WIDTH + SPACING)
            y = start_y + row * (LEVEL_HEIGHT + SPACING)

            # Get level info
            level_info = game.game_data.get("summary", {}).get("levels", {}).get(level_name, {})
            unlocked = is_level_unlocked(game.game_data, level_name)

            # Draw level box
            level_color = (60, 80, 120) if unlocked else (60, 60, 60)
            pygame.draw.rect(game.screen, level_color, (x, y, LEVEL_WIDTH, LEVEL_HEIGHT))
            pygame.draw.rect(game.screen, (200, 200, 255), (x, y, LEVEL_WIDTH, LEVEL_HEIGHT), 2)

            # Draw level name
            level_text = f"Level {level_name.replace('level', '')}"
            level_surface = font.render(level_text, True, (255, 255, 255))
            level_rect = level_surface.get_rect(center=(x + LEVEL_WIDTH / 2, y + 25))
            game.screen.blit(level_surface, level_rect)

            if unlocked:
                # Draw stars
                stars = level_info.get("stars", 0)
                star_y = y + 55
                for s in range(3):
                    star_color = (255, 255, 0) if s < stars else (70, 70, 70)
                    star_x = x + LEVEL_WIDTH / 2 - (STAR_SIZE * 3) / 2 + s * STAR_SIZE
                    pygame.draw.polygon(game.screen, star_color,
                                        [(p[0] + star_x, p[1] + star_y) for p in star_points])

                # Draw time
                if "time" in level_info:
                    time_text = f"Time: {level_info['time']}"
                    time_surface = small_font.render(time_text, True, (200, 200, 200))
                    time_rect = time_surface.get_rect(center=(x + LEVEL_WIDTH / 2, y + 90))
                    game.screen.blit(time_surface, time_rect)

                # Draw score
                if "score" in level_info:
                    score_text = f"Score: {level_info['score']}"
                    score_surface = small_font.render(score_text, True, (200, 200, 200))
                    score_rect = score_surface.get_rect(center=(x + LEVEL_WIDTH / 2, y + 110))
                    game.screen.blit(score_surface, score_rect)
            else:
                # Draw lock
                game.screen.blit(lock_img, (x + LEVEL_WIDTH / 2 - 25, y + 60))

        # Draw instructions
        inst_font = pygame.font.SysFont('Arial', 18)
        inst_text = "Click on a level to play. Press ESC to exit."
        inst_surface = inst_font.render(inst_text, True, (180, 180, 180))
        inst_rect = inst_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 40))
        game.screen.blit(inst_surface, inst_rect)

        pygame.display.flip()
        clock.tick(30)

    return False


def check_level_click(mouse_pos, game_data):
    """Check if mouse clicked on a level and return level name"""
    LEVEL_WIDTH = 150
    LEVEL_HEIGHT = 180
    LEVELS_PER_ROW = 4
    SPACING = 30

    level_count = len(game_data.get("levels", {}))
    start_x = (SCREEN_WIDTH - (LEVELS_PER_ROW * LEVEL_WIDTH + (LEVELS_PER_ROW - 1) * SPACING)) / 2
    start_y = 120

    for i, level_name in enumerate(sorted(game_data.get("levels", {}).keys())):
        row = i // LEVELS_PER_ROW
        col = i % LEVELS_PER_ROW

        x = start_x + col * (LEVEL_WIDTH + SPACING)
        y = start_y + row * (LEVEL_HEIGHT + SPACING)

        # Check if mouse pos is inside this level box
        if (x <= mouse_pos[0] <= x + LEVEL_WIDTH and
                y <= mouse_pos[1] <= y + LEVEL_HEIGHT):
            return level_name

    return None


def is_level_unlocked(game_data, level_name):
    """Check if the level is unlocked based on previous level completion"""
    if level_name == "level1":
        return True  # First level is always unlocked

    # Get level number
    if level_name.startswith("level"):
        level_num = int(level_name[5:])
        prev_level_name = f"level{level_num - 1}"

        # Check if previous level exists and has stars (completed)
        prev_level_stars = game_data.get("summary", {}).get("levels", {}).get(prev_level_name, {}).get("stars", 0)
        return prev_level_stars > 0

    return False


def calculate_stars(points, time_taken):
    """Calculate stars based on points and time taken"""
    # Base calculation on points
    if points >= 1500:
        stars = 3
    elif points >= 1000:
        stars = 2
    elif points > 0:
        stars = 1
    else:
        stars = 0

    # Reduce stars if took too long
    minutes = time_taken / 60  # time_taken is in seconds
    if minutes > 5:
        stars = max(0, stars - 1)

    return stars


def format_time(seconds):
    """Format seconds into MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def save_level_stats(game):
    """Save level statistics to the game data"""
    if not game.game_data:
        return

    # Ensure summary structure exists
    if "summary" not in game.game_data:
        game.game_data["summary"] = {"total_levels": len(game.game_data.get("levels", {})), "levels": {}}

    if "levels" not in game.game_data["summary"]:
        game.game_data["summary"]["levels"] = {}

    # Calculate stars based on points and time
    stars = calculate_stars(game.points, game.time_taken)

    # Save level stats
    game.game_data["summary"]["levels"][game.current_level] = {
        "stars": stars,
        "time": format_time(game.time_taken),
        "score": game.points
    }

    # Save to file
    try:
        with open("game_data.json", "w") as file:
            json.dump(game.game_data, file, indent=4)
        logger.info(
            f"Saved stats for {game.current_level}: {stars} stars, time: {format_time(game.time_taken)}, score: {game.points}")
    except Exception as e:
        logger.error(f"Error saving game data: {str(e)}")

def load_level(game, level_name):
    """Load a specific level into the game"""
    # Clear existing game state
    game.cells = []
    game.bridges = []
    game.balls = []
    game.effects = []
    game.selected_cell = None
    game.last_ball_spawn_time = {}

    try:
        # Load game data if not already loaded
        if not hasattr(game, 'game_data') or not game.game_data:
            game.game_data = load_game_data("game_data.json")  # Adjust path as needed

        # Get level data
        if level_name not in game.game_data.get("levels", {}):
            logger.error(f"Level '{level_name}' not found")
            return False

        level_data = game.game_data["levels"][level_name]
        game_map = level_data.get("map", [])
        description = level_data.get("description", {})

        # Calculate grid dimensions
        grid_width = SCREEN_WIDTH // len(game_map[0])
        grid_height = SCREEN_HEIGHT // len(game_map)

        # Keep track of how many of each type we've already placed
        type_counters = {cell_type: 0 for cell_type in description}

        # Create cells based on map
        for y, row in enumerate(game_map):
            for x, cell_char in enumerate(row):
                # Skip walls and empty spaces
                if cell_char == '#' or cell_char == ' ':
                    continue

                # If this is a cell type defined in our description
                if cell_char in description:
                    # Get the appropriate description based on how many we've already placed
                    if type_counters[cell_char] < len(description[cell_char]):
                        cell_info = description[cell_char][type_counters[cell_char]]
                        type_counters[cell_char] += 1

                        # Calculate position
                        cell_x = x * grid_width + grid_width // 2
                        cell_y = y * grid_height + grid_height // 2

                        # Determine cell type
                        if cell_info["color"] == "blue":
                            cell_type = CellType.PLAYER
                        elif cell_info["color"] == "red":
                            cell_type = CellType.ENEMY
                        else:
                            cell_type = CellType.EMPTY

                        # Determine cell shape
                        if cell_info["kind"] == "c":
                            shape = CellShape.CIRCLE
                        elif cell_info["kind"] == "t":
                            shape = CellShape.TRIANGLE
                        else:
                            shape = CellShape.RECTANGLE

                        # Determine evolution
                        evolution = EvolutionLevel(cell_info["evolution"])

                        # Create cell and add to game
                        new_cell = Cell(cell_x, cell_y, cell_type, shape, evolution)
                        new_cell.points = cell_info["points"]
                        game.cells.append(new_cell)
                    else:
                        logger.warning(f"Too many cells of type {cell_char} in map")

        # Verify that all defined cells were placed
        for cell_type, counter in type_counters.items():
            if counter != len(description[cell_type]):
                logger.warning(
                    f"Not all cells of type {cell_type} were placed. Used {counter}/{len(description[cell_type])}")

        logger.info(f"Loaded level: {level_name}")
        return True

    except Exception as e:
        logger.error(f"Error loading level {level_name}: {str(e)}")
        return False
# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()
