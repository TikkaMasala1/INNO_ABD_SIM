from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
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

server = ModularServer(
    TrafficModel,
    [grid],
    "Kruispunt Simulatie met Wachtrijen en Verkeerslichten",
    {"width": 20, "height": 20}
)

if __name__ == "__main__":
    server.launch()