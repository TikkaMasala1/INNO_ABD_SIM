from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import Slider
from model import TrafficModel
from agents import RoadCell, VehicleAgent, TrafficLightAgent
import random

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

grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500)

# Define the slider for traffic_light_cycle
traffic_light_cycle_slider = Slider(
    "Traffic Light Cycle",  # Label
    30,  # Default value
    10,  # Min value
    60,  # Max value
    1,  # Step size
    description="Adjust the traffic light cycle duration"
)
spawn_rate_slider = Slider(
    "car spawn rate",  # Label
    15,  # Default value
    10,  # Min value
    80,  # Max value
    5,  # Step size
    description="Adjust the chance of spawning a car per step"
)

server = ModularServer(
    TrafficModel,
    [grid],
    "Kruispunt Simulatie met Wachtrijen en Verkeerslichten",
    {
        "width": 20,
        "height": 20,
        "traffic_light_cycle": traffic_light_cycle_slider,  # Add the slider to the model parameters
        "car_spawn_rate": spawn_rate_slider 
    }
)

if __name__ == "__main__":
    server.launch()