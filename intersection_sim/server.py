from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from .model import TrafficModel
from .agents import RoadCell, VehicleAgent

def agent_portrayal(agent):
    """ Definieer hoe agenten eruitzien op het grid """
    if isinstance(agent, RoadCell):
        return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "gray", "Layer": 0}
    elif isinstance(agent, VehicleAgent):
        return {"Shape": "circle", "r": 0.5, "Filled": "true", "Color": "red", "Layer": 1}
    
    return None

grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500)

server = ModularServer(
    TrafficModel,
    [grid],
    "Kruispunt Simulatie",
    {"width": 20, "height": 20, "num_agents": 15} 
)

if __name__ == "__main__":
    server.launch()
