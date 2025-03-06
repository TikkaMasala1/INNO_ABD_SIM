from mesa import Agent
import random

class RoadCell(Agent):
    """ Wegcellen voor het kruispunt """
    def __init__(self, pos, model):
        super().__init__(pos, model)
        self.pos = pos

class VehicleAgent(Agent):
    """ Simpele voertuigagent met beweging"""
    def __init__(self, unique_id, model, start_pos):
        super().__init__(unique_id, model)
        self.pos = start_pos
        self.steps_taken = 0  # Houdt bij hoe ver de auto al is gegaan
        self.direction = self.determine_direction(start_pos)  # Kies rijrichting

    def determine_direction(self, start_pos):
        """ Bepaal de richting waarin de auto moet rijden op basis van de startpositie """
        if start_pos[0] == 0: return (1, 0)  # Van links naar rechts
        if start_pos[0] == 19: return (-1, 0)  # Van rechts naar links
        if start_pos[1] == 0: return (0, 1)  # Van boven naar beneden
        if start_pos[1] == 19: return (0, -1)  # Van beneden naar boven
        return (0, 0)  # Stilstaan (onwaarschijnlijk)

    def step(self):
        """ Voertuig beweegt als de volgende cel een weg is """
        new_x = self.pos[0] + self.direction[0]
        new_y = self.pos[1] + self.direction[1]

        if 0 <= new_x < self.model.grid.width and 0 <= new_y < self.model.grid.height:
            cell_contents = self.model.grid.get_cell_list_contents((new_x, new_y))
            road_present = any(isinstance(agent, RoadCell) for agent in cell_contents)

            if road_present:
                self.model.grid.move_agent(self, (new_x, new_y))
                self.steps_taken += 1  
