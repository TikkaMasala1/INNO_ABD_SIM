from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import Slider
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

grid = CanvasGrid(agent_portrayal,40, 40, 600, 600)

auction_interval_slider = Slider(
    "Auction Interval",
    30,
    10,
    60,
    1,
    description="Interval between auctions (steps)"
)

spawn_rate_slider = Slider(
    "Car Spawn Rate",
    15,
    10,
    80,
    5,
    description="Adjust the chance of spawning a car per step"
)
num_lanes_slider = Slider(
    "Number of Lanes",
    2,  # Default value
    1,  # Min value
    5,  # Max value
    1,  # Step size
    description="Adjust the number of lanes per direction (incoming + outgoing)"
)

server = ModularServer(
    TrafficModel,
    [grid],
    "Auction-Based Traffic Simulation",
    {
        "width": 40,
        "height": 40,
        "auction_interval": auction_interval_slider,  # Updated parameter name
        "car_spawn_rate": spawn_rate_slider,
        "num_lanes": num_lanes_slider
    }
)

if __name__ == "__main__":
    server.launch()