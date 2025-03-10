from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from agents import VehicleAgent, RoadCell, TrafficLightAgent
import random

class TrafficModel(Model):
    def __init__(self, width=20, height=20, traffic_light_cycle=30, car_spawn_rate=15):
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.current_agents = 0
        self.total_entered = 0
        self.total_exited = 0
        self.car_spawn_rate = car_spawn_rate

        # Add roads
        for x in range(width):
            for y in range(height):
                if y == 10 or y == 9 or x == 10 or x == 9:
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
            light = TrafficLightAgent(pos, self, traffic_light_cycle)
            self.traffic_lights.append(light)
            self.grid.place_agent(light, pos)
            self.schedule.add(light)

    def step(self):
        # Spawn new vehicles dynamically
        if random.random() < (self.car_spawn_rate/100):  # 10% chance to spawn a vehicle each step
            self.spawn_vehicle()

        self.schedule.step()

    def spawn_vehicle(self):
        start_pos = random.choice(VehicleAgent.spawn_positions)
        vehicle_id = self.next_id()  # Generate a unique ID for the new vehicle
        vehicle = VehicleAgent(vehicle_id, self, start_pos)
        self.schedule.add(vehicle)
        self.grid.place_agent(vehicle, start_pos)
        self.current_agents += 1  # Increment the current vehicles counter
        self.total_entered += 1  # Increment the total entered counter