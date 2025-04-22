from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from agents import VehicleAgent, RoadCell, TrafficLightAgent
import random
import numpy as np

class TrafficModel(Model):
    """A traffic simulation model with configurable intersections and smart traffic lights.

    The model simulates vehicle movement through an intersection with dynamic traffic light
    control based on an auction system, fixed cycle, or Dutch system.

    Attributes:
        grid: MultiGrid representing the simulation space
        schedule: Activation schedule for agents
        current_agents: Count of currently active vehicles
        total_entered: Total vehicles entered since start
        total_exited: Total vehicles exited since start
        car_spawn_rate: Mean number of vehicles to spawn per second (normal distribution)
        car_spawn_std: Standard deviation for vehicle spawn rate
        num_lanes: Number of lanes per direction
        decision_interval: Steps between traffic light auctions
        current_cycle_time: Steps since last auction
        horizontal_phase: Current traffic light phase (True=EW green, False=NS green)
        phase_transition: Current transition state (None or 'clearing')
        pending_phase: Phase to transition to after clearing
        traffic_lights: List of TrafficLightAgent instances
        min_green_time: Minimum green time for Dutch system
        max_green_time: Maximum green time for Dutch system
        clearance_time: Clearance time for Dutch system
        dutch_cycle_time: Tracks cycle time for Dutch system
    """

    def __init__(self, width=40, height=40, decision_interval=30, traffic_condition="Normale tijd", num_lanes=1, car_speed=1, light_strategy="auction"):
        """Initialize traffic model with given parameters.

        Args:
            width: Grid width in cells
            height: Grid height in cells
            decision_interval: Steps between traffic light phase auctions
            traffic_condition: Traffic condition ("Normale tijd" or "Spitsuur")
            num_lanes: Number of lanes per direction
            car_speed: Speed of vehicles (cells per step)
            light_strategy: Traffic light control strategy ("auction", "fixed_cycle", "dutch_system")
        """
        super().__init__()
        self.car_speed = car_speed
        self.light_strategy = light_strategy

        # Map traffic condition to car_spawn_rate
        self.spawn_rate_mapping = {
            "Normale tijd": 0.5,  # 30 vehicles/minute
            "Spitsuur": 0.5 * 2.5  # 75 vehicles/minute (0.5 * 2.5 = 1.25 vehicles/second)
        }
        self.car_spawn_rate = self.spawn_rate_mapping[traffic_condition]
        self.car_spawn_std = np.sqrt(self.car_spawn_rate)  # Default std = sqrt(mean)

        # Initialize core model components
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)

        # Traffic statistics tracking
        self.current_agents = 0
        self.total_entered = 0
        self.total_exited = 0
        self.last_exited_count = 0
        self.flow_interval = 10
        # Model configuration parameters
        self.num_lanes = num_lanes
        self.decision_interval = decision_interval
        self.current_cycle_time = 0

        # Traffic light state management
        self.horizontal_phase = True  # True = E-W green, False = N-S green
        self.phase_transition = None  # None or 'clearing'
        self.pending_phase = None

        # Dutch system parameters
        self.min_green_time = 7  # Minimum green time in steps (realistic for small intersections)
        self.max_green_time = 60  # Maximum green time in steps
        self.clearance_time = 3  # Clearance time in steps (2-5 seconds equivalent)
        self.dutch_cycle_time = 0
        self.sensor_range = 10  # 50 meters / 5 meters per grid space = 10 grid spaces

        # Calculate intersection geometry
        intersection_size = 2 * self.num_lanes
        self.center_start = (width - intersection_size) // 2
        self.center_end = self.center_start + intersection_size
        self.center_range = range(self.center_start, self.center_end)
        self.incoming_lanes = list(range(self.center_start, self.center_start + self.num_lanes))
        self.outgoing_lanes = list(range(self.center_end - self.num_lanes, self.center_end))

        # Build road network
        road_lanes = self.incoming_lanes + self.outgoing_lanes
        self.create_road_segment(road_lanes, range(0, self.center_start))  # North roads
        self.create_road_segment(road_lanes, range(self.center_end, height))  # South roads
        self.create_road_segment(range(0, self.center_start), road_lanes)  # West roads
        self.create_road_segment(range(self.center_end, width), road_lanes)  # East roads
        self.create_road_segment(self.center_range, self.center_range)  # Intersection

        # Configure vehicle spawn positions
        VehicleAgent.spawn_positions = []
        for y in self.incoming_lanes:
            VehicleAgent.spawn_positions.append((0, y))  # West incoming
        for y in self.outgoing_lanes:
            VehicleAgent.spawn_positions.append((width - 1, y))  # East incoming
        for x in self.outgoing_lanes:
            VehicleAgent.spawn_positions.append((x, 0))  # North incoming
        for x in self.incoming_lanes:
            VehicleAgent.spawn_positions.append((x, height - 1))  # South incoming

        # Initialize traffic lights
        self.traffic_lights = []
        self._initialize_traffic_lights(width, height)

        self.datacollector = DataCollector(
            model_reporters={
                "TrafficFlowPerInterval": lambda m: m.get_flow_this_interval(),
                "AverageWaitingTime": lambda m: m.get_average_waiting_time()
            }
        )

    def _initialize_traffic_lights(self, width, height):
        """Create and position traffic light agents at intersection approaches."""
        traffic_light_positions = []
        # North approach lights
        for x in self.incoming_lanes:
            traffic_light_positions.append((x + self.num_lanes, self.center_start - 1))
        # South approach lights
        for x in self.outgoing_lanes:
            traffic_light_positions.append((x - self.num_lanes, self.center_end))
        # West approach lights
        for y in self.incoming_lanes:
            traffic_light_positions.append((self.center_start - 1, y))
        # East approach lights
        for y in self.outgoing_lanes:
            traffic_light_positions.append((self.center_end, y))

        # Create light agents
        for pos in traffic_light_positions:
            light = TrafficLightAgent(pos, self)
            self.traffic_lights.append(light)
            self.grid.place_agent(light, pos)
            self.schedule.add(light)

    def step(self):
        """Advance the model by one step.

        Handles vehicle spawning, phase timing, and transition management.
        """
        # For data visualisation
        self.datacollector.collect(self)

        # Spawn vehicles based on normal distribution
        num_vehicles = max(0, int(round(np.random.normal(self.car_spawn_rate, self.car_spawn_std))))
        for _ in range(num_vehicles):
            self.spawn_vehicle()

        # Phase timing and traffic light control
        self.current_cycle_time += 1
        self.dutch_cycle_time += 1

        if self.light_strategy == "auction":
            if self.current_cycle_time >= self.decision_interval:
                self.conduct_auction()
                self.current_cycle_time = 0

        elif self.light_strategy == "fixed_cycle":
            if self.current_cycle_time >= self.decision_interval:
                self.horizontal_phase = not self.horizontal_phase
                print('Flipping, Fixed cycle')
                self.current_cycle_time = 0

        elif self.light_strategy == "dutch_system":
            self.conduct_dutch_system()

        # Execute all agent steps
        self.schedule.step()

        # Handle phase transitions if intersection clears
        if self.phase_transition == 'clearing' and self.is_intersection_clear():
            print(f"Intersection clear. Switching to {'Horizontal' if self.pending_phase else 'Vertical'} phase.")
            self.horizontal_phase = self.pending_phase
            self.phase_transition = None
            self.pending_phase = None

    def conduct_auction(self):
        """Determine optimal traffic light phase via auction system.

        Collects bids from all approaches based on queue length and wait time,
        then decides whether to change the current phase.
        """
        total_horizontal = 0.0
        total_vertical = 0.0

        for light in self.traffic_lights:
            queue_length = 0
            total_wait = 0

            # Calculate queue metrics for this light's approach
            for cell in light.get_lane_cells():
                for agent in self.grid.get_cell_list_contents(cell):
                    if isinstance(agent, VehicleAgent):
                        queue_length += 1
                        total_wait += agent.waiting_time

            avg_wait = total_wait / queue_length if queue_length > 0 else 0
            bid = queue_length * avg_wait

            # Accumulate bids by direction
            if light.is_horizontal:
                total_horizontal += bid
            else:
                total_vertical += bid

        # Determine phase change
        new_phase = total_horizontal >= total_vertical
        phase_changed = new_phase != self.horizontal_phase

        if phase_changed:
            self.phase_transition = 'clearing'
            self.pending_phase = new_phase
        else:
            print("\nNo phase change needed.")

        # Log auction results
        print(f"Phase changed, Auction")

    def conduct_dutch_system(self):
        """Implement Dutch traffic light system with dynamic green times and clearance time."""
        if self.phase_transition == 'clearing':
            # Wait for intersection to clear
            return

        # Calculate queue lengths for horizontal and vertical directions within 50 meters (10 grid spaces)
        horizontal_queue = 0
        vertical_queue = 0
        for light in self.traffic_lights:
            queue_length = 0
            light_pos = light.pos
            for cell in light.get_lane_cells():
                cell_x, cell_y = cell
                # Calculate distance from traffic light
                if light.is_horizontal:
                    distance = abs(cell_x - light_pos[0])
                else:
                    distance = abs(cell_y - light_pos[1])
                # Only count vehicles within sensor range (10 grid spaces = 50 meters)
                if distance <= self.sensor_range:
                    for agent in self.grid.get_cell_list_contents(cell):
                        if isinstance(agent, VehicleAgent):
                            queue_length += 1
            if light.is_horizontal:
                horizontal_queue += queue_length
            else:
                vertical_queue += queue_length

        # Determine green time based on queue length
        total_queue = horizontal_queue + vertical_queue
        if total_queue > 0:
            horizontal_ratio = horizontal_queue / total_queue
            green_time = self.min_green_time + (self.max_green_time - self.min_green_time) * horizontal_ratio
            green_time = max(self.min_green_time, min(self.max_green_time, int(green_time)))
        else:
            green_time = self.min_green_time

        # Check if it's time to switch phase
        if self.dutch_cycle_time >= green_time + self.clearance_time:
            new_phase = not self.horizontal_phase
            self.phase_transition = 'clearing'
            self.pending_phase = new_phase
            self.dutch_cycle_time = 0
            print(f"Switching to {'Horizontal' if new_phase else 'Vertical'} phase after {green_time} steps green and {self.clearance_time} steps clearance.")

    def is_intersection_clear(self):
        """Check if intersection area contains no vehicles.

        Returns:
            bool: True if no vehicles in intersection, False otherwise
        """
        for x in self.center_range:
            for y in self.center_range:
                if any(isinstance(agent, VehicleAgent)
                       for agent in self.grid.get_cell_list_contents((x, y))):
                    return False
        return True

    def spawn_vehicle(self):
        """Attempt to spawn a new vehicle at a random available spawn point."""
        available_positions = list(VehicleAgent.spawn_positions)
        random.shuffle(available_positions)

        for start_pos in available_positions:
            if not any(isinstance(agent, VehicleAgent)
                       for agent in self.grid.get_cell_list_contents(start_pos)):
                vehicle_id = self.next_id()
                vehicle = VehicleAgent(vehicle_id, self, start_pos, car_spawn_rate=self.car_spawn_rate, speed=self.car_speed)
                self.schedule.add(vehicle)
                self.grid.place_agent(vehicle, start_pos)
                self.current_agents += 1
                self.total_entered += 1
                return

    def create_road_segment(self, x_range, y_range):
        """Create road cells in the specified area.

        Args:
            x_range: Range of x-coordinates for road segment
            y_range: Range of y-coordinates for road segment
        """
        for x in x_range:
            for y in y_range:
                self.grid.place_agent(RoadCell((x, y), self), (x, y))

    def get_flow_this_interval(self):
        if self.schedule.steps % self.flow_interval == 0:
            flow = self.total_exited - self.last_exited_count
            self.last_exited_count = self.total_exited
            return flow
        else:
            return 0
        
    def get_average_waiting_time(self):
        agents = [a for a in self.schedule.agents if hasattr(a, "waiting_time")]
        if agents:
            total_wait = sum([a.waiting_time for a in agents])
            return total_wait / len(agents)
        return 0