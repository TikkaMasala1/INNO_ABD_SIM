from mesa import Agent
import random


class RoadCell(Agent):
    """A simple agent representing a road cell in the traffic simulation."""
    def __init__(self, pos, model):
        super().__init__(pos, model)
        self.pos = pos


class TrafficLightAgent(Agent):
    """Agent representing a traffic light that controls vehicle flow at intersections."""
    def __init__(self, pos, model):
        super().__init__(pos, model)
        self.pos = pos
        self.state = "Red"  # Default state, updated in first step
        self.is_horizontal = self._determine_orientation()  # Determine orientation once

    def _determine_orientation(self):
        """Determine if this light controls horizontal (E-W) traffic."""
        if (self.pos[0] == self.model.center_start - 1 and
                self.pos[1] in self.model.incoming_lanes):
            return True
        if (self.pos[0] == self.model.center_end and
                self.pos[1] in self.model.outgoing_lanes):
            return True
        return False

    def get_lane_cells(self):
        """Get all cells in the lane controlled by this traffic light."""
        cells = []
        model = self.model
        if self.is_horizontal:
            if self.pos[0] == model.center_start - 1:
                for x in range(0, model.center_start):
                    cells.append((x, self.pos[1]))
            else:
                for x in range(model.center_end, model.grid.width):
                    cells.append((x, self.pos[1]))
        else:
            if self.pos[1] == model.center_start - 1:
                for y in range(0, model.center_start):
                    cells.append((self.pos[0], y))
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
    colors = ["Red", "Blue", "Green", "Purple"]
    directions = {
        (1, 0): "east",
        (-1, 0): "west",
        (0, 1): "south",
        (0, -1): "north"
    }

    def __init__(self, unique_id, model, start_pos, car_spawn_rate=15, speed=1):
        super().__init__(unique_id, model)
        self.pos = start_pos
        self.direction = self._determine_direction(start_pos)
        self.speed = speed
        self.original_speed = speed
        self.sensing_range = 5
        self.steps_taken = 0
        self.is_stopped_for_queue = False
        self.is_stopped_at_light = False
        self.has_passed_light = False
        self.color = random.choice(self.colors)
        self.image = self._get_image_path()
        self.waiting_time = 0
        self.car_spawn_rate = car_spawn_rate

    def _get_image_path(self):
        direction_name = self.directions.get(self.direction, "east")
        return f"intersection_sim/assets/cars/{self.color}/{self.color}_{direction_name}.png"

    def _determine_direction(self, start_pos):
        width, height = self.model.grid.width, self.model.grid.height
        if start_pos[0] == 0 and start_pos[1] in self.model.incoming_lanes:
            return (1, 0)
        if start_pos[0] == width - 1 and start_pos[1] in self.model.outgoing_lanes:
            return (-1, 0)
        if start_pos[1] == 0 and start_pos[0] in self.model.outgoing_lanes:
            return (0, 1)
        if start_pos[1] == height - 1 and start_pos[0] in self.model.incoming_lanes:
            return (0, -1)
        return (0, 0)

    def detect_queue(self):
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
        next_x = self.pos[0] + self.direction[0]
        next_y = self.pos[1] + self.direction[1]
        return ((next_x in self.model.center_range and self.pos[1] in self.model.center_range) or
                (self.pos[0] in self.model.center_range and next_y in self.model.center_range))

    def is_at_traffic_light(self):
        light_pos = None
        if self.direction == (1, 0):
            lane_idx = (self.model.incoming_lanes.index(self.pos[1])
                        if self.pos[1] in self.model.incoming_lanes else 0)
            light_pos = (self.model.center_start - 1, self.model.incoming_lanes[lane_idx])
        elif self.direction == (-1, 0):
            lane_idx = (self.model.outgoing_lanes.index(self.pos[1])
                        if self.pos[1] in self.model.outgoing_lanes else 0)
            light_pos = (self.model.center_end, self.model.outgoing_lanes[lane_idx])
        elif self.direction == (0, 1):
            lane_idx = (self.model.outgoing_lanes.index(self.pos[0])
                        if self.pos[0] in self.model.outgoing_lanes else 0)
            light_pos = (self.model.outgoing_lanes[lane_idx], self.model.center_start - 1)
        elif self.direction == (0, -1):
            lane_idx = (self.model.incoming_lanes.index(self.pos[0])
                        if self.pos[0] in self.model.incoming_lanes else 0)
            light_pos = (self.model.incoming_lanes[lane_idx], self.model.center_end)
        return self.pos == light_pos

    def get_distance_to_traffic_light(self):
        light_pos = None
        if self.direction == (1, 0):
            lane_idx = (self.model.incoming_lanes.index(self.pos[1])
                        if self.pos[1] in self.model.incoming_lanes else 0)
            light_pos = (self.model.center_start - 1, self.model.incoming_lanes[lane_idx])
        elif self.direction == (-1, 0):
            lane_idx = (self.model.outgoing_lanes.index(self.pos[1])
                        if self.pos[1] in self.model.outgoing_lanes else 0)
            light_pos = (self.model.center_end, self.model.outgoing_lanes[lane_idx])
        elif self.direction == (0, 1):
            lane_idx = (self.model.outgoing_lanes.index(self.pos[0])
                        if self.pos[0] in self.model.outgoing_lanes else 0)
            light_pos = (self.model.outgoing_lanes[lane_idx], self.model.center_start - 1)
        elif self.direction == (0, -1):
            lane_idx = (self.model.incoming_lanes.index(self.pos[0])
                        if self.pos[0] in self.model.incoming_lanes else 0)
            light_pos = (self.model.incoming_lanes[lane_idx], self.model.center_end)
        if light_pos and self.pos != light_pos:
            if self.direction == (1, 0):
                return light_pos[0] - self.pos[0]
            elif self.direction == (-1, 0):
                return self.pos[0] - light_pos[0]
            elif self.direction == (0, 1):
                return light_pos[1] - self.pos[1]
            elif self.direction == (0, -1):
                return self.pos[1] - light_pos[1]
        return None

    def check_traffic_light_state(self):
        if not self.is_at_traffic_light():
            return None
        light_agents = self.model.grid.get_cell_list_contents(self.pos)
        for agent in light_agents:
            if isinstance(agent, TrafficLightAgent):
                return agent.state
        return None

    def is_in_intersection(self):
        return (self.pos[0] in self.model.center_range and
                self.pos[1] in self.model.center_range)

    def step(self):
        if not self.is_in_intersection():
            self.has_passed_light = False
        distance = self.get_distance_to_traffic_light()
        if distance is not None and not self.is_stopped_at_light and not self.is_stopped_for_queue:
            slowdown_distance = self.original_speed * 2
            if distance <= slowdown_distance:
                self.speed = 1
            else:
                self.speed = self.original_speed
        if not self.has_passed_light and self.is_at_traffic_light():
            light_state = self.check_traffic_light_state()
            if light_state == "Red":
                self.speed = 0
                self.is_stopped_at_light = True
                self.is_stopped_for_queue = False
                self.waiting_time += 1
                return
            elif light_state == "Green" and self.is_stopped_at_light:
                self.speed = self.original_speed
                self.is_stopped_at_light = False
                self.has_passed_light = True
        if self.speed == 0:
            self.waiting_time += 1
        else:
            self.waiting_time = 0
        if self.is_approaching_intersection() and not self.is_at_traffic_light():
            self._handle_intersection_approach()
        if not self.is_stopped_at_light:
            if self.detect_queue():
                self.speed = 0
                self.is_stopped_for_queue = True
            else:
                if self.is_stopped_for_queue and not self.detect_queue():
                    self.speed = self.original_speed
                    self.is_stopped_for_queue = False
                else:
                    self.speed = max(1, self.speed)
        if self.speed > 0:
            self._move_forward()

    def _handle_intersection_approach(self):
        light_pos = None
        if self.direction == (1, 0):
            lane_idx = (self.model.incoming_lanes.index(self.pos[1])
                        if self.pos[1] in self.model.incoming_lanes else 0)
            light_pos = (self.model.center_start - 1, self.model.incoming_lanes[lane_idx])
        elif self.direction == (-1, 0):
            lane_idx = (self.model.outgoing_lanes.index(self.pos[1])
                        if self.pos[1] in self.model.outgoing_lanes else 0)
            light_pos = (self.model.center_end, self.model.outgoing_lanes[lane_idx])
        elif self.direction == (0, 1):
            lane_idx = (self.model.outgoing_lanes.index(self.pos[0])
                        if self.pos[0] in self.model.outgoing_lanes else 0)
            light_pos = (self.model.outgoing_lanes[lane_idx], self.model.center_start - 1)
        elif self.direction == (0, -1):
            lane_idx = (self.model.incoming_lanes.index(self.pos[0])
                        if self.pos[0] in self.model.incoming_lanes else 0)
            light_pos = (self.model.incoming_lanes[lane_idx], self.model.center_end)
        if light_pos:
            light_agents = self.model.grid.get_cell_list_contents(light_pos)
            for agent in light_agents:
                if isinstance(agent, TrafficLightAgent) and agent.state == "Red":
                    self.speed = 0
                    self.is_stopped_for_queue = False
                    return

    def _move_forward(self):
        """Move vehicle forward up to speed grid spaces, filling gaps if possible."""
        max_steps = int(self.speed)
        if max_steps <= 0:
            return

        last_valid_pos = self.pos  # Start with current position as valid
        width, height = self.model.grid.width, self.model.grid.height

        # Check each cell up to max_steps
        for i in range(1, max_steps + 1):
            check_x = self.pos[0] + self.direction[0] * i
            check_y = self.pos[1] + self.direction[1] * i

            # Stop if out of bounds
            if not (0 <= check_x < width and 0 <= check_y < height):
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
                self.model.current_agents -= 1
                self.model.total_exited += 1
                return

            # Check cell contents
            cell_contents = self.model.grid.get_cell_list_contents((check_x, check_y))
            road_present = any(isinstance(agent, RoadCell) for agent in cell_contents)
            vehicle_present = any(isinstance(agent, VehicleAgent) for agent in cell_contents)

            # If no road or another vehicle is present, stop checking further
            if not road_present or vehicle_present:
                break

            # Update last valid position
            last_valid_pos = (check_x, check_y)

        # Move to the last valid position if it's different from current
        if last_valid_pos != self.pos:
            self.model.grid.move_agent(self, last_valid_pos)
            steps_moved = abs(last_valid_pos[0] - self.pos[0]) + abs(last_valid_pos[1] - self.pos[1])
            self.steps_taken += steps_moved