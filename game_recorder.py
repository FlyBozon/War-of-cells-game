import os
import pygame
import time
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import json
import logging
import datetime
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

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BACKGROUND_COLOR = (10, 10, 20)

CELL_RADIUS = 30
POINT_GROWTH_INTERVAL = 3000  # ms
BALL_SPEED = 2
BALL_RADIUS = 5
BRIDGE_WIDTH = 3

PLAYER_COLOR = (50, 100, 255)  # Blue
ENEMY_COLOR = (255, 50, 50)  # Red
EMPTY_COLOR = (50, 50, 50)  # Dark Gray
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

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


def generate_game_id(level_name=None, completed=False):
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    completion_status = "completed" if completed else "in_progress"

    if level_name is None:
        return f"game_{timestamp}_{completion_status}"
    else:
        return f"{level_name}_{timestamp}_{completion_status}"

class GameRecorder:
    def __init__(self, game):
        self.game = game

        self.game_type = game.game_type
        if game.game_type==GameType.ONLINE: #check is it correct, to make option to send data about game during the game
            self.send_matedata=True
        else: self.send_matedata=False

        self.recording = False
        self.events = []
        self.cell_id_map = {}
        self.start_time = 0
        self.game_id = None
        self.metadata = {}

    def start_recording(self):
        self.recording = True
        self.events = []
        self.cell_id_map = {}
        self.start_time = time.time()
        self.game_id = generate_game_id()

        for i, cell in enumerate(self.game.cells):
            self.cell_id_map[cell] = i

        self.metadata = {
            "gameId": self.game_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "level": self.game.current_level,
            "gameType": self.game.game_type.to_string(),
            "turnBased": self.game.turn_based_mode,
            "aiEnabled": self.game.ai_enabled,
            "aiDifficulty": self.game.ai_difficulty,
            "result": None,
            "duration": 0
        }

        self.record_event("GAME_START", {
            "cells": [self._serialize_cell(cell) for cell in self.game.cells]
        })

    def stop_recording(self, result):
        if not self.recording:
            return

        self.recording = False
        self.metadata["result"] = result
        self.metadata["duration"] = time.time() - self.start_time

        self.record_event("GAME_END", {
            "result": result,
            "score": self.game.points,
            "time": self.game.time_taken,
            "cells": [self._serialize_cell(cell) for cell in self.game.cells]
        })

    def record_event(self, event_type, data):
        if not self.recording:
            return

        timestamp = time.time() - self.start_time
        self.events.append({
            "timestamp": timestamp,
            "eventType": event_type,
            "data": data
        })

    def save_to_json(self):
        if not self.events:
            return None

        os.makedirs("saved_games/json", exist_ok=True)

        game_history = {
            "metadata": self.metadata,
            "events": self.events
        }

        filename = f"saved_games/json/{self.game_id}.json"
        with open(filename, "w") as f:
            json.dump(game_history, f, indent=2)

        return filename

    def save_to_xml(self):
        if not self.events:
            return None

        os.makedirs("saved_games/xml", exist_ok=True)

        root = ET.Element("GameHistory")

        metadata_elem = ET.SubElement(root, "Metadata")
        for key, value in self.metadata.items():
            meta_item = ET.SubElement(metadata_elem, key)
            meta_item.text = str(value)

        events_elem = ET.SubElement(root, "Events")
        for event in self.events:
            event_elem = ET.SubElement(events_elem, "Event")
            event_elem.set("timestamp", str(event["timestamp"]))
            event_elem.set("type", event["eventType"])

            for key, value in event["data"].items():
                if isinstance(value, list):
                    list_elem = ET.SubElement(event_elem, key)
                    for item in value:
                        if isinstance(item, dict):
                            item_elem = ET.SubElement(list_elem, "Item")
                            for k, v in item.items():
                                item_attr = ET.SubElement(item_elem, k)
                                item_attr.text = str(v)
                        else:
                            item_elem = ET.SubElement(list_elem, "Item")
                            item_elem.text = str(item)
                else:
                    data_elem = ET.SubElement(event_elem, key)
                    data_elem.text = str(value)

        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")

        filename = f"saved_games/xml/{self.game_id}.xml"
        with open(filename, "w") as f:
            f.write(xml_str)

        return filename

    def save_to_mongodb(self, connection_string=None):
        try:
            import pymongo
            from mongodb_config import DEFAULT_CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME
        except ImportError:
            logger.error("MongoDB support not available. Install pymongo package.")
            return None

        if not self.events:
            logger.error("No events to save")
            return None

        try:
            conn_str = connection_string or DEFAULT_CONNECTION_STRING
            client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)

            client.server_info()

            db = client[DATABASE_NAME]
            collection = db[COLLECTION_NAME]

            game_history = {
                "metadata": self.metadata,
                "events": self.events,
                "timestamp": datetime.datetime.now()
            }

            result = collection.insert_one(game_history)
            logger.info(f"Game history saved to MongoDB with ID: {result.inserted_id}")
            return str(result.inserted_id)

        except pymongo.errors.ServerSelectionTimeoutError:
            logger.error("Could not connect to MongoDB server. Is it running?")
            return None
        except Exception as e:
            logger.error(f"MongoDB error: {e}")
            return None

    def _serialize_cell(self, cell):
        if cell not in self.cell_id_map:
            self.cell_id_map[cell] = len(self.cell_id_map)

        return {
            "id": self.cell_id_map[cell],
            "x": cell.x,
            "y": cell.y,
            "type": cell.cell_type.name,
            "shape": cell.shape.name,
            "evolution": cell.evolution.value,
            "points": cell.points
        }
