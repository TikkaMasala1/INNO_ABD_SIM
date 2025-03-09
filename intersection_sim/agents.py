from mesa import Agent
import random

class RoadCell(Agent):
    def __init__(self, pos, model):
        super().__init__(pos, model)
        self.pos = pos

class TrafficLightAgent(Agent):
    def __init__(self, pos, model, lights_cycle=30):
        super().__init__(pos, model)
        self.pos = pos
        self.state = "Red"  # Initial state
        self.lights_cycle = lights_cycle  # Cycle duration for the traffic light
        self.current_cycle_time = 0  # Tracks the current time in the cycle
        self.horizontal_lights_green = True  # Start with horizontal lights green

    def is_intersection_clear(self):
        # Check if the middle 4 grid points are empty
        intersection_cells = [(9, 9), (9, 10), (10, 9), (10, 10)]
        for cell in intersection_cells:
            cell_contents = self.model.grid.get_cell_list_contents(cell)
            if any(isinstance(agent, VehicleAgent) for agent in cell_contents):
                return False  # Intersection is not clear
        return True  # Intersection is clear

    def step(self):
        self.current_cycle_time += 1

        if self.current_cycle_time >= self.lights_cycle and self.is_intersection_clear():
            self.horizontal_lights_green = not self.horizontal_lights_green
            self.current_cycle_time = 0
            self.update_state()

    def update_state(self):
        if self.pos in [(8, 10), (11, 9)]:  # Eastbound and Westbound lights (Horizontal)
            self.state = "Green" if self.horizontal_lights_green else "Red"
        elif self.pos in [(10, 8), (9, 11)]:  # Southbound and Northbound lights (Vertical)
            self.state = "Red" if self.horizontal_lights_green else "Green"

class VehicleAgent(Agent):
    # Define spawn_points as a class-level attribute
    spawn_positions = [(0, 9), (19, 10), (10, 0), (9, 19)]
    colors = ["Red", "Blue", "Green", "Purple"]  # List of available colors
    directions = {
        (1, 0): "east",  # Eastbound
        (-1, 0): "west",  # Westbound
        (0, 1): "south",  # Southbound
        (0, -1): "north",  # Northbound
    }
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model)
        self.pos = start_pos
        self.steps_taken = 0
        self.direction = self.determine_direction(start_pos)
        self.speed = 1
        self.sensing_range = 5
        self.is_stopped_for_queue = False
        self.color = random.choice(self.colors)  # Assign a random color
        self.image = self.get_image_path()  # Get the correct image path
        
    def get_image_path(self):
        # Construct the image path based on color and direction
        direction_name = self.directions.get(self.direction, "east")  # Default to east if direction is unknown
        return f"assets/cars/{self.color}/{self.color}_{direction_name}.png"

    def determine_direction(self, start_pos):
        if start_pos[0] == 0 and start_pos[1] == 9: return (1, 0) # East
        if start_pos[0] == 19 and start_pos[1] == 10: return (-1, 0) # West
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
                for agent in cell_contents:
                    if isinstance(agent, VehicleAgent):
                        vehicle_ahead = agent
                        if vehicle_ahead.speed < self.speed:
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
            self.is_stopped_for_queue = False  # Reset queue stop flag if stopped by light
            return

        if self.detect_queue():
            self.speed = 0
            self.is_stopped_for_queue = True
        else:
            if self.is_stopped_for_queue:
                if not self.detect_queue():  # Re-check queue again right now.
                    self.speed = 1
                    self.is_stopped_for_queue = False
            else:
                self.speed = 1  # Maintain speed if no queue and not previously stopped for queue.

        if self.speed > 0:
            new_x = self.pos[0] + self.direction[0]
            new_y = self.pos[1] + self.direction[1]

            # Check if the vehicle has exited the grid
            if not (0 <= new_x < self.model.grid.width and 0 <= new_y < self.model.grid.height):
                self.model.grid.remove_agent(self)  # Remove the vehicle from the grid
                self.model.schedule.remove(self)  # Remove the vehicle from the schedule
                self.model.current_agents -= 1  # Decrement the counter
                return
            
            cell_contents = self.model.grid.get_cell_list_contents((new_x, new_y))
            road_present = any(isinstance(agent, RoadCell) for agent in cell_contents)
            vehicle_present = any(isinstance(agent, VehicleAgent) for agent in cell_contents)

            if road_present and not vehicle_present:
                self.model.grid.move_agent(self, (new_x, new_y))
                self.steps_taken += 1