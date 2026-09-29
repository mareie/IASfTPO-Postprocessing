import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CapacityParameters:
    beta: float
    alpha_c: float
    mp: float
    mpc: float
    sp: float
    spc: float
    delta_p_pb: float
    delta_p_pbc: float
    gamma_p: float


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
        self.wt = wall_thickness
        self.ys = yield_strength
        self.ts = tensile_strength
        self.D_t = d_over_t if d_over_t is not None else self.od / self.wt
        self.ys_ts = ys_ts if ys_ts is not None else self.ys / self.ts
        self.qh = qh
        self.capacity = None

    def calculate_capacity_parameters_STF101(self):
        beta = (60 - self.D_t) / 90
        alpha_c = 1 + beta * (self.ys_ts**-1 - 1)

        mp = self.ys * (self.od - self.wt)**2 * self.wt  # Plastic moment
        mpc = alpha_c * mp  # Plastic moment capacity included hardening

        sp = self.ys * math.pi * (self.od - self.wt) * self.wt  # Axial plastic capacity
        spc = alpha_c * sp  # Axial plastic capacity included hardening

        delta_p_pb = math.sqrt(3) / 2 * self.qh
        delta_p_pbc = delta_p_pb / alpha_c

        if delta_p_pb <= 2 / 3:
            gamma_p = 1 - beta
        else:
            gamma_p = 1 - 3 * beta * (1 - delta_p_pb)

        self.capacity = CapacityParameters(
            beta=beta,
            alpha_c=alpha_c,
            mp=mp,
            mpc=mpc,
            sp=sp,
            spc=spc,
            delta_p_pb=delta_p_pb,
            delta_p_pbc=delta_p_pbc,
            gamma_p=gamma_p,
        )
        return self.capacity

    def _require_capacity(self):
        if self.capacity is None:
            raise RuntimeError("Calculate capacity parameters before using them")
        return self.capacity

    @property
    def mpc(self):
        return self._require_capacity().mpc

    @property
    def delta_P_Pb(self):
        return self._require_capacity().delta_p_pb

    def print_capacity_parameters(self):
        capacity = self._require_capacity()
        rows = [
            ("M_p", "Plastic moment", capacity.mp, ",.3f"),
            ("M_pc", "Plastic moment capacity incl. hardening", capacity.mpc, ",.3f"),
            ("S_p", "Axial plastic capacity", capacity.sp, ",.3f"),
            ("S_pc", "Axial plastic capacity incl. hardening", capacity.spc, ",.3f"),
            ("Delta P / P_b", "Pressure ratio", capacity.delta_p_pb, ".3f"),
            ("Delta P / P_bc", "Pressure ratio incl. hardening", capacity.delta_p_pbc, ".3f"),
        ]

        print(f"{'Variable':<16} {'Description':<45} {'Value':>18}")
        print("-" * 81)
        for symbol, description, value, fmt in rows:
            print(f"{symbol:<16} {description:<45} {value:>{fmt}}")