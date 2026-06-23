




def calculate_utilization_factor_STF101(moment_term, force_term, pressure_term, safety_factor_moment=1, safety_factor_force=1, takeSqrt:bool = False):
    """
    Calculate LCC utilization for combining moment, force, and pressure terms according to ST-F101 combined loading criterion.
    
    Parameters:
    - moment_term: M/Mpc, the normalized moment term.
    - force_term: S/Spc, the normalized axial force term.
    - pressure_term: The normalized pressure term.
    - safety_factor_moment: Safety factor to apply to the moment term (default is 1, meaning no safety factor).
    - safety_factor_force: Safety factor to apply to the force term (default is 1, meaning no safety factor).
    - takeSqrt: If False, return how it is defined in DNV-ST-F101. If True return the square root of that, which is how it is typically used as a linear utilization factor.
    """

    LCC_STF101 = ((moment_term * safety_factor_moment + (safety_factor_force * force_term)**2)**2 + (pressure_term)**2)  # DNV-ST-F101

    if takeSqrt: return LCC_STF101**0.5     
    else: return LCC_STF101


def calculate_allowable_moment_util_STF101(force_term, pressure_term, safety_factor_moment=1, safety_factor_force=1):
    """
    Calculate allowable moment utilization for combining moment, force, and pressure terms according to ST-F101 combined loading criterion.
    
    Parameters:
    - force_term: S/Spc, the normalized axial force term.
    - pressure_term: The normalized pressure term.
    - safety_factor_moment: Safety factor to apply to the moment term (default is 1, meaning no safety factor).
    - safety_factor_force: Safety factor to apply to the force term (default is 1, meaning no safety factor).
    Returns:
    - the allowable moment term (M/Mpc) that would satisfy the criterion for the given force and pressure terms.
    - multiply with Mpc to get the actual allowable moment (e.g. to be compared with FE output)

    """

    moment_STF101 = ( (1 - (pressure_term)**2)**0.5 - (safety_factor_force * force_term)**2 ) / safety_factor_moment

    return moment_STF101