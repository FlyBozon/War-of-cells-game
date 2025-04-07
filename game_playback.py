import os
import time
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import json
import datetime
import logging
from enum import Enum

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('WarOfCEllsGame')

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


class GamePlayback:
    def __init__(self, game, cell_class=None, cell_type_class=None, cell_shape_class=None, evolution_level_class=None):
        self.game = game
        self.history = None
        self.is_playing = False
        self.current_time = 0
        self.playback_speed = 1.0
        self.event_index = 0
        self.last_update_time = 0
        self.cell_id_map = {}

        self.Cell = cell_class
        self.CellType = cell_type_class
        self.CellShape = cell_shape_class
        self.EvolutionLevel = evolution_level_class

    def load_json_history(self, filename):
        try:
            with open(filename, "r") as f:
                self.history = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading JSON history: {e}")
            return False

    def load_xml_history(self, filename):
        try:
            tree = ET.parse(filename)
            root = tree.getroot()

            metadata = {}
            metadata_elem = root.find("Metadata")
            for child in metadata_elem:
                if child.tag in ["turnBased", "aiEnabled"]:
                    metadata[child.tag] = child.text.lower() == "true"
                elif child.tag == "duration":
                    metadata[child.tag] = float(child.text)
                else:
                    metadata[child.tag] = child.text

            events = []
            events_elem = root.find("Events")
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
                                    if attr.tag in ["id", "x", "y", "evolution", "points"]:
                                        item_dict[attr.tag] = int(attr.text)
                                    else:
                                        item_dict[attr.tag] = attr.text
                                items.append(item_dict)
                            else:
                                items.append(item_elem.text)
                        event["data"][child.tag] = items
                    else:
                        event["data"][child.tag] = child.text

                events.append(event)

            self.history = {
                "metadata": metadata,
                "events": events
            }
            return True

        except Exception as e:
            print(f"Error loading XML history: {e}")
            return False

    def load_mongodb_history(self, game_id):
        try:
            import pymongo
            from bson import ObjectId
            from mongodb_config import DEFAULT_CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME
        except ImportError:
            logger.error("MongoDB support not available. Install pymongo package.")
            return False

        try:
            client = pymongo.MongoClient(DEFAULT_CONNECTION_STRING)
            db = client[DATABASE_NAME]
            collection = db[COLLECTION_NAME]

            try:
                if len(game_id) == 24:
                    object_id = ObjectId(game_id)
                    game_history = collection.find_one({"_id": object_id})
                else:
                    game_history = collection.find_one({"metadata.gameId": game_id})
            except:
                game_history = collection.find_one({"metadata.gameId": game_id})

            if game_history:
                if "_id" in game_history:
                    game_history["_id"] = str(game_history["_id"])
                self.history = game_history
                return True
            else:
                logger.error(f"Game with ID {game_id} not found in MongoDB")
                return False

        except Exception as e:
            logger.error(f"MongoDB error: {e}")
            return False


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
            self.game_started = True
            return True
        else:
            self.playback_active = False
            self.game_playback = None
            return False

    def _apply_initial_state(self):
        if not self.history or self.event_index >= len(self.history["events"]):
            return

        for i, event in enumerate(self.history["events"]):
            if event["eventType"] == "GAME_START":
                metadata = self.history["metadata"]
                self.game.current_level = metadata.get("level", "level1")
                self.game.turn_based_mode = metadata.get("turnBased", False)
                self.game.ai_enabled = metadata.get("aiEnabled", False)
                self.game.ai_difficulty = metadata.get("aiDifficulty", "Medium")

                self.game.cells = []
                self.game.bridges = []
                self.game.balls = []
                self.cell_id_map = {}

                cells_data = event["data"].get("cells", [])

                for cell_data in cells_data:
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

                    self.game.cells.append(cell)
                    self.cell_id_map[cell_data.get("id")] = cell

                self.event_index = i + 1
                return

    def pause(self):
        self.is_playing = False

    def resume(self):
        if self.history:
            self.is_playing = True
            self.last_update_time = time.time()

    def set_speed(self, speed):
        self.playback_speed = max(0.25, min(4.0, speed))

    def seek(self, target_time):
        if not self.history:
            return

        self._apply_initial_state()

        while (self.event_index < len(self.history["events"]) and
               self.history["events"][self.event_index]["timestamp"] <= target_time):
            self._apply_event(self.history["events"][self.event_index])
            self.event_index += 1

        self.current_time = target_time

    def update(self):
        if not self.is_playing or not self.history:
            return

        current_real_time = time.time()
        dt = (current_real_time - self.last_update_time) * self.playback_speed
        self.last_update_time = current_real_time

        self.current_time += dt

        while (self.event_index < len(self.history["events"]) and
               self.history["events"][self.event_index]["timestamp"] <= self.current_time):
            self._apply_event(self.history["events"][self.event_index])
            self.event_index += 1

        if self.event_index >= len(self.history["events"]):
            self.is_playing = False

    def _apply_event(self, event):
        if not event:
            return

        event_type = event["eventType"]
        data = event["data"]

        if event_type == "BRIDGE_CREATED":
            source_id = data.get("sourceId")
            target_id = data.get("targetId")

            if source_id in self.cell_id_map and target_id in self.cell_id_map:
                source_cell = self.cell_id_map[source_id]
                target_cell = self.cell_id_map[target_id]
                self.game.create_bridge(source_cell, target_cell)

        elif event_type == "BRIDGE_REMOVED":
            source_id = data.get("sourceId")
            target_id = data.get("targetId")

            if source_id in self.cell_id_map and target_id in self.cell_id_map:
                source_cell = self.cell_id_map[source_id]
                target_cell = self.cell_id_map[target_id]

                for bridge in self.game.bridges:
                    if bridge.source_cell == source_cell and bridge.target_cell == target_cell:
                        self.game.remove_bridge(bridge)
                        break

        elif event_type == "CELL_CAPTURED":
            cell_id = data.get("cellId")
            new_type_name = data.get("newType")

            if cell_id in self.cell_id_map and new_type_name:
                cell = self.cell_id_map[cell_id]
                cell.cell_type = getattr(CellType, new_type_name)
                cell.points = data.get("points", 20)

        elif event_type == "CELL_EVOLVED":
            cell_id = data.get("cellId")
            new_level = data.get("newLevel")

            if cell_id in self.cell_id_map and new_level:
                cell = self.cell_id_map[cell_id]
                cell.evolution = EvolutionLevel(new_level)

        elif event_type == "TURN_SWITCH":
            self.game.current_player_turn = data.get("isPlayerTurn", True)

        elif event_type == "GAME_END":
            pass