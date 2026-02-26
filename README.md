*This project has been created as part of the 42 curriculum by andmarti.*

# Fly-in

## Description

Fly-in is a drone routing simulation system designed to move multiple drones
from a single start zone to a target end zone while minimizing the total
number of simulation turns.

The project parses a structured map file describing:

- Zones (start_hub, end_hub, hub)
- Zone types (normal, restricted, priority, blocked)
- Zone capacity constraints (max_drones)
- Connection capacity constraints (max_link_capacity)
- Number of drones

The simulation engine computes valid turn-by-turn drone movements while
strictly enforcing:

- Zone occupancy rules
- Connection capacity rules
- Movement costs based on zone type
- Multi-turn transitions for restricted zones
- Conflict and deadlock avoidance

The implementation is fully object-oriented and completely typesafe
(using flake8 and mypy).

---

## Instructions

### Installation

Install dependencies:

```bash

make install
```

## Resources

### Algorithm & Theory References

- Cormen, Leiserson, Rivest, Stein — *Introduction to Algorithms (CLRS)*  
  (Dijkstra’s algorithm and shortest-path theory)

- Dijkstra, E. W. (1959).  
  *A note on two problems in connexion with graphs.*

- Ahuja, Magnanti, Orlin — *Network Flows: Theory, Algorithms, and Applications*  
  (Time-expanded networks and capacity-constrained routing concepts)

- Multi-Agent Path Finding (MAPF) literature  
  (Concepts related to scheduling and conflict avoidance)

---

### Python Documentation

- Python `heapq` module documentation  
  https://docs.python.org/3/library/heapq.html

- Python `typing` module documentation  
  https://docs.python.org/3/library/typing.html

- PEP 484 — Type Hints  
  https://peps.python.org/pep-0484/

- PEP 257 — Docstring Conventions  
  https://peps.python.org/pep-0257/

- flake8 documentation  
  https://flake8.pycqa.org/

- mypy documentation  
  https://mypy.readthedocs.io/

---

An "Algorithm explanation" section describing the pathfinding approach and design decisions.
Documentation of visual representation features and how they enhance user experience.
Example input and expected output demonstrating the program's functionality.

### AI Usage Disclosure

AI tools were used in a limited and controlled manner for:

- Structuring documentation and refining README wording  
- Clarifying theoretical explanations of Dijkstra and time-expanded graphs  
- Assisting in resolving mypy type inference issues  
- Improving clarity of docstrings and comments  

All algorithm design decisions, architectural structure, parsing logic,
capacity management, scheduling strategy, and debugging were implemented
manually and fully understood before integration.

No core pathfinding or simulation logic was generated blindly by AI.
Peer discussions were used to validate correctness and optimization strategy.
