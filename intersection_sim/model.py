from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from agents import VehicleAgent, RoadCell, TrafficLightAgent
import random

class TrafficModel(Model):
    def __init__(self, width=20, height=20, num_agents=15):
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.traffic_light_cycle = 30 # 30 steps for each light cycle (green or red)
        self.current_cycle_time = 0
        self.horizontal_lights_green = True # Start with horizontal lights green

        # Add roads
        for x in range(width):
            for y in range(height):
                if y == 10: # East-West road (Eastbound)
                    road = RoadCell((x, y), self)
                    self.grid.place_agent(road, (x, y))
                elif y == 9: # East-West road (Westbound)
                    road = RoadCell((x, y), self)
                    self.grid.place_agent(road, (x, y))
                elif x == 10: # North-South road (Southbound)
                    road = RoadCell((x, y), self)
                    self.grid.place_agent(road, (x, y))
                elif x == 9: # North-South road (Northbound)
                    road = RoadCell((x, y), self)
                    self.grid.place_agent(road, (x, y))

        # Add traffic lights
        self.traffic_lights = []
        traffic_light_positions = [
            (8, 10), # Eastbound traffic light
            (11, 9), # Westbound traffic light
            (10, 8), # Southbound traffic light
            (9, 11)  # Northbound traffic light
        ]
        for pos in traffic_light_positions:
            light = TrafficLightAgent(pos, self)
            self.traffic_lights.append(light)
            self.grid.place_agent(light, pos)
            self.schedule.add(light)

        # Spawn points
        spawn_positions = [(0, 10), (19, 9), (10, 0), (9, 19)]

        # Add vehicles
        for i in range(num_agents):
            start_pos = random.choice(spawn_positions)
            vehicle = VehicleAgent(i, self, start_pos)
            self.schedule.add(vehicle)
            self.grid.place_agent(vehicle, start_pos)

        self.update_traffic_lights() # Initialize traffic lights state

    def step(self):
        self.current_cycle_time += 1

        if self.current_cycle_time >= self.traffic_light_cycle:
            self.horizontal_lights_green = not self.horizontal_lights_green
            self.current_cycle_time = 0
            self.update_traffic_lights()

        self.schedule.step()

    def update_traffic_lights(self):
        for light in self.traffic_lights:
            if light.pos in [(8, 10), (11, 9)]: # Eastbound and Westbound lights (Horizontal)
                light.state = "Green" if self.horizontal_lights_green else "Red"
            elif light.pos in [(10, 8), (9, 11)]: # Southbound and Northbound lights (Vertical)
                light.state = "Red" if self.horizontal_lights_green else "Green"