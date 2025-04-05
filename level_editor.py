import pygame
import sys
import json
import os
import math
from enum import Enum

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 10
CELL_SIZE = 40
GRID_WIDTH = SCREEN_WIDTH // CELL_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // CELL_SIZE
SIDEBAR_WIDTH = 200
EDITOR_WIDTH = SCREEN_WIDTH - SIDEBAR_WIDTH

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
RED = (255, 50, 50)
BLUE = (50, 100, 255)
GREEN = (50, 200, 50)
YELLOW = (255, 255, 0)


class CellType(Enum):
    EMPTY = 0
    PLAYER = 1
    ENEMY = 2
    OPEN = 3


class CellShape(Enum):
    CIRCLE = 0
    TRIANGLE = 1
    RECTANGLE = 2


class LevelEditor:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("War of Cells Level Editor")
        self.clock = pygame.time.Clock()

        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_cell_type = CellType.PLAYER
        self.selected_shape = CellShape.CIRCLE
        self.cell_points = 10
        self.cell_evolution = 1
        self.cells_count = {
            CellType.PLAYER: 0,
            CellType.ENEMY: 0,
            CellType.OPEN: 0
        }
        self.max_cells_per_type = 5

        self.game_data = self.load_game_data()
        self.levels = self.game_data.get("levels", {})
        self.current_level_index = len(self.levels) + 1

        self.show_save_dialog = False
        self.show_level_select = False
        self.show_level_edit = False
        self.show_level_reorder = False
        self.message = ""
        self.message_timer = 0

        self.level_name_input = f"level{self.current_level_index}"
        self.input_active = False

        self.selected_level_to_edit = None
        self.selected_level_to_reorder = None
        self.reorder_target = None

        self.buttons = []
        self.init_buttons()

    def init_buttons(self):
        button_height = 30
        button_margin = 10
        y_pos = 10

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Player Cell (Blue)",
            "action": lambda: self.set_cell_type(CellType.PLAYER),
            "color": BLUE
        })
        y_pos += button_height + button_margin

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Enemy Cell (Red)",
            "action": lambda: self.set_cell_type(CellType.ENEMY),
            "color": RED
        })
        y_pos += button_height + button_margin

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Open Cell (Gray)",
            "action": lambda: self.set_cell_type(CellType.OPEN),
            "color": GRAY
        })
        y_pos += button_height + button_margin * 2

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Circle Shape",
            "action": lambda: self.set_cell_shape(CellShape.CIRCLE),
            "color": WHITE
        })
        y_pos += button_height + button_margin

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Triangle Shape",
            "action": lambda: self.set_cell_shape(CellShape.TRIANGLE),
            "color": WHITE
        })
        y_pos += button_height + button_margin

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Rectangle Shape",
            "action": lambda: self.set_cell_shape(CellShape.RECTANGLE),
            "color": WHITE
        })
        y_pos += button_height + button_margin * 2

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, 50, button_height),
            "text": "-5",
            "action": lambda: self.adjust_points(-5),
            "color": LIGHT_GRAY
        })

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 70, y_pos, 60, button_height),
            "text": "Points",
            "action": None,
            "color": LIGHT_GRAY
        })

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 140, y_pos, 50, button_height),
            "text": "+5",
            "action": lambda: self.adjust_points(5),
            "color": LIGHT_GRAY
        })
        y_pos += button_height + button_margin

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Save Level",
            "action": lambda: self.toggle_save_dialog(),
            "color": GREEN
        })
        y_pos += button_height + button_margin

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Load Level",
            "action": lambda: self.toggle_level_select(),
            "color": YELLOW
        })
        y_pos += button_height + button_margin

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Edit Level",
            "action": lambda: self.toggle_level_edit(),
            "color": YELLOW
        })
        y_pos += button_height + button_margin

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Reorder Levels",
            "action": lambda: self.toggle_level_reorder(),
            "color": YELLOW
        })
        y_pos += button_height + button_margin

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Clear Grid",
            "action": lambda: self.clear_grid(),
            "color": RED
        })
        y_pos += button_height + button_margin

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, y_pos, SIDEBAR_WIDTH - 20, button_height),
            "text": "Quick Save",
            "action": lambda: self.quick_save(),
            "color": GREEN
        })
        y_pos += button_height + button_margin

        self.buttons.append({
            "rect": pygame.Rect(EDITOR_WIDTH + 10, SCREEN_HEIGHT - 50, SIDEBAR_WIDTH - 20, button_height),
            "text": "Back to Menu",
            "action": lambda: self.return_to_menu(),
            "color": YELLOW
        })

    def load_game_data(self):
        try:
            if os.path.exists("game_data.json"):
                with open("game_data.json", "r") as file:
                    return json.load(file)
            else:
                return {"levels": {}, "summary": {"total_levels": 0, "levels": {}}}
        except Exception as e:
            print(f"Error loading game data: {e}")
            return {"levels": {}, "summary": {"total_levels": 0, "levels": {}}}

    def save_game_data(self):
        try:
            with open("game_data.json", "w") as file:
                json.dump(self.game_data, file, indent=4)
            return True
        except Exception as e:
            print(f"Error saving game data: {e}")
            return False

    def return_to_menu(self):
        if self.main_game:
            self.main_game.show_menu()
            return True
        else:
            self.show_message("Cannot return to menu in standalone mode")
            return False

    def set_cell_type(self, cell_type):
        self.selected_cell_type = cell_type

    def set_cell_shape(self, shape):
        self.selected_shape = shape

    def adjust_points(self, delta):
        self.cell_points = max(1, self.cell_points + delta)

    def toggle_save_dialog(self):
        self.show_save_dialog = not self.show_save_dialog
        if self.show_save_dialog:
            self.level_name_input = f"level{self.current_level_index}"
            self.input_active = True

    def toggle_level_select(self):
        self.show_level_select = not self.show_level_select
        self.show_level_edit = False
        self.show_level_reorder = False

    def toggle_level_edit(self):
        self.show_level_edit = not self.show_level_edit
        self.show_level_select = False
        self.show_level_reorder = False

    def toggle_level_reorder(self):
        self.show_level_reorder = not self.show_level_reorder
        self.show_level_select = False
        self.show_level_edit = False

    def clear_grid(self):
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.cells_count = {
            CellType.PLAYER: 0,
            CellType.ENEMY: 0,
            CellType.OPEN: 0
        }
        self.show_message("Grid cleared")

    def show_message(self, text, duration=2000):
        self.message = text
        self.message_timer = duration

    def can_place_cell(self, cell_type):
        return self.cells_count[cell_type] < self.max_cells_per_type

    def place_cell(self, grid_x, grid_y):
        if not (0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE):
            return

        if grid_x == 0 or grid_x == GRID_SIZE - 1 or grid_y == 0 or grid_y == GRID_SIZE - 1:
            self.show_message("Cannot place cells on border")
            return

        if self.grid[grid_y][grid_x] is not None:
            cell_type = self.grid[grid_y][grid_x]["type"]
            self.cells_count[cell_type] -= 1
            self.grid[grid_y][grid_x] = None
            return

        if not self.can_place_cell(self.selected_cell_type):
            self.show_message(f"Maximum {self.max_cells_per_type} cells of this type allowed")
            return

        if self.selected_cell_type == CellType.OPEN:
            self.grid[grid_y][grid_x] = {
                "type": self.selected_cell_type,
                "shape": self.selected_shape,
                "points": 0,
                #"capture_points": self.capture_points,
                "evolution": 1
            }
        else:
            evolution = 1
            if self.cell_points >= 15 and self.cell_points < 35:
                evolution = 2
            elif self.cell_points >= 35:
                evolution = 3

            self.grid[grid_y][grid_x] = {
                "type": self.selected_cell_type,
                "shape": self.selected_shape,
                "points": self.cell_points,
                "evolution": evolution
            }

        self.cells_count[self.selected_cell_type] += 1


    def create_level_map(self):
        map_data = []
        for y in range(GRID_SIZE):
            row = ""
            for x in range(GRID_SIZE):
                if x == 0 or x == GRID_SIZE - 1 or y == 0 or y == GRID_SIZE - 1:
                    row += "#"
                elif self.grid[y][x] is None:
                    row += " "
                elif self.grid[y][x]["type"] == CellType.PLAYER:
                    row += "u"
                elif self.grid[y][x]["type"] == CellType.ENEMY:
                    row += "e"
                elif self.grid[y][x]["type"] == CellType.OPEN:
                    row += "o"
            map_data.append(row)
        return map_data

    def create_level_description(self):
        description = {"e": [], "u": [], "o": []}

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] is not None:
                    cell = self.grid[y][x]

                    if cell["type"] == CellType.PLAYER:
                        key = "u"
                        color = "blue"
                    elif cell["type"] == CellType.ENEMY:
                        key = "e"
                        color = "red"
                    elif cell["type"] == CellType.OPEN:
                        key = "o"
                        color = "no"
                    else:
                        continue

                    if cell["shape"] == CellShape.CIRCLE:
                        kind = "c"
                    elif cell["shape"] == CellShape.TRIANGLE:
                        kind = "t"
                    else:
                        kind = "r"

                    description[key].append({
                        "points": cell["points"],
                        "evolution": cell["evolution"],
                        "kind": kind,
                        "color": color
                    })

        return description

    def save_level(self):
        if not self.level_name_input.startswith("level"):
            self.show_message("Level name must start with 'level'")
            return

        if self.cells_count[CellType.PLAYER] == 0:
            self.show_message("Level must have at least one player cell")
            return

        if self.cells_count[CellType.ENEMY] == 0:
            self.show_message("Level must have at least one enemy cell")
            return

        level_data = {
            "map": self.create_level_map(),
            "description": self.create_level_description()
        }

        self.game_data["levels"][self.level_name_input] = level_data

        if self.level_name_input not in self.game_data["summary"]["levels"]:
            self.game_data["summary"]["levels"][self.level_name_input] = {
                "stars": 0,
                "time": "00:00",
                "score": 0
            }

        self.game_data["summary"]["total_levels"] = len(self.game_data["levels"])

        if self.save_game_data():
            self.show_message(f"Level {self.level_name_input} saved successfully")
            self.show_save_dialog = False
            self.levels = self.game_data["levels"]

            level_numbers = []
            for level in self.levels:
                if level.startswith("level"):
                    try:
                        level_numbers.append(int(level[5:]))
                    except ValueError:
                        pass

            if level_numbers:
                self.current_level_index = max(level_numbers) + 1
            else:
                self.current_level_index = 1
        else:
            self.show_message("Error saving level")

    def load_level(self, level_name):
        if level_name not in self.game_data["levels"]:
            self.show_message(f"Level {level_name} not found")
            return

        self.clear_grid()

        level_data = self.game_data["levels"][level_name]
        map_data = level_data["map"]
        description = level_data["description"]

        cell_data = {}
        for key, cells in description.items():
            for i, cell in enumerate(cells):
                if key == "u":
                    cell_type = CellType.PLAYER
                elif key == "e":
                    cell_type = CellType.ENEMY
                elif key == "o":
                    cell_type = CellType.OPEN

                if cell["kind"] == "c":
                    shape = CellShape.CIRCLE
                elif cell["kind"] == "t":
                    shape = CellShape.TRIANGLE
                else:
                    shape = CellShape.RECTANGLE

                cell_data[f"{key}{i}"] = {
                    "type": cell_type,
                    "shape": shape,
                    "points": cell["points"],
                    "evolution": cell["evolution"]
                }

        cell_counts = {"u": 0, "e": 0, "o": 0}

        for y, row in enumerate(map_data):
            for x, char in enumerate(row):
                if char in ["u", "e", "o"]:
                    cell_key = f"{char}{cell_counts[char]}"
                    if cell_key in cell_data:
                        self.grid[y][x] = cell_data[cell_key]
                        self.cells_count[cell_data[cell_key]["type"]] += 1
                        cell_counts[char] += 1

        self.show_message(f"Level {level_name} loaded")
        self.level_name_input = level_name

    def reorder_levels(self, level_name, target_index):
        if level_name not in self.game_data["levels"] or target_index < 1:
            return

        level_names = sorted([name for name in self.game_data["levels"].keys() if name.startswith("level")],
                             key=lambda x: int(x[5:]) if x[5:].isdigit() else float('inf'))

        if level_name not in level_names:
            return

        current_index = level_names.index(level_name)
        level_names.pop(current_index)

        target_index = min(target_index - 1, len(level_names))
        level_names.insert(target_index, level_name)

        new_levels = {}
        new_summary_levels = {}

        for i, name in enumerate(level_names):
            new_level_name = f"level{i + 1}"

            new_levels[new_level_name] = self.game_data["levels"][name]

            if name in self.game_data["summary"]["levels"]:
                new_summary_levels[new_level_name] = self.game_data["summary"]["levels"][name]
            else:
                new_summary_levels[new_level_name] = {"stars": 0, "time": "00:00", "score": 0}

        self.game_data["levels"] = new_levels
        self.game_data["summary"]["levels"] = new_summary_levels
        self.game_data["summary"]["total_levels"] = len(new_levels)

        if self.save_game_data():
            self.show_message("Levels reordered successfully")
            self.levels = self.game_data["levels"]
        else:
            self.show_message("Error reordering levels")

    def draw_grid(self):
        self.screen.fill(BLACK)

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

                if x == 0 or x == GRID_SIZE - 1 or y == 0 or y == GRID_SIZE - 1:
                    pygame.draw.rect(self.screen, DARK_GRAY, rect)
                    continue

                pygame.draw.rect(self.screen, BLACK, rect)
                pygame.draw.rect(self.screen, DARK_GRAY, rect, 1)

                if self.grid[y][x] is not None:
                    cell = self.grid[y][x]
                    cell_rect = pygame.Rect(x * CELL_SIZE + 2, y * CELL_SIZE + 2, CELL_SIZE - 4, CELL_SIZE - 4)

                    if cell["type"] == CellType.PLAYER:
                        color = BLUE
                    elif cell["type"] == CellType.ENEMY:
                        color = RED
                    else:
                        color = GRAY

                    if cell["shape"] == CellShape.CIRCLE:
                        pygame.draw.circle(self.screen, color,
                                           (x * CELL_SIZE + CELL_SIZE // 2,
                                            y * CELL_SIZE + CELL_SIZE // 2),
                                           CELL_SIZE // 2 - 4)
                    elif cell["shape"] == CellShape.TRIANGLE:
                        points = [
                            (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + 4),
                            (x * CELL_SIZE + 4, y * CELL_SIZE + CELL_SIZE - 4),
                            (x * CELL_SIZE + CELL_SIZE - 4, y * CELL_SIZE + CELL_SIZE - 4)
                        ]
                        pygame.draw.polygon(self.screen, color, points)
                    else:
                        pygame.draw.rect(self.screen, color, cell_rect)

                    # Replace the existing code that draws cell info with this:
                    if cell["type"] == CellType.OPEN:
                        # For open cells, show 0/{points}
                        font = pygame.font.SysFont(None, 20)
                        capture_text = f"0/{cell['points']}"

                        text_surface = font.render(capture_text, True, WHITE)
                        text_rect = text_surface.get_rect(center=(x * CELL_SIZE + CELL_SIZE // 2,
                                                                  y * CELL_SIZE + CELL_SIZE // 2))

                        self.screen.blit(text_surface, text_rect)
                    else:
                        # For player/enemy cells
                        font = pygame.font.SysFont(None, 20)
                        points_text = str(cell["points"])

                        # Calculate evolution based on points
                        evolution = 1
                        if cell["points"] >= 15 and cell["points"] < 35:
                            evolution = 2
                        elif cell["points"] >= 35:
                            evolution = 3

                        evolution_text = f"E{evolution}"

                        pts_surface = font.render(points_text, True, WHITE)
                        evo_surface = font.render(evolution_text, True, WHITE)

                        pts_rect = pts_surface.get_rect(center=(x * CELL_SIZE + CELL_SIZE // 2,
                                                                y * CELL_SIZE + CELL_SIZE // 2 - 5))
                        evo_rect = evo_surface.get_rect(center=(x * CELL_SIZE + CELL_SIZE // 2,
                                                                y * CELL_SIZE + CELL_SIZE // 2 + 10))

                        self.screen.blit(pts_surface, pts_rect)
                        self.screen.blit(evo_surface, evo_rect)
    def draw_sidebar(self):
        sidebar_rect = pygame.Rect(EDITOR_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, DARK_GRAY, sidebar_rect)
        pygame.draw.line(self.screen, WHITE, (EDITOR_WIDTH, 0), (EDITOR_WIDTH, SCREEN_HEIGHT), 2)

        for button in self.buttons:
            pygame.draw.rect(self.screen, button["color"], button["rect"])
            pygame.draw.rect(self.screen, BLACK, button["rect"], 2)

            font = pygame.font.SysFont(None, 20)
            text_surface = font.render(button["text"], True, BLACK)
            text_rect = text_surface.get_rect(center=button["rect"].center)
            self.screen.blit(text_surface, text_rect)

        font = pygame.font.SysFont(None, 24)

        if self.selected_cell_type == CellType.PLAYER:
            type_text = "Player Cell"
            type_color = BLUE
        elif self.selected_cell_type == CellType.ENEMY:
            type_text = "Enemy Cell"
            type_color = RED
        else:
            type_text = "Open Cell"
            type_color = GRAY

        if self.selected_shape == CellShape.CIRCLE:
            shape_text = "Circle"
        elif self.selected_shape == CellShape.TRIANGLE:
            shape_text = "Triangle"
        else:
            shape_text = "Rectangle"

        count_y = 350
        pygame.draw.rect(self.screen, LIGHT_GRAY,
                         (EDITOR_WIDTH + 10, count_y, SIDEBAR_WIDTH - 20, 80))

        info_font = pygame.font.SysFont(None, 22)
        count_text = f"Cell Counts (max {self.max_cells_per_type}):"
        blue_text = f"Player (blue): {self.cells_count[CellType.PLAYER]}"
        red_text = f"Enemy (red): {self.cells_count[CellType.ENEMY]}"
        gray_text = f"Open: {self.cells_count[CellType.OPEN]}"

        count_surface = info_font.render(count_text, True, BLACK)
        blue_surface = info_font.render(blue_text, True, BLUE)
        red_surface = info_font.render(red_text, True, RED)
        gray_surface = info_font.render(gray_text, True, BLACK)

        self.screen.blit(count_surface, (EDITOR_WIDTH + 15, count_y + 5))
        self.screen.blit(blue_surface, (EDITOR_WIDTH + 15, count_y + 25))
        self.screen.blit(red_surface, (EDITOR_WIDTH + 15, count_y + 45))
        self.screen.blit(gray_surface, (EDITOR_WIDTH + 15, count_y + 65))

        settings_y = 440
        pygame.draw.rect(self.screen, LIGHT_GRAY,
                         (EDITOR_WIDTH + 10, settings_y, SIDEBAR_WIDTH - 20, 100))

        selected_text = "Selected:"
        type_surface = info_font.render(f"Type: {type_text}", True, type_color)
        shape_surface = info_font.render(f"Shape: {shape_text}", True, BLACK)
        points_surface = info_font.render(f"Points: {self.cell_points}", True, BLACK)
        evolution_surface = info_font.render(f"Evolution: {self.cell_evolution}", True, BLACK)

        self.screen.blit(info_font.render(selected_text, True, BLACK),
                         (EDITOR_WIDTH + 15, settings_y + 5))
        self.screen.blit(type_surface, (EDITOR_WIDTH + 15, settings_y + 25))
        self.screen.blit(shape_surface, (EDITOR_WIDTH + 15, settings_y + 45))
        self.screen.blit(points_surface, (EDITOR_WIDTH + 15, settings_y + 65))
        self.screen.blit(evolution_surface, (EDITOR_WIDTH + 15, settings_y + 85))

    def draw_save_dialog(self):
        dialog_width = 300
        dialog_height = 150
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2

        pygame.draw.rect(self.screen, DARK_GRAY,
                         (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, WHITE,
                         (dialog_x, dialog_y, dialog_width, dialog_height), 2)

        font = pygame.font.SysFont(None, 28)
        title_surface = font.render("Save Level", True, WHITE)
        title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2,
                                                    dialog_y + 25))
        self.screen.blit(title_surface, title_rect)

        input_rect = pygame.Rect(dialog_x + 20, dialog_y + 50,
                                 dialog_width - 40, 30)
        input_color = WHITE if self.input_active else LIGHT_GRAY
        pygame.draw.rect(self.screen, input_color, input_rect)
        pygame.draw.rect(self.screen, BLACK, input_rect, 2)

        font = pygame.font.SysFont(None, 24)
        input_surface = font.render(self.level_name_input, True, BLACK)
        self.screen.blit(input_surface, (input_rect.x + 5, input_rect.y + 5))

        save_rect = pygame.Rect(dialog_x + 20, dialog_y + 100, 100, 30)
        cancel_rect = pygame.Rect(dialog_x + dialog_width - 120, dialog_y + 100, 100, 30)

        pygame.draw.rect(self.screen, GREEN, save_rect)
        pygame.draw.rect(self.screen, RED, cancel_rect)
        pygame.draw.rect(self.screen, BLACK, save_rect, 2)
        pygame.draw.rect(self.screen, BLACK, cancel_rect, 2)

        save_surface = font.render("Save", True, BLACK)
        cancel_surface = font.render("Cancel", True, BLACK)

        save_text_rect = save_surface.get_rect(center=save_rect.center)
        cancel_text_rect = cancel_surface.get_rect(center=cancel_rect.center)

        self.screen.blit(save_surface, save_text_rect)
        self.screen.blit(cancel_surface, cancel_text_rect)

        return save_rect, cancel_rect

    def draw_level_select(self):
        dialog_width = 400
        dialog_height = 400
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2

        pygame.draw.rect(self.screen, DARK_GRAY,
                         (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, WHITE,
                         (dialog_x, dialog_y, dialog_width, dialog_height), 2)

        font = pygame.font.SysFont(None, 28)
        title_surface = font.render("Select Level to Load", True, WHITE)
        title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2,
                                                    dialog_y + 25))
        self.screen.blit(title_surface, title_rect)

        level_rects = []
        font = pygame.font.SysFont(None, 24)

        level_names = sorted([name for name in self.levels.keys()],
                             key=lambda x: int(x[5:]) if x[5:].isdigit() else float('inf'))

        list_y = dialog_y + 60
        for level_name in level_names:
            level_rect = pygame.Rect(dialog_x + 20, list_y, dialog_width - 40, 30)
            pygame.draw.rect(self.screen, LIGHT_GRAY, level_rect)
            pygame.draw.rect(self.screen, BLACK, level_rect, 2)

            text_surface = font.render(level_name, True, BLACK)
            self.screen.blit(text_surface, (level_rect.x + 10, level_rect.y + 5))

            level_rects.append((level_rect, level_name))
            list_y += 35

            if list_y > dialog_y + dialog_height - 40:
                break

        cancel_rect = pygame.Rect(dialog_x + dialog_width - 120,
                                  dialog_y + dialog_height - 40, 100, 30)

        pygame.draw.rect(self.screen, RED, cancel_rect)
        pygame.draw.rect(self.screen, BLACK, cancel_rect, 2)

        cancel_surface = font.render("Cancel", True, BLACK)
        cancel_text_rect = cancel_surface.get_rect(center=cancel_rect.center)

        self.screen.blit(cancel_surface, cancel_text_rect)

        return level_rects, cancel_rect

    def draw_level_edit(self):
        return self.draw_level_select()

    def draw_level_reorder(self):
        dialog_width = 500
        dialog_height = 400
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2

        pygame.draw.rect(self.screen, DARK_GRAY,
                         (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, WHITE,
                         (dialog_x, dialog_y, dialog_width, dialog_height), 2)

        font = pygame.font.SysFont(None, 28)
        title_surface = font.render("Reorder Levels", True, WHITE)
        title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2,
                                                    dialog_y + 25))
        self.screen.blit(title_surface, title_rect)

        font = pygame.font.SysFont(None, 20)
        instruct_surface = font.render("Select a level, then select a position to move it to", True, WHITE)
        instruct_rect = instruct_surface.get_rect(center=(dialog_x + dialog_width // 2,
                                                          dialog_y + 50))
        self.screen.blit(instruct_surface, instruct_rect)

        level_rects = []
        position_rects = []
        font = pygame.font.SysFont(None, 24)

        level_names = sorted([name for name in self.levels.keys()],
                             key=lambda x: int(x[5:]) if x[5:].isdigit() else float('inf'))

        list_y = dialog_y + 80
        for i, level_name in enumerate(level_names):
            level_rect = pygame.Rect(dialog_x + 20, list_y, 200, 30)
            color = YELLOW if self.selected_level_to_reorder == level_name else LIGHT_GRAY
            pygame.draw.rect(self.screen, color, level_rect)
            pygame.draw.rect(self.screen, BLACK, level_rect, 2)

            text_surface = font.render(f"{i + 1}. {level_name}", True, BLACK)
            self.screen.blit(text_surface, (level_rect.x + 10, level_rect.y + 5))

            level_rects.append((level_rect, level_name))

            pos_rect = pygame.Rect(dialog_x + 230, list_y, 50, 30)
            color = GREEN if self.reorder_target == i + 1 else LIGHT_GRAY
            pygame.draw.rect(self.screen, color, pos_rect)
            pygame.draw.rect(self.screen, BLACK, pos_rect, 2)

            text_surface = font.render(f"{i + 1}", True, BLACK)
            text_rect = text_surface.get_rect(center=pos_rect.center)
            self.screen.blit(text_surface, text_rect)

            position_rects.append((pos_rect, i + 1))

            list_y += 35

            if list_y > dialog_y + dialog_height - 80:
                break

        move_rect = pygame.Rect(dialog_x + 20, dialog_y + dialog_height - 50, 120, 30)
        cancel_rect = pygame.Rect(dialog_x + dialog_width - 140,
                                  dialog_y + dialog_height - 50, 120, 30)

        move_color = GREEN if self.selected_level_to_reorder and self.reorder_target else LIGHT_GRAY
        pygame.draw.rect(self.screen, move_color, move_rect)
        pygame.draw.rect(self.screen, RED, cancel_rect)
        pygame.draw.rect(self.screen, BLACK, move_rect, 2)
        pygame.draw.rect(self.screen, BLACK, cancel_rect, 2)

        move_surface = font.render("Move Level", True, BLACK)
        cancel_surface = font.render("Cancel", True, BLACK)

        move_text_rect = move_surface.get_rect(center=move_rect.center)
        cancel_text_rect = cancel_surface.get_rect(center=cancel_rect.center)

        self.screen.blit(move_surface, move_text_rect)
        self.screen.blit(cancel_surface, cancel_text_rect)

        return level_rects, position_rects, move_rect, cancel_rect

    def draw_message(self):
        if self.message and self.message_timer > 0:
            font = pygame.font.SysFont(None, 24)
            message_surface = font.render(self.message, True, WHITE)
            message_rect = message_surface.get_rect(center=(SCREEN_WIDTH // 2, 30))

            bg_rect = message_rect.copy()
            bg_rect.inflate_ip(20, 10)
            pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect)
            pygame.draw.rect(self.screen, WHITE, bg_rect, 2)

            self.screen.blit(message_surface, message_rect)

    def run(self):
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.show_save_dialog:
                            save_rect, cancel_rect = self.draw_save_dialog()
                            if save_rect.collidepoint(mouse_pos):
                                self.save_level()
                            elif cancel_rect.collidepoint(mouse_pos):
                                self.show_save_dialog = False

                        elif self.show_level_select:
                            level_rects, cancel_rect = self.draw_level_select()

                            if cancel_rect.collidepoint(mouse_pos):
                                self.show_level_select = False
                            else:
                                for rect, level_name in level_rects:
                                    if rect.collidepoint(mouse_pos):
                                        self.load_level(level_name)
                                        self.show_level_select = False
                                        break

                        elif self.show_level_edit:
                            level_rects, cancel_rect = self.draw_level_edit()

                            if cancel_rect.collidepoint(mouse_pos):
                                self.show_level_edit = False
                            else:
                                for rect, level_name in level_rects:
                                    if rect.collidepoint(mouse_pos):
                                        self.load_level(level_name)
                                        self.show_level_edit = False
                                        break

                        elif self.show_level_reorder:
                            level_rects, position_rects, move_rect, cancel_rect = self.draw_level_reorder()

                            if cancel_rect.collidepoint(mouse_pos):
                                self.show_level_reorder = False
                                self.selected_level_to_reorder = None
                                self.reorder_target = None
                            elif move_rect.collidepoint(mouse_pos):
                                if self.selected_level_to_reorder and self.reorder_target:
                                    self.reorder_levels(self.selected_level_to_reorder, self.reorder_target)
                                    self.selected_level_to_reorder = None
                                    self.reorder_target = None
                            else:
                                for rect, level_name in level_rects:
                                    if rect.collidepoint(mouse_pos):
                                        self.selected_level_to_reorder = level_name
                                        break

                                for rect, position in position_rects:
                                    if rect.collidepoint(mouse_pos):
                                        self.reorder_target = position
                                        break

                        else:
                            for button in self.buttons:
                                if button["rect"].collidepoint(mouse_pos) and button["action"]:
                                    button["action"]()
                                    break
                            else:
                                grid_x = mouse_pos[0] // CELL_SIZE
                                grid_y = mouse_pos[1] // CELL_SIZE

                                if grid_x < GRID_SIZE and grid_y < GRID_SIZE:
                                    self.place_cell(grid_x, grid_y)

                elif event.type == pygame.KEYDOWN:
                    if self.show_save_dialog and self.input_active:
                        if event.key == pygame.K_RETURN:
                            self.save_level()
                        elif event.key == pygame.K_BACKSPACE:
                            self.level_name_input = self.level_name_input[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            self.show_save_dialog = False
                        else:
                            self.level_name_input += event.unicode

            self.draw_grid()
            self.draw_sidebar()

            if self.show_save_dialog:
                self.draw_save_dialog()
            elif self.show_level_select:
                self.draw_level_select()
            elif self.show_level_edit:
                self.draw_level_edit()
            elif self.show_level_reorder:
                self.draw_level_reorder()

            if self.message_timer > 0:
                self.message_timer -= self.clock.get_time()
                self.draw_message()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()


if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()
