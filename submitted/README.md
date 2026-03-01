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

```bash
make run MAP=<map-filename.txt>
```
or
```bash
make run-visual MAP=<map-filename.txt>
```
### Installation

Install dependencies to lint:

```bash
make venv
. venv/bin/activate
make lint
```

## Resources

### Algorithm & Theory References

  https://cp-algorithms.com/index.html

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

### Algorithm explanation

I time expanded my graph and used reverse dijkstra.
It is not global optimal but has great time complexity and is
shorter and easier to debug than min cost max flow and path decomposition.
Even though the algorithm is naive the time-expansion and reversed implementation
make is pretty optimal in my opinion.

```
D1-1
D1-2, D2-1
D1-3, D2-2
D2-3

==================
== START STATE  ==
==================
name: start
zone: start_hub
color: green (##)
max_drones: 5
current occupancy: 2

==================
== TURN #: 1 ==
==================

name: start
zone: start_hub
color: green (##)
max_drones: 5
current occupancy: 1

name: waypoint1
zone: normal
color: blue (##)
max_drones: 1
current occupancy: 1

==================
== TURN #: 2 ==
==================

name: waypoint1
zone: normal
color: blue (##)
max_drones: 1
current occupancy: 1

name: waypoint2
zone: normal
color: blue (##)
max_drones: 1
current occupancy: 1

==================
== TURN #: 3 ==
==================

name: waypoint2
zone: normal
color: blue (##)
max_drones: 1
current occupancy: 1

name: goal
zone: end_hub
color: red (##)
max_drones: ∞
current occupancy: 1

==================
== TURN #: 4 ==
==================

name: goal
zone: end_hub
color: red (##)
max_drones: ∞
current occupancy: 2
```

### AI Usage Disclosure

AI tools were used in a limited and controlled manner for:

- Structuring documentation and refining README wording  
- Assisting in resolving mypy type inference issues  
- Motivation to complete project and continue debugging
- Unit testing with pytest (not included in this repo btw)
- Some ascii and print functions

