from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from agents import VehicleAgent, RoadCell, TrafficLightAgent
import random


class TrafficModel(Model):
    """A traffic simulation model with configurable intersections and smart traffic lights.

    The model simulates vehicle movement through an intersection with dynamic traffic light
    control based on an auction system that responds to traffic conditions.

    Attributes:
        grid: MultiGrid representing the simulation space
        schedule: Activation schedule for agents
        current_agents: Count of currently active vehicles
        total_entered: Total vehicles entered since start
        total_exited: Total vehicles exited since start
        car_spawn_rate: Probability of spawning a new vehicle each step (percentage)
        num_lanes: Number of lanes per direction
        auction_interval: Steps between traffic light auctions
        current_cycle_time: Steps since last auction
        horizontal_phase: Current traffic light phase (True=EW green, False=NS green)
        phase_transition: Current transition state (None or 'clearing')
        pending_phase: Phase to transition to after clearing
        traffic_lights: List of TrafficLightAgent instances
    """

    def __init__(self, width=40, height=40, auction_interval=30, car_spawn_rate=15, num_lanes=1):
        """Initialize traffic model with given parameters.

        Args:
            width: Grid width in cells
            height: Grid height in cells
            auction_interval: Steps between traffic light phase auctions
            car_spawn_rate: Vehicle spawn probability (0-100)
            num_lanes: Number of lanes per direction
        """
        super().__init__()
        # Initialize core model components
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)

        # Traffic statistics tracking
        self.current_agents = 0
        self.total_entered = 0
        self.total_exited = 0

        # Model configuration parameters
        self.car_spawn_rate = car_spawn_rate
        self.num_lanes = num_lanes
        self.auction_interval = auction_interval
        self.current_cycle_time = 0

        # Traffic light state management
        self.horizontal_phase = True  # True = E-W green, False = N-S green
        self.phase_transition = None  # None or 'clearing'
        self.pending_phase = None

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
        # Random vehicle spawning
        if random.random() < (self.car_spawn_rate / 100):
            self.spawn_vehicle()

        # Phase timing and auction management
        self.current_cycle_time += 1
        if self.current_cycle_time >= self.auction_interval:
            self.conduct_auction()
            self.current_cycle_time = 0

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
            print(f"Total wait: {total_wait} Queue length: {queue_length} Avg wait: {avg_wait} Bid: {bid}")

        # Determine phase change
        new_phase = total_horizontal >= total_vertical
        phase_changed = new_phase != self.horizontal_phase

        if phase_changed:
            print(
                f"\nPhase change initiated. Current: {'Horizontal' if self.horizontal_phase else 'Vertical'}, New: {'Horizontal' if new_phase else 'Vertical'}")
            self.phase_transition = 'clearing'
            self.pending_phase = new_phase
        else:
            print("\nNo phase change needed.")

        # Log auction results
        print(f"\nAuction Results (Step {self.schedule.steps}):")
        print(f"Horizontal Bids: {total_horizontal:.2f}")
        print(f"Vertical Bids: {total_vertical:.2f}")
        print(f"New Phase: {'Horizontal' if new_phase else 'Vertical'}")
        print(f"Phase Changed: {phase_changed}")

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
                vehicle = VehicleAgent(vehicle_id, self, start_pos, car_spawn_rate=self.car_spawn_rate)
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
