from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from .agents import VehicleAgent, RoadCell
import random

class TrafficModel(Model):
    def __init__(self, width=20, height=20, num_agents=15):
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)

        # Voeg wegen toe: tweebaanswegen op x=9,10 en y=9,10
        for x in range(width):
            for y in range(height):
                if y in [9, 10] or x in [9, 10]:  # Wegen op twee stroken per richting
                    road = RoadCell((x, y), self)
                    self.grid.place_agent(road, (x, y))

        # Spawnpunten aan de rand
        spawn_positions = [(0, 9), (0, 10), (19, 9), (19, 10), (9, 0), (10, 0), (9, 19), (10, 19)]

        # Voeg voertuigen toe op de wegen
        for i in range(num_agents):
            start_pos = random.choice(spawn_positions)  # Willekeurige startpositie
            vehicle = VehicleAgent(i, self, start_pos)
            self.schedule.add(vehicle)
            self.grid.place_agent(vehicle, start_pos)

    def step(self):
        self.schedule.step()
