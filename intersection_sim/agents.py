from mesa import Agent
import random


class RoadCell(Agent):
    """A simple agent representing a road cell in the traffic simulation."""

    def __init__(self, pos, model):
        """Initialize a road cell at the specified position.

        Args:
            pos: Tuple (x,y) representing the cell's position
            model: Reference to the main model instance
        """
        super().__init__(pos, model)
        self.pos = pos


class TrafficLightAgent(Agent):
    """Agent representing a traffic light that controls vehicle flow at intersections."""

    def __init__(self, pos, model):
        """Initialize a traffic light agent.

        Args:
            pos: Tuple (x,y) representing the light's position
            model: Reference to the main model instance
        """
        super().__init__(pos, model)
        self.pos = pos
        self.state = "Red"  # Default state, updated in first step
        self.is_horizontal = self._determine_orientation()  # Determine orientation once

    def _determine_orientation(self):
        """Determine if this light controls horizontal (E-W) traffic.

        Returns:
            bool: True if controls horizontal traffic, False for vertical
        """
        # West incoming (Eastbound)
        if (self.pos[0] == self.model.center_start - 1 and
                self.pos[1] in self.model.incoming_lanes):
            return True
        # East incoming (Westbound)
        if (self.pos[0] == self.model.center_end and
                self.pos[1] in self.model.outgoing_lanes):
            return True
        return False  # Vertical (N-S)

    def get_lane_cells(self):
        """Get all cells in the lane controlled by this traffic light.

        Returns:
            list: Coordinates of all cells in the controlled lane
        """
        cells = []
        model = self.model

        if self.is_horizontal:
            # West approach lane
            if self.pos[0] == model.center_start - 1:
                for x in range(0, model.center_start):
                    cells.append((x, self.pos[1]))
            # East approach lane
            else:
                for x in range(model.center_end, model.grid.width):
                    cells.append((x, self.pos[1]))
        else:
            # North approach lane
            if self.pos[1] == model.center_start - 1:
                for y in range(0, model.center_start):
                    cells.append((self.pos[0], y))
            # South approach lane
            else:
                for y in range(model.center_end, model.grid.height):
                    cells.append((self.pos[0], y))
        return cells

    def step(self):
        """Update light state based on model's current phase."""
        if self.model.phase_transition is not None:
            self.state = "Red"
        else:
            self.state = "Green" if (self.is_horizontal == self.model.horizontal_phase) else "Red"


class VehicleAgent(Agent):
    """Agent representing a vehicle in the traffic simulation."""

    # Class attributes
    colors = ["Red", "Blue", "Green", "Purple"]
    directions = {
        (1, 0): "east",
        (-1, 0): "west",
        (0, 1): "south",
        (0, -1): "north"
    }

    def __init__(self, unique_id, model, start_pos, car_spawn_rate=15):
        """Initialize a vehicle agent.

        Args:
            unique_id: Unique identifier for the agent
            model: Reference to the main model instance
            start_pos: Tuple (x,y) representing starting position
            car_spawn_rate: Probability of vehicle spawning (0-100)
        """
        super().__init__(unique_id, model)
        self.pos = start_pos
        self.direction = self._determine_direction(start_pos)

        # Movement attributes
        self.speed = 1
        self.sensing_range = 5
        self.steps_taken = 0

        # State flags
        self.is_stopped_for_queue = False
        self.is_stopped_at_light = False
        self.has_passed_light = False

        # Appearance
        self.color = random.choice(self.colors)
        self.image = self._get_image_path()

        # Statistics
        self.waiting_time = 0
        self.car_spawn_rate = car_spawn_rate

    def _get_image_path(self):
        """Get the image path based on vehicle color and direction.

        Returns:
            str: Path to vehicle image asset
        """
        direction_name = self.directions.get(self.direction, "east")
        return f"intersection_sim/assets/cars/{self.color}/{self.color}_{direction_name}.png"

    def _determine_direction(self, start_pos):
        """Determine travel direction based on spawn position.

        Args:
            start_pos: Tuple (x,y) representing spawn position

        Returns:
            Tuple: (dx, dy) direction vector
        """
        width, height = self.model.grid.width, self.model.grid.height

        # West incoming (Eastbound)
        if start_pos[0] == 0 and start_pos[1] in self.model.incoming_lanes:
            return (1, 0)
        # East incoming (Westbound)
        if start_pos[0] == width - 1 and start_pos[1] in self.model.outgoing_lanes:
            return (-1, 0)
        # North incoming (Southbound)
        if start_pos[1] == 0 and start_pos[0] in self.model.outgoing_lanes:
            return (0, 1)
        # South incoming (Northbound)
        if start_pos[1] == height - 1 and start_pos[0] in self.model.incoming_lanes:
            return (0, -1)
        return (0, 0)

    def detect_queue(self):
        """Check for slower vehicles ahead in the same lane.

        Returns:
            bool: True if queue detected, False otherwise
        """
        if self.speed == 0:
            return False

        for i in range(1, self.sensing_range + 1):
            check_x = self.pos[0] + self.direction[0] * i
            check_y = self.pos[1] + self.direction[1] * i

            if (0 <= check_x < self.model.grid.width and
                    0 <= check_y < self.model.grid.height):
                cell_contents = self.model.grid.get_cell_list_contents((check_x, check_y))
                for agent in cell_contents:
                    if isinstance(agent, VehicleAgent) and agent.speed < self.speed:
                        return True
        return False

    def is_approaching_intersection(self):
        """Check if vehicle is about to enter intersection.

        Returns:
            bool: True if approaching intersection, False otherwise
        """
        next_x = self.pos[0] + self.direction[0]
        next_y = self.pos[1] + self.direction[1]
        return ((next_x in self.model.center_range and self.pos[1] in self.model.center_range) or
                (self.pos[0] in self.model.center_range and next_y in self.model.center_range))

    def is_at_traffic_light(self):
        """Check if vehicle is at its controlling traffic light.

        Returns:
            bool: True if at traffic light position, False otherwise
        """
        light_pos = None
        # Eastbound (West incoming)
        if self.direction == (1, 0):
            lane_idx = (self.model.incoming_lanes.index(self.pos[1])
                        if self.pos[1] in self.model.incoming_lanes else 0)
            light_pos = (self.model.center_start - 1, self.model.incoming_lanes[lane_idx])
        # Westbound (East incoming)
        elif self.direction == (-1, 0):
            lane_idx = (self.model.outgoing_lanes.index(self.pos[1])
                        if self.pos[1] in self.model.outgoing_lanes else 0)
            light_pos = (self.model.center_end, self.model.outgoing_lanes[lane_idx])
        # Southbound (North incoming)
        elif self.direction == (0, 1):
            lane_idx = (self.model.outgoing_lanes.index(self.pos[0])
                        if self.pos[0] in self.model.outgoing_lanes else 0)
            light_pos = (self.model.outgoing_lanes[lane_idx], self.model.center_start - 1)
        # Northbound (South incoming)
        elif self.direction == (0, -1):
            lane_idx = (self.model.incoming_lanes.index(self.pos[0])
                        if self.pos[0] in self.model.incoming_lanes else 0)
            light_pos = (self.model.incoming_lanes[lane_idx], self.model.center_end)

        return self.pos == light_pos

    def check_traffic_light_state(self):
        """Get the state of the traffic light at current position.

        Returns:
            str: Current light state ("Red" or "Green"), or None if no light present
        """
        if not self.is_at_traffic_light():
            return None

        light_agents = self.model.grid.get_cell_list_contents(self.pos)
        for agent in light_agents:
            if isinstance(agent, TrafficLightAgent):
                return agent.state
        return None

    def is_in_intersection(self):
        """Check if vehicle is inside intersection area.

        Returns:
            bool: True if in intersection, False otherwise
        """
        return (self.pos[0] in self.model.center_range and
                self.pos[1] in self.model.center_range)

    def step(self):
        """Execute one simulation step for the vehicle."""
        # Reset passed light flag when exiting intersection
        if not self.is_in_intersection():
            self.has_passed_light = False

        # Traffic light behavior
        if not self.has_passed_light and self.is_at_traffic_light():
            light_state = self.check_traffic_light_state()
            if light_state == "Red":
                self.speed = 0
                self.is_stopped_at_light = True
                self.is_stopped_for_queue = False
                self.waiting_time += 1
                return
            elif light_state == "Green" and self.is_stopped_at_light:
                self.speed = 1
                self.is_stopped_at_light = False
                self.has_passed_light = True

        # Update waiting time statistics
        if self.speed == 0:
            self.waiting_time += 1
        else:
            self.waiting_time = 0

        # Handle approaching intersection
        if self.is_approaching_intersection() and not self.is_at_traffic_light():
            self._handle_intersection_approach()

        # Queue detection and movement
        if not self.is_stopped_at_light:
            if self.detect_queue():
                self.speed = 0
                self.is_stopped_for_queue = True
            else:
                if self.is_stopped_for_queue and not self.detect_queue():
                    self.speed = 1
                    self.is_stopped_for_queue = False
                else:
                    self.speed = 1

        # Execute movement if speed > 0
        if self.speed > 0:
            self._move_forward()

    def _handle_intersection_approach(self):
        """Handle behavior when approaching an intersection."""
        light_pos = None
        # Determine light position based on direction
        if self.direction == (1, 0):  # Eastbound
            lane_idx = (self.model.incoming_lanes.index(self.pos[1])
                        if self.pos[1] in self.model.incoming_lanes else 0)
            light_pos = (self.model.center_start - 1, self.model.incoming_lanes[lane_idx])
        elif self.direction == (-1, 0):  # Westbound
            lane_idx = (self.model.outgoing_lanes.index(self.pos[1])
                        if self.pos[1] in self.model.outgoing_lanes else 0)
            light_pos = (self.model.center_end, self.model.outgoing_lanes[lane_idx])
        elif self.direction == (0, 1):  # Southbound
            lane_idx = (self.model.outgoing_lanes.index(self.pos[0])
                        if self.pos[0] in self.model.outgoing_lanes else 0)
            light_pos = (self.model.outgoing_lanes[lane_idx], self.model.center_start - 1)
        elif self.direction == (0, -1):  # Northbound
            lane_idx = (self.model.incoming_lanes.index(self.pos[0])
                        if self.pos[0] in self.model.incoming_lanes else 0)
            light_pos = (self.model.incoming_lanes[lane_idx], self.model.center_end)

        # Check light state if position found
        if light_pos:
            light_agents = self.model.grid.get_cell_list_contents(light_pos)
            for agent in light_agents:
                if isinstance(agent, TrafficLightAgent) and agent.state == "Red":
                    self.speed = 0
                    self.is_stopped_for_queue = False
                    return

    def _move_forward(self):
        """Move vehicle forward in its current direction."""
        new_x = self.pos[0] + self.direction[0]
        new_y = self.pos[1] + self.direction[1]

        # Check bounds
        if not (0 <= new_x < self.model.grid.width and 0 <= new_y < self.model.grid.height):
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.current_agents -= 1
            self.model.total_exited += 1
            return

        # Check for obstacles
        cell_contents = self.model.grid.get_cell_list_contents((new_x, new_y))
        road_present = any(isinstance(agent, RoadCell) for agent in cell_contents)
        vehicle_present = any(isinstance(agent, VehicleAgent) for agent in cell_contents)

        if road_present and not vehicle_present:
            self.model.grid.move_agent(self, (new_x, new_y))
            self.steps_taken += 1
