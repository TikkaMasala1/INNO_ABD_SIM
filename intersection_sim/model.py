from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from agents import VehicleAgent, RoadCell, TrafficLightAgent
import random

class TrafficModel(Model):
    def __init__(self, width=30, height=30, traffic_light_cycle=30, car_spawn_rate=15):
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.current_agents = 0
        self.total_entered = 0
        self.total_exited = 0
        self.car_spawn_rate = car_spawn_rate

        center_range = range(12, 18)  # 6x6 kruising

        # Bepaal rijstroken per richting
        incoming_lanes = [12, 13, 14]  # meest links → rechts (inkomend)
        outgoing_lanes = [15, 16, 17]  # meest links → rechts (uitgaand)

        # Noord (van boven naar kruising)
        for x in incoming_lanes + outgoing_lanes:
            for y in range(0, 12):  # 0 t/m 11
                self.grid.place_agent(RoadCell((x, y), self), (x, y))

        # Zuid (van onder naar kruising)
        for x in incoming_lanes + outgoing_lanes:
            for y in range(18, 30):  # 18 t/m 29
                self.grid.place_agent(RoadCell((x, y), self), (x, y))

        # West (van links naar kruising)
        for y in incoming_lanes + outgoing_lanes:
            for x in range(0, 12):
                self.grid.place_agent(RoadCell((x, y), self), (x, y))

        # Oost (van rechts naar kruising)
        for y in incoming_lanes + outgoing_lanes:
            for x in range(18, 30):
                self.grid.place_agent(RoadCell((x, y), self), (x, y))

        # Middenkruising (6x6)
        for x in center_range:
            for y in center_range:
                self.grid.place_agent(RoadCell((x, y), self), (x, y))


        # Verkeerslichten - 12 stuks (3 per kant, voor elke rijstrook)
        self.traffic_lights = []
        traffic_light_positions = [
            (15, 11), (16, 11), (17, 11),
            (12, 18), (13, 18), (14, 18),
            (11, 12), (11, 13), (11, 14),
            (18, 17), (18, 16), (18, 15),
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