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
        self.state = "Red" # Initial state, will be updated by model

    def step(self):
        pass # State is updated by the TrafficModel, no action needed here

class VehicleAgent(Agent):
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model)
        self.pos = start_pos
        self.steps_taken = 0
        self.direction = self.determine_direction(start_pos)
        self.speed = 1
        self.sensing_range = 5
        self.is_stopped_for_queue = False

    def determine_direction(self, start_pos):

        if start_pos[0] == 0 and start_pos[1] == 10: return (1, 0) # East
        if start_pos[0] == 19 and start_pos[1] == 9: return (-1, 0) # West
        if start_pos[1] == 0 and start_pos[0] == 10: return (0, 1) # South
        if start_pos[1] == 19 and start_pos[0] == 9: return (0, -1) # North
        return (0, 0)

    def detect_queue(self):
        if self.speed == 0:
            return False

        for i in range(1, self.sensing_range + 1):
            check_x = self.pos[0] + self.direction[0] * i
            check_y = self.pos[1] + self.direction[1] * i

            if 0 <= check_x < self.model.grid.width and 0 <= check_y < self.model.grid.height:
                cell_contents = self.model.grid.get_cell_list_contents((check_x, check_y))
                vehicle_ahead = any(isinstance(agent, VehicleAgent) for agent in cell_contents)
                if vehicle_ahead:
                    return True
        return False

    def is_approaching_intersection(self):
        intersection_x_range = range(9, 11)
        intersection_y_range = range(9, 11)
        next_x = self.pos[0] + self.direction[0]
        next_y = self.pos[1] + self.direction[1]

        return (next_x in intersection_x_range and self.pos[1] in intersection_y_range) or \
               (self.pos[0] in intersection_x_range and next_y in intersection_y_range)

    def check_traffic_light(self):
        if self.is_approaching_intersection():
            light_pos = None
            if self.direction == (1, 0): # Eastbound
                light_pos = (8, 10)
            elif self.direction == (-1, 0): # Westbound
                light_pos = (11, 9)
            elif self.direction == (0, 1): # Southbound
                light_pos = (10, 8)
            elif self.direction == (0, -1): # Northbound
                light_pos = (9, 11)

            if light_pos:
                light_agents = self.model.grid.get_cell_list_contents(light_pos)
                for agent in light_agents:
                    if isinstance(agent, TrafficLightAgent) and agent.state == "Red":
                        return True # Stop if traffic light is red
        return False # No need to stop for traffic light

    def step(self):
        if self.check_traffic_light():
            self.speed = 0
            return # Stop and don't move further

        if self.detect_queue():
            self.speed = 0
            self.is_stopped_for_queue = True
        else:
            if self.is_stopped_for_queue:
                self.speed = 1
                self.is_stopped_for_queue = False
            else:
                self.speed = 1

        if self.speed > 0:
            new_x = self.pos[0] + self.direction[0]
            new_y = self.pos[1] + self.direction[1]

            if 0 <= new_x < self.model.grid.width and 0 <= new_y < self.model.grid.height:
                cell_contents = self.model.grid.get_cell_list_contents((new_x, new_y))
                road_present = any(isinstance(agent, RoadCell) for agent in cell_contents)
                vehicle_present = any(isinstance(agent, VehicleAgent) for agent in cell_contents)

                if road_present and not vehicle_present:
                    self.model.grid.move_agent(self, (new_x, new_y))
                    self.steps_taken += 1