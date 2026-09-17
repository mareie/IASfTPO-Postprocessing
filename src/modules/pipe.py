import math
from dataclasses import dataclass


@dataclass
class Pipe:
    def __init__(
        self,
        outer_diameter,
        wall_thickness,
        yield_strength,
        tensile_strength,
        d_over_t=None,
        ys_ts=None,
        qh=0,
    ):
        self.od = outer_diameter
        self.th = wall_thickness
        self.ys = yield_strength
        self.ts = tensile_strength
        self.D_t = d_over_t if d_over_t is not None else self.od / self.th
        self.ys_ts = ys_ts if ys_ts is not None else self.ys / self.ts
        self.qh = qh

    def calculate_capacity_parameters(self):
        self.beta = (60 - self.D_t) / 90
        self.alpha_c = 1 + self.beta * (self.ys_ts**-1 - 1)

        self.mp = self.ys * (self.od - self.th)**2 * self.th  # Plastic moment
        self.mpc = self.alpha_c * self.mp  # Plastic moment capacity included hardening

        self.sp = self.ys * math.pi * (self.od - self.th) * self.th  # Axial plastic capacity
        self.spc = self.alpha_c * self.sp  # Axial plastic capacity included hardening

        self.delta_P_Pb = math.sqrt(3) / 2  * self.qh
        self.delta_P_Pbc =  self.delta_P_Pb / self.alpha_c

        if self.delta_P_Pb <= 2 / 3:
            self.gamma_p = 1 - self.beta
        elif self.delta_P_Pb > 2 / 3:
            self.gamma_p = 1 - 3 * self.beta * (1 - self.delta_P_Pb)

    def print_capacity_parameters(self):
        rows = [
            ("M_p", "Plastic moment", self.mp, ",.3f"),
            ("M_pc", "Plastic moment capacity incl. hardening", self.mpc, ",.3f"),
            ("S_p", "Axial plastic capacity", self.sp, ",.3f"),
            ("S_pc", "Axial plastic capacity incl. hardening", self.spc, ",.3f"),
            ("Delta P / P_b", "Pressure ratio", self.delta_P_Pb, ".3f"),
            ("Delta P / P_bc", "Pressure ratio incl. hardening", self.delta_P_Pbc, ".3f"),
        ]

        print(f"{'Variable':<16} {'Description':<45} {'Value':>18}")
        print("-" * 81)
        for symbol, description, value, fmt in rows:
            print(f"{symbol:<16} {description:<45} {value:>{fmt}}")