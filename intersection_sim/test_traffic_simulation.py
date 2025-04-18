import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import unittest
from unittest.mock import Mock, MagicMock, PropertyMock
import random
from agents import RoadCell, TrafficLightAgent, VehicleAgent
from model import TrafficModel
from server import agent_portrayal, server, grid, traffic_flow_chart

# Set random seed for reproducible tests
random.seed(42)

class TestTrafficSimulation(unittest.TestCase):
    """
    Unit tests for the traffic simulation codebase (agents.py, model.py, server.py).
    Covers RoadCell, TrafficLightAgent, VehicleAgent, TrafficModel, and visualization.
    Located in intersection_sim/ directory.
    """

    def setUp(self):
        """Set up a mock model with required attributes for tests that create agents."""
        self.model = Mock()
        self.model.agents_ = {RoadCell: {}, TrafficLightAgent: {}, VehicleAgent: {}}
        # Attributes for VehicleAgent._determine_direction and other methods
        self.model.incoming_lanes = [10, 11]
        self.model.outgoing_lanes = [12, 13]
        self.model.grid = MagicMock()
        self.model.grid.width = 40
        self.model.grid.height = 40
        self.model.grid.get_cell_list_contents = MagicMock(return_value=[])
        # Attributes for TrafficLightAgent and intersection checks
        self.model.center_start = 10
        self.model.center_end = 14
        self.model.center_range = range(10, 14)
        # Mock schedule for agent management
        self.model.schedule = MagicMock()
        self.model.schedule.get_agents = MagicMock(return_value=[])
        self.model.schedule.steps = 0

    # --- Tests for agents.py ---

    def test_road_cell_init(self):
        """Test RoadCell initialization."""
        pos = (5, 5)
        road_cell = RoadCell(pos, self.model)
        self.assertEqual(road_cell.pos, pos)
        self.assertEqual(road_cell.model, self.model)

    def test_traffic_light_orientation(self):
        """Test TrafficLightAgent orientation detection."""
        # West incoming (horizontal)
        light = TrafficLightAgent((9, 10), self.model)
        self.assertTrue(light._determine_orientation())
        
        # North incoming (vertical)
        light = TrafficLightAgent((10, 9), self.model)
        self.assertFalse(light._determine_orientation())

    def test_traffic_light_step(self):
        """Test TrafficLightAgent state updates."""
        self.model.horizontal_phase = True
        self.model.phase_transition = None
        light = TrafficLightAgent((10, 10), self.model)
        light.is_horizontal = True
        light.step()
        self.assertEqual(light.state, "Green")
        
        self.model.phase_transition = "clearing"
        light.step()
        self.assertEqual(light.state, "Red")

    def test_traffic_light_get_lane_cells(self):
        """Test TrafficLightAgent lane cell retrieval."""
        # West approach (horizontal)
        light = TrafficLightAgent((9, 10), self.model)
        light.is_horizontal = True
        cells = light.get_lane_cells()
        self.assertEqual(cells, [(x, 10) for x in range(0, 10)])

    def test_vehicle_direction(self):
        """Test VehicleAgent direction determination."""
        # West incoming (eastbound)
        vehicle = VehicleAgent(1, self.model, (0, 10))
        self.assertEqual(vehicle._determine_direction((0, 10)), (1, 0))
        
        # North incoming (southbound)
        vehicle = VehicleAgent(1, self.model, (12, 0))
        self.assertEqual(vehicle._determine_direction((12, 0)), (0, 1))

    def test_vehicle_image_path(self):
        """Test VehicleAgent image path generation."""
        vehicle = VehicleAgent(1, self.model, (0, 10))
        vehicle.color = "Red"
        vehicle.direction = (1, 0)  # Eastbound
        self.assertEqual(
            vehicle._get_image_path(),
            "intersection_sim/assets/cars/Red/Red_east.png"
        )

    def test_vehicle_at_red_light(self):
        """Test VehicleAgent stopping at red light."""
        self.model.grid.get_cell_list_contents.return_value = [Mock(spec=TrafficLightAgent, state="Red")]
        
        vehicle = VehicleAgent(1, self.model, (9, 10))
        vehicle.direction = (1, 0)
        vehicle.step()
        self.assertEqual(vehicle.speed, 0)
        self.assertTrue(vehicle.is_stopped_at_light)
        self.assertEqual(vehicle.waiting_time, 1)

    def test_vehicle_detect_queue(self):
        """Test VehicleAgent queue detection."""
        vehicle = VehicleAgent(1, self.model, (5, 10))
        vehicle.direction = (1, 0)
        vehicle.speed = 1
        
        # Mock a slower vehicle ahead
        slow_vehicle = Mock(spec=VehicleAgent, speed=0)
        self.model.grid.get_cell_list_contents.return_value = [slow_vehicle]
        self.assertTrue(vehicle.detect_queue())
        
        # No vehicle ahead
        self.model.grid.get_cell_list_contents.return_value = []
        self.assertFalse(vehicle.detect_queue())

    # --- Tests for model.py ---

    def test_model_init(self):
        """Test TrafficModel initialization."""
        model = TrafficModel(width=40, height=40, num_lanes=2)
        self.assertEqual(model.grid.width, 40)
        self.assertEqual(model.grid.height, 40)
        self.assertEqual(len(model.incoming_lanes), 2)
        self.assertEqual(len(model.outgoing_lanes), 2)
        self.assertEqual(len(model.traffic_lights), 8)  # 4 approaches * 2 lanes

    def test_create_road_segment(self):
        """Test TrafficModel road segment creation."""
        model = TrafficModel(width=40, height=40, num_lanes=1)
        model.create_road_segment(range(0, 5), range(0, 5))
        for x in range(0, 5):
            for y in range(0, 5):
                agents = model.grid.get_cell_list_contents((x, y))
                self.assertTrue(any(isinstance(agent, RoadCell) for agent in agents))

    def test_spawn_vehicle(self):
        """Test TrafficModel vehicle spawning."""
        model = TrafficModel(width=40, height=40, num_lanes=1)
        model.grid.get_cell_list_contents = MagicMock(return_value=[])
        model.spawn_vehicle()
        self.assertEqual(model.current_agents, 1)
        self.assertEqual(model.total_entered, 1)

    def test_conduct_auction(self):
        """Test TrafficModel auction logic."""
        model = TrafficModel(width=40, height=40, num_lanes=1)
        model.horizontal_phase = False  # Start in vertical phase
        light1 = Mock(spec=TrafficLightAgent, is_horizontal=True)
        light2 = Mock(spec=TrafficLightAgent, is_horizontal=False)
        model.traffic_lights = [light1, light2]
        
        light1.get_lane_cells.return_value = [(0, 10)]
        light2.get_lane_cells.return_value = [(10, 0)]
        model.grid.get_cell_list_contents = MagicMock(side_effect=[
            [Mock(spec=VehicleAgent, waiting_time=10)],  # Horizontal lane
            []  # Vertical lane
        ])
        
        model.conduct_auction()
        self.assertEqual(model.phase_transition, 'clearing')
        self.assertTrue(model.pending_phase)

    def test_is_intersection_clear(self):
        """Test TrafficModel intersection clearing check."""
        model = TrafficModel(width=40, height=40, num_lanes=1)
        model.center_range = range(10, 14)
        
        # Intersection with vehicle
        model.grid.get_cell_list_contents = MagicMock(return_value=[Mock(spec=VehicleAgent)])
        self.assertFalse(model.is_intersection_clear())
        
        # Empty intersection
        model.grid.get_cell_list_contents = MagicMock(return_value=[])
        self.assertTrue(model.is_intersection_clear())

    def test_get_flow_this_interval(self):
        """Test TrafficModel traffic flow calculation."""
        model = TrafficModel(width=40, height=40, num_lanes=1)
        model.flow_interval = 5
        model.total_exited = 10
        model.last_exited_count = 5
        model.schedule.steps = 5
        self.assertEqual(model.get_flow_this_interval(), 5)
        model.schedule.steps = 6
        self.assertEqual(model.get_flow_this_interval(), 0)

    def test_get_average_waiting_time(self):
        """Test TrafficModel average waiting time calculation."""
        model = TrafficModel(width=40, height=40, num_lanes=1)
        vehicle = Mock(spec=VehicleAgent, waiting_time=10)
        # Mock the schedule.agents property using PropertyMock
        type(model.schedule).agents = PropertyMock(return_value=[vehicle])
        self.assertEqual(model.get_average_waiting_time(), 10)
    
        # Test with no agents
        type(model.schedule).agents = PropertyMock(return_value=[])
        self.assertEqual(model.get_average_waiting_time(), 0)

    def test_agent_portrayal(self):
        """Test agent_portrayal function for visualization."""
        # RoadCell
        road_cell = RoadCell((0, 0), self.model)
        self.assertEqual(agent_portrayal(road_cell), {
            "Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "gray", "Layer": 0
        })
        
        # TrafficLightAgent
        light = TrafficLightAgent((0, 0), self.model)
        light.state = "Green"
        portrayal = agent_portrayal(light)
        self.assertEqual(portrayal["Color"], "green")
        self.assertEqual(portrayal["w"], 0.5)
        
        # VehicleAgent
        vehicle = VehicleAgent(1, self.model, (0, 10))
        vehicle.image = "intersection_sim/assets/cars/Red/Red_east.png"
        portrayal = agent_portrayal(vehicle)
        self.assertEqual(portrayal["Shape"], vehicle.image)
        self.assertEqual(portrayal["w"], 0.8)

    def test_server_setup(self):
        """Test ModularServer configuration."""
        self.assertEqual(server.model_cls, TrafficModel)
        self.assertEqual(len(server.visualization_elements), 3)
        self.assertEqual(grid.canvas_width, 600)
        self.assertEqual(traffic_flow_chart.data_collector_name, 'datacollector')
        self.assertEqual(server.model_kwargs["width"], 40)

if __name__ == '__main__':
    unittest.main()