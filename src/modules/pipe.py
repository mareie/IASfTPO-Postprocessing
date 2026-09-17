import math
from dataclasses import dataclass


@dataclass
class Pipe_info:
    def __init__(self, diameter, thickness, yield_strength):
        self.outer_diameter = diameter
        self.thickness = thickness
        self.yield_strength = yield_strength

    def calculate_capacity_parameters(self):
        self.beta = (60 - self.outer_diameter / self.thickness) / 90
        self.alpha_c = 1 + self.beta * (self.yield_strength / self.yield_strength - 1)

        self.moment_plastic = self.yield_strength * (self.outer_diameter - self.thickness)**2 * self.thickness
        self.moment_capacity = self.alpha_c * self.moment_plastic

        self.axial_load_capacity_plastic = self.yield_strength * math.pi * (self.outer_diameter - self.thickness) * self.thickness
        self.effective_axial_force_capacity = self.alpha_c * self.axial_load_capacity_plastic