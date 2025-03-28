from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from agents import VehicleAgent, RoadCell, TrafficLightAgent
import random

class TrafficModel(Model):
    def __init__(self, width=40, height=40, traffic_light_cycle=30, car_spawn_rate=15, num_lanes=1):
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.current_agents = 0
        self.total_entered = 0
        self.total_exited = 0
        self.car_spawn_rate = car_spawn_rate
        self.num_lanes = num_lanes
        self.traffic_light_cycle = traffic_light_cycle  # Store cycle duration
        self.current_cycle_time = 0  # Track time in the current phase
        self.horizontal_phase = True  # True = E-W green, False = N-S green

        # Calculate and store center range and lane data
        intersection_size = 2 * self.num_lanes
        self.center_start = (width - intersection_size) // 2
        self.center_end = self.center_start + intersection_size
        self.center_range = range(self.center_start, self.center_end)
        self.incoming_lanes = list(range(self.center_start, self.center_start + self.num_lanes))
        self.outgoing_lanes = list(range(self.center_end - self.num_lanes, self.center_end))

        road_lanes = self.incoming_lanes + self.outgoing_lanes
        self.create_road_segment(road_lanes, range(0, self.center_start))  # North roads
        self.create_road_segment(road_lanes, range(self.center_end, height))  # South roads
        self.create_road_segment(range(0, self.center_start), road_lanes)  # West roads
        self.create_road_segment(range(self.center_end, width), road_lanes)  # East roads
        self.create_road_segment(self.center_range, self.center_range)  # Intersection

        # Update spawn positions
        VehicleAgent.spawn_positions = []
        for y in self.incoming_lanes:
            VehicleAgent.spawn_positions.append((0, y))  # West incoming
        for y in self.outgoing_lanes:
            VehicleAgent.spawn_positions.append((width - 1, y))  # East incoming
        for x in self.outgoing_lanes:
            VehicleAgent.spawn_positions.append((x, 0))  # North incoming
        for x in self.incoming_lanes:
            VehicleAgent.spawn_positions.append((x, height - 1))  # South incoming

        # Traffic lights
        self.traffic_lights = []
        traffic_light_positions = []
        for x in self.incoming_lanes:
            traffic_light_positions.append((x + self.num_lanes, self.center_start - 1))  # North
        for x in self.outgoing_lanes:
            traffic_light_positions.append((x - self.num_lanes, self.center_end))  # South
        for y in self.incoming_lanes:
            traffic_light_positions.append((self.center_start - 1, y))  # West
        for y in self.outgoing_lanes:
            traffic_light_positions.append((self.center_end, y))  # East

        for pos in traffic_light_positions:
            light = TrafficLightAgent(pos, self)
            self.traffic_lights.append(light)
            self.grid.place_agent(light, pos)
            self.schedule.add(light)

    def step(self):
        """Advance the model, including traffic light phase management."""
        if random.random() < (self.car_spawn_rate / 100):
            self.spawn_vehicle()
        
        self.current_cycle_time += 1
        if self.current_cycle_time >= self.traffic_light_cycle and self.is_intersection_clear():
            self.horizontal_phase = not self.horizontal_phase  # Switch phase
            self.current_cycle_time = 0
        
        self.schedule.step()

    def is_intersection_clear(self):
        """Check if the intersection is clear of vehicles."""
        for x in self.center_range:
            for y in self.center_range:
                cell_contents = self.grid.get_cell_list_contents((x, y))
                if any(isinstance(agent, VehicleAgent) for agent in cell_contents):
                    return False
        return True

    def spawn_vehicle(self):
        available_positions = list(VehicleAgent.spawn_positions)
        random.shuffle(available_positions)
        for start_pos in available_positions:
            cell_contents = self.grid.get_cell_list_contents(start_pos)
            vehicle_present = any(isinstance(agent, VehicleAgent) for agent in cell_contents)
            if not vehicle_present:
                vehicle_id = self.next_id()
                vehicle = VehicleAgent(vehicle_id, self, start_pos, car_spawn_rate=self.car_spawn_rate)
                self.schedule.add(vehicle)
                self.grid.place_agent(vehicle, start_pos)
                self.current_agents += 1
                self.total_entered += 1
                return

    def create_road_segment(self, x_range, y_range):
        """Helper function to create road cells."""
        for x in x_range:
            for y in y_range:
                self.grid.place_agent(RoadCell((x, y), self), (x, y))