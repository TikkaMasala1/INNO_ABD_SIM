from mesa import Agent
import random

class RoadCell(Agent):
    def __init__(self, pos, model):
        super().__init__(pos, model)
        self.pos = pos

class TrafficLightAgent(Agent):
    def __init__(self, pos, model):
        super().__init__(pos, model)
        self.pos = pos
        self.state = "Red"  # Default state, updated in first step
        self.is_horizontal = self.is_horizontal_light()  # Determine orientation once

    def is_horizontal_light(self):
        """Determine if this traffic light controls horizontal (E-W) traffic."""
        if self.pos[0] == self.model.center_start - 1 and self.pos[1] in self.model.incoming_lanes:
            return True  # West incoming (Eastbound)
        if self.pos[0] == self.model.center_end and self.pos[1] in self.model.outgoing_lanes:
            return True  # East incoming (Westbound)
        return False  # Vertical (N-S)

    def step(self):
        """Update state based on the model's current phase."""
        self.state = "Green" if (self.is_horizontal == self.model.horizontal_phase) else "Red"

class VehicleAgent(Agent):
    colors = ["Red", "Blue", "Green", "Purple"]
    directions = {
        (1, 0): "east",
        (-1, 0): "west",
        (0, 1): "south",
        (0, -1): "north"
    }
    def __init__(self, unique_id, model, start_pos, car_spawn_rate=15):
        super().__init__(unique_id, model)
        self.pos = start_pos
        self.steps_taken = 0
        self.direction = self.determine_direction(start_pos)
        self.speed = 1
        self.sensing_range = 5
        self.is_stopped_for_queue = False
        self.is_stopped_at_light = False
        self.color = random.choice(self.colors)
        self.image = self.get_image_path()
        self.car_spawn_rate = car_spawn_rate

    def get_image_path(self):
        direction_name = self.directions.get(self.direction, "east")
        return f"intersection_sim/assets/cars/{self.color}/{self.color}_{direction_name}.png"

    def determine_direction(self, start_pos):
        """Determine direction using model attributes."""
        width, height = self.model.grid.width, self.model.grid.height
        if start_pos[0] == 0 and start_pos[1] in self.model.incoming_lanes:  # West incoming
            return (1, 0)  # East
        if start_pos[0] == width - 1 and start_pos[1] in self.model.outgoing_lanes:  # East incoming
            return (-1, 0)  # West
        if start_pos[1] == 0 and start_pos[0] in self.model.outgoing_lanes:  # North incoming
            return (0, 1)  # South
        if start_pos[1] == height - 1 and start_pos[0] in self.model.incoming_lanes:  # South incoming
            return (0, -1)  # North
        return (0, 0)

    def detect_queue(self):
        """Detect if there's a vehicle ahead in the same lane."""
        if self.speed == 0:
            return False

        for i in range(1, self.sensing_range + 1):
            check_x = self.pos[0] + self.direction[0] * i
            check_y = self.pos[1] + self.direction[1] * i
            if 0 <= check_x < self.model.grid.width and 0 <= check_y < self.model.grid.height:
                cell_contents = self.model.grid.get_cell_list_contents((check_x, check_y))
                for agent in cell_contents:
                    if isinstance(agent, VehicleAgent) and agent.speed < self.speed:
                        return True
        return False

    def is_approaching_intersection(self):
        """Check if the vehicle is about to enter the intersection."""
        next_x = self.pos[0] + self.direction[0]
        next_y = self.pos[1] + self.direction[1]
        return (next_x in self.model.center_range and self.pos[1] in self.model.center_range) or \
               (self.pos[0] in self.model.center_range and next_y in self.model.center_range)

    def is_at_traffic_light(self):
        """Check if the vehicle is at its traffic light position."""
        light_pos = None
        if self.direction == (1, 0):  # Eastbound (West incoming)
            lane_idx = self.model.incoming_lanes.index(self.pos[1]) if self.pos[1] in self.model.incoming_lanes else 0
            light_pos = (self.model.center_start - 1, self.model.incoming_lanes[lane_idx])
        elif self.direction == (-1, 0):  # Westbound (East incoming)
            lane_idx = self.model.outgoing_lanes.index(self.pos[1]) if self.pos[1] in self.model.outgoing_lanes else 0
            light_pos = (self.model.center_end, self.model.outgoing_lanes[lane_idx])
        elif self.direction == (0, 1):  # Southbound (North incoming)
            lane_idx = self.model.outgoing_lanes.index(self.pos[0]) if self.pos[0] in self.model.outgoing_lanes else 0
            light_pos = (self.model.outgoing_lanes[lane_idx], self.model.center_start - 1)
        elif self.direction == (0, -1):  # Northbound (South incoming)
            lane_idx = self.model.incoming_lanes.index(self.pos[0]) if self.pos[0] in self.model.incoming_lanes else 0
            light_pos = (self.model.incoming_lanes[lane_idx], self.model.center_end)

        return self.pos == light_pos

    def check_traffic_light_state(self):
        """Check the state of the traffic light at the current position."""
        if not self.is_at_traffic_light():
            return None
        light_agents = self.model.grid.get_cell_list_contents(self.pos)
        for agent in light_agents:
            if isinstance(agent, TrafficLightAgent):
                return agent.state
        return None

    def step(self):
        """Update vehicle movement, stopping at traffic light until green."""
        if self.is_at_traffic_light():
            light_state = self.check_traffic_light_state()
            if light_state == "Red":
                self.speed = 0
                self.is_stopped_at_light = True
                self.is_stopped_for_queue = False
                return
            elif light_state == "Green" and self.is_stopped_at_light:
                self.speed = 1
                self.is_stopped_at_light = False

        if self.is_approaching_intersection() and not self.is_at_traffic_light():
            light_pos = None
            if self.direction == (1, 0):  # Eastbound
                lane_idx = self.model.incoming_lanes.index(self.pos[1]) if self.pos[1] in self.model.incoming_lanes else 0
                light_pos = (self.model.center_start - 1, self.model.incoming_lanes[lane_idx])
            elif self.direction == (-1, 0):  # Westbound
                lane_idx = self.model.outgoing_lanes.index(self.pos[1]) if self.pos[1] in self.model.outgoing_lanes else 0
                light_pos = (self.model.center_end, self.model.outgoing_lanes[lane_idx])
            elif self.direction == (0, 1):  # Southbound
                lane_idx = self.model.outgoing_lanes.index(self.pos[0]) if self.pos[0] in self.model.outgoing_lanes else 0
                light_pos = (self.model.outgoing_lanes[lane_idx], self.model.center_start - 1)
            elif self.direction == (0, -1):  # Northbound
                lane_idx = self.model.incoming_lanes.index(self.pos[0]) if self.pos[0] in self.model.incoming_lanes else 0
                light_pos = (self.model.incoming_lanes[lane_idx], self.model.center_end)

            if light_pos:
                light_agents = self.model.grid.get_cell_list_contents(light_pos)
                for agent in light_agents:
                    if isinstance(agent, TrafficLightAgent) and agent.state == "Red":
                        self.speed = 0
                        self.is_stopped_for_queue = False
                        return

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

        if self.speed > 0:
            new_x = self.pos[0] + self.direction[0]
            new_y = self.pos[1] + self.direction[1]
            if not (0 <= new_x < self.model.grid.width and 0 <= new_y < self.model.grid.height):
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
                self.model.current_agents -= 1
                self.model.total_exited += 1
                return

            cell_contents = self.model.grid.get_cell_list_contents((new_x, new_y))
            road_present = any(isinstance(agent, RoadCell) for agent in cell_contents)
            vehicle_present = any(isinstance(agent, VehicleAgent) for agent in cell_contents)
            if road_present and not vehicle_present:
                self.model.grid.move_agent(self, (new_x, new_y))
                self.steps_taken += 1