from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import Slider, Choice
from model import TrafficModel
from agents import RoadCell, VehicleAgent, TrafficLightAgent

def agent_portrayal(agent):
    if isinstance(agent, RoadCell):
        return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "gray", "Layer": 0}
    
    elif isinstance(agent, TrafficLightAgent):
        color = "green" if agent.state == "Green" else "red"
        return {
            "Shape": "rect", 
            "w": 0.5, 
            "h": 0.5, 
            "Filled": "true", 
            "Color": color, 
            "Layer": 2
        }
    
    elif isinstance(agent, VehicleAgent):
        return {
            "Shape": agent.image, 
            "w": 0.8,
            "h": 0.8, 
            "r": 0.5, 
            "Filled": "true", 
            "Layer": 1
        }

    return None

grid = CanvasGrid(agent_portrayal, 40, 40, 600, 600)

traffic_flow_chart = ChartModule(
    [{"Label": "TrafficFlowPerInterval", "Color": "Blue"}],
    data_collector_name='datacollector'
)

waiting_time_chart = ChartModule(
    [{"Label": "AverageWaitingTime", "Color": "Red"}],
    data_collector_name='datacollector'
)

light_strategy_choice = Choice(
    "Traffic Light Strategy",
    value="auction",
    choices=["auction", "fixed_cycle", "dutch_system"],
    description="Select the traffic light control strategy"
)

decision_interval_slider = Slider(
    "Decision Interval",
    30,
    10,
    60,
    1,
    description="Interval between light strategies decisions"
)

spawn_rate_choice = Choice(
    "Traffic Condition",
    value="Normale tijd",
    choices=["Normale tijd", "Spitsuur"],
    description="Select traffic condition (Spitsuur has 2.5x higher spawn rate)"
)

num_lanes_slider = Slider(
    "Number of Lanes",
    2,
    1,
    5,
    1,
    description="Adjust the number of lanes per direction (incoming + outgoing)"
)

server = ModularServer(
    TrafficModel,
    [grid, traffic_flow_chart, waiting_time_chart],
    "Auction-Based Traffic Simulation",
    {
        "width": 40,
        "height": 40,
        "light_strategy": light_strategy_choice,
        "decision_interval": decision_interval_slider,
        "traffic_condition": spawn_rate_choice,
        "num_lanes": num_lanes_slider,
        "car_speed": 1
    }
)

if __name__ == "__main__":
    server.launch()