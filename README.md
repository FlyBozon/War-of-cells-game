# War of Cells Game – Documentation
![alt text](gif_game_ui/first_level_and_pseudo_ai_enemy.gif)

## Features

### Game Scene
- The game scene is implemented through the `Game` class, which includes its own properties and parameters.

### Units as Objects
- Each unit is an individual object inheriting from the `Cell` class.

### Unit Interactivity
- Units are clickable and draggable.
- Context menus allow for creating and removing connections between units.
- Although dragging units isn’t necessary for gameplay, a level editor was implemented to fulfill this purpose. It allows rearranging cells and modifying their parameters.

### Unit Control
- Players can create custom levels using the built-in level editor.
- Levels are saved in JSON format with unit parameters, layout, and performance data. Example:

```json
{
  "summary": {
    "total_levels": 5,
    "levels": {
      "level1": {
        "stars": 1,
        "time": "00:59",
        "score": 740
      },
      "level2": {
        "stars": 3,
        "time": "01:43",
        "score": 1685
      } ...
    }
  }
}
```

```json
"level2": {
  "map": [
    "##########",
    "#   e  e #",
    "#        #",
    "#    u   #",
    "#        #",
    "# u   e  #",
    "#        #",
    "#  o   u #",
    "#        #",
    "##########"
  ],
  "description": {
    "e": [
      {
        "points": 10,
        "evolution": 1,
        "kind": "c",
        "color": "red"
      }
      ...
    ],
    "u": [
      {
        "points": 15,
        "evolution": 2,
        "kind": "c",
        "color": "blue"
      }
      ...
    ],
    "o": [
      {
        "points": 10,
        "evolution": 1,
        "kind": "c",
        "color": "no"
      }
      ...
    ]
  }
}
```

_Where `u` = user, `e` = enemy, `o` = open cells_

- Users can also reorder levels or edit specific ones using the level editor. *(Note: the game must be restarted for changes to apply.)*
- Units are moved by selecting and repositioning them on the grid.
- Players can switch between red and blue units using the spacebar.

### Move & Attack Highlighting
- Possible moves and attacks are visually highlighted, following the same logic as the pseudo AI.
- Moves are shown in both "A" and "H" modes (may require pressing "H" multiple times).

### Combat System
- Takes unit types, evolution levels, and multipliers into account.
- Connections between cells have values based on their distance.
- Units of the same color support each other, increasing attack frequency. The more supporting units, the higher the multiplier and frequency.
- Evolution Levels:
  - 1–15 points – Level 1
  - 16–35 points – Level 2
  - 35+ points – Level 3
- Shape multipliers:
  - Circle – 1x  
  - Triangle – 2x  
  - Square – 3x

### Turn-Based System & Round Timer
- Turn-based gameplay with a time limit per turn.
- Red units can be controlled by a pseudo AI in this mode.

### AI Suggestions
- Pressing "H" in the terminal provides suggestions for the best possible moves (if any are available). Try modifying or removing connections if suggestions don't appear.

![alt text](gif_game_ui/move_suggestions.gif)

![alt text](gif_game_ui/move_suggestions_2.gif)


### Logger
- Displays logs both in the terminal.
- Rotating log system informs players about game state and actions.

---

## Installation

To install the required libraries, run:

```bash
pip install -r requirements.txt
```

---

## Controls

- **Spacebar** – switch between players  
- **T** – toggle turn-based mode  
- **A** – enable/disable pseudo AI  
- **D** – change AI difficulty (AI typically loses but can occasionally win on hard mode)  
- **H** – show best move suggestions in the terminal
- **S** - save game progress

---

## Game End

After finishing a level:
- Points are calculated based on time and performance.
- Stars are awarded accordingly.
- Results are saved to a `JSON` file and shown in the game menu.
- The next level is unlocked once the previous one is completed.

---

## Game Mode Configuration

A mode selection feature was added, allowing the player to choose between:
- Single Player
- Local Multiplayer
- Online Multiplayer

![choose game type](gif_game_ui/choose_game_type.gif)

Permissions and functionality are managed based on the selected mode:

| Feature          | Single Player | Local Multiplayer | Online Multiplayer             |
|------------------|---------------|-------------------|--------------------------------|
| AI               | ✅             | ❌                | ❌                              |
| Turn-based mode  | ✅             | ✅                | ✅ (only mode available)        |
| AI Help (H key)  | ❌ (toggle)    | ❌ (toggle)       | ❌ (toggle)                     |

*A pseudo AI is only useful in single-player mode.*

The menu includes an interface for selecting the game mode.

Game history is saved in both JSON and XML formats. An attempt was made to implement MongoDB support, but it couldn't be tested due to server issues.

Players can also save the current game state with **S**. Upon reopening the game, it checks for unfinished sessions and offers to resume from the last point.

A playback feature with speed control was also started, but remains incomplete.

---
