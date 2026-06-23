
def calculate_utilization_g_hat(moment_term, Q_Ry, D_t, delta_p_pb):
    """
    Calculate the utilization factor g_hat based on 2022-1355 Local buckling with point load, Rev 3

    Parameters:
    - moment_term: M/Mpc, the normalized moment term.
    - Q_Ry: Q/Ry, the point load term.
    - D_t: D/t, the diameter-to-thickness ratio.
    - delta_p_pb: Δp/p_b, the pressure ratio.

    Returns:
    - g_hat: The calculated utilization factor.
    """
    g_hat = 0.971 * moment_term + 1.039 * Q_Ry * D_t/130 + 0.366 * (delta_p_pb)**2 - 0.261 * delta_p_pb * D_t/20
    return g_hat