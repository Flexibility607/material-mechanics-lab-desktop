import argparse
import math
from collections import defaultdict

from common import (add_io_arguments, default_output, mean, microstrain,
                    read_rows, relative_error_pct, run_or_template, sample_std,
                    text_value, to_float, write_json, write_rows)


FIELDS = [
    "repeat", "load_case", "point", "surface",
    "F0_N", "Fmax_N", "delta_F_N",
    "epsilon_0_micro", "epsilon_p45_micro", "epsilon_m45_micro",
    "eps0_bridge_reading_micro", "gamma_bridge_reading_micro",
    "E_MPa", "mu", "D_mm", "d_mm", "wall_thickness_mm",
    "D1_mm", "D2_mm", "D3_mm",
    "d1_mm", "d2_mm", "d3_mm",
    "wall_thickness1_mm", "wall_thickness2_mm", "wall_thickness3_mm",
    "Wz_mm3", "Wp_mm3",
    "M_theory_Nmm", "T_theory_Nmm",
    "force_N", "bending_arm_mm", "torsion_arm_mm",
]

TEMPLATE = [
    {"repeat": 1, "load_case": "F0_to_Fmax", "point": "A", "surface": "upper",
     "F0_N": 500, "Fmax_N": 1500, "delta_F_N": 1000,
     "epsilon_0_micro": 348, "epsilon_p45_micro": 311,
     "epsilon_m45_micro": -61, "eps0_bridge_reading_micro": 696,
     "gamma_bridge_reading_micro": -744,
     "E_MPa": 206000, "mu": 0.28, "D_mm": 42.02, "d_mm": "",
     "wall_thickness_mm": 3.01, "D1_mm": "", "D2_mm": "", "D3_mm": "",
     "d1_mm": "", "d2_mm": "", "d3_mm": "",
     "wall_thickness1_mm": "", "wall_thickness2_mm": "",
     "wall_thickness3_mm": "", "Wz_mm3": "", "Wp_mm3": "",
     "M_theory_Nmm": "", "T_theory_Nmm": "",
     "force_N": "", "bending_arm_mm": 240, "torsion_arm_mm": -200},
    {"repeat": 2, "load_case": "F0_to_Fmax", "point": "A", "surface": "upper",
     "F0_N": 500, "Fmax_N": 1500, "delta_F_N": 1000,
     "epsilon_0_micro": 350, "epsilon_p45_micro": 313,
     "epsilon_m45_micro": -59, "eps0_bridge_reading_micro": 700,
     "gamma_bridge_reading_micro": -746,
     "E_MPa": 206000, "mu": 0.28, "D_mm": 42.00, "d_mm": "",
     "wall_thickness_mm": 3.00, "D1_mm": "", "D2_mm": "", "D3_mm": "",
     "d1_mm": "", "d2_mm": "", "d3_mm": "",
     "wall_thickness1_mm": "", "wall_thickness2_mm": "",
     "wall_thickness3_mm": "", "Wz_mm3": "", "Wp_mm3": "",
     "M_theory_Nmm": "", "T_theory_Nmm": "",
     "force_N": "", "bending_arm_mm": 240, "torsion_arm_mm": -200},
    {"repeat": 3, "load_case": "F0_to_Fmax", "point": "A", "surface": "upper",
     "F0_N": 500, "Fmax_N": 1500, "delta_F_N": 1000,
     "epsilon_0_micro": 347, "epsilon_p45_micro": 310,
     "epsilon_m45_micro": -62, "eps0_bridge_reading_micro": 694,
     "gamma_bridge_reading_micro": -742,
     "E_MPa": 206000, "mu": 0.28, "D_mm": 41.98, "d_mm": "",
     "wall_thickness_mm": 2.99, "D1_mm": "", "D2_mm": "", "D3_mm": "",
     "d1_mm": "", "d2_mm": "", "d3_mm": "",
     "wall_thickness1_mm": "", "wall_thickness2_mm": "",
     "wall_thickness3_mm": "", "Wz_mm3": "", "Wp_mm3": "",
     "M_theory_Nmm": "", "T_theory_Nmm": "",
     "force_N": "", "bending_arm_mm": 240, "torsion_arm_mm": -200},
    {"repeat": 4, "load_case": "F0_to_Fmax", "point": "A", "surface": "upper",
     "F0_N": 500, "Fmax_N": 1500, "delta_F_N": 1000,
     "epsilon_0_micro": 349, "epsilon_p45_micro": 312,
     "epsilon_m45_micro": -60, "eps0_bridge_reading_micro": 698,
     "gamma_bridge_reading_micro": -744,
     "E_MPa": 206000, "mu": 0.28, "D_mm": "", "d_mm": "",
     "wall_thickness_mm": "", "D1_mm": "", "D2_mm": "", "D3_mm": "",
     "d1_mm": "", "d2_mm": "", "d3_mm": "",
     "wall_thickness1_mm": "", "wall_thickness2_mm": "",
     "wall_thickness3_mm": "", "Wz_mm3": "", "Wp_mm3": "",
     "M_theory_Nmm": "", "T_theory_Nmm": "",
     "force_N": "", "bending_arm_mm": 240, "torsion_arm_mm": -200},
]


def values(rows, *names):
    return [to_float(row, *names) for row in rows]


def all_values(rows, *names):
    result = []
    for row in rows:
        for name in names:
            value = to_float(row, name)
            if value is not None:
                result.append(value)
    return result


def first_float(rows, *names, default=None):
    for row in rows:
        value = to_float(row, *names)
        if value is not None:
            return value
    return default


def average(rows, *names):
    return mean(values(rows, *names))


def average_all(rows, *names):
    return mean(all_values(rows, *names))


def deviation(rows, *names):
    return sample_std(values(rows, *names))


def deviation_all(rows, *names):
    return sample_std(all_values(rows, *names))


def group_key(row):
    return (
        text_value(row, "load_case", default=""),
        text_value(row, "point", default="A"),
        text_value(row, "surface", default=""),
    )


def section(rows):
    D_names = ("D_mm", "D1_mm", "D2_mm", "D3_mm", "outer_diameter_mm")
    d_names = ("d_mm", "d1_mm", "d2_mm", "d3_mm", "inner_diameter_mm")
    t_names = (
        "wall_thickness_mm", "t_mm",
        "wall_thickness1_mm", "wall_thickness2_mm", "wall_thickness3_mm",
        "t1_mm", "t2_mm", "t3_mm",
    )
    D = average_all(rows, *D_names)
    d = average_all(rows, *d_names)
    wall_thickness = average_all(rows, *t_names)
    Wz = average_all(rows, "Wz_mm3")
    Wp = average_all(rows, "Wp_mm3")
    D_std = deviation_all(rows, *D_names)
    d_std = deviation_all(rows, *d_names)
    wall_thickness_std = deviation_all(rows, *t_names)

    if d is None and D is not None and wall_thickness is not None:
        d = D - 2.0 * wall_thickness
    if d is None:
        d = 0.0

    if D is not None and D != 0:
        factor = 1.0 - (d / D) ** 4
        if Wz is None:
            Wz = math.pi * D ** 3 / 32.0 * factor
        if Wp is None:
            Wp = math.pi * D ** 3 / 16.0 * factor
    return D, d, wall_thickness, D_std, d_std, wall_thickness_std, Wz, Wp


def load_increment(rows):
    delta_F = first_float(rows, "delta_F_N")
    if delta_F is not None:
        return delta_F
    F0 = first_float(rows, "F0_N")
    Fmax = first_float(rows, "Fmax_N")
    if F0 is not None and Fmax is not None:
        return Fmax - F0
    return None


def theory(rows, direct_name, arm_name):
    value = first_float(rows, direct_name)
    if value is not None:
        return value
    force = first_float(rows, "force_N", "load_N")
    if force is None:
        force = load_increment(rows)
    arm = first_float(rows, arm_name)
    return None if force is None or arm is None else force * arm


def principal_angle_error_deg(value, reference):
    if value is None or reference is None:
        return None
    diff = value - reference
    while diff > 45.0:
        diff -= 90.0
    while diff < -45.0:
        diff += 90.0
    return diff


def principal_results(E, mu, ex, ey, gamma):
    if None in (ex, ey, gamma):
        return None, None, None, None, None

    avg = (ex + ey) / 2.0
    radius = math.sqrt(((ex - ey) / 2.0) ** 2 + (gamma / 2.0) ** 2)
    eps1 = avg + radius
    eps2 = avg - radius
    alpha_deg = 0.5 * math.degrees(math.atan2(-gamma, ex - ey))

    sigma1 = sigma2 = None
    if E is not None:
        coef = E / (1.0 - mu ** 2)
        sigma1 = coef * (eps1 + mu * eps2)
        sigma2 = coef * (eps2 + mu * eps1)
    return eps1, eps2, alpha_deg, sigma1, sigma2


def principal_theory(M, T, Wz, Wp):
    if None in (M, T, Wz, Wp) or Wz == 0 or Wp == 0:
        return None, None, None, None, None
    sigma_x = M / Wz
    tau_xy = T / Wp
    avg = sigma_x / 2.0
    radius = math.sqrt((sigma_x / 2.0) ** 2 + tau_xy ** 2)
    sigma1 = avg + radius
    sigma2 = avg - radius
    alpha_deg = 0.5 * math.degrees(math.atan2(-2.0 * tau_xy, sigma_x))
    return sigma_x, tau_xy, sigma1, sigma2, alpha_deg


def process_group(load_case, point, surface, rows):
    E = first_float(rows, "E_MPa")
    mu = first_float(rows, "mu", default=0.28)
    F0 = first_float(rows, "F0_N")
    Fmax = first_float(rows, "Fmax_N")
    delta_F = load_increment(rows)
    bending_arm = first_float(rows, "bending_arm_mm")
    torsion_arm = first_float(rows, "torsion_arm_mm")

    eps0_avg = average(rows, "epsilon_0_micro", "eps0_micro")
    eps45_avg = average(rows, "epsilon_p45_micro", "epsilon_45_micro")
    epsm45_avg = average(rows, "epsilon_m45_micro", "epsilon_minus45_micro")
    eps0_bridge_avg = average(rows, "eps0_bridge_reading_micro")
    gamma_bridge_avg = average(rows, "gamma_bridge_reading_micro")

    eps0_for_rosette_micro = eps0_avg
    if eps0_for_rosette_micro is None and eps0_bridge_avg is not None:
        eps0_for_rosette_micro = eps0_bridge_avg / 2.0

    gamma_rosette_micro = None
    if epsm45_avg is not None and eps45_avg is not None:
        gamma_rosette_micro = epsm45_avg - eps45_avg

    eps0_for_M_micro = eps0_avg
    bridge_epsilon0_equiv_micro = None
    if eps0_bridge_avg is not None:
        bridge_epsilon0_equiv_micro = eps0_bridge_avg / 2.0
        eps0_for_M_micro = bridge_epsilon0_equiv_micro

    gamma_for_T_micro = gamma_rosette_micro
    bridge_gamma_equiv_micro = None
    if gamma_bridge_avg is not None:
        bridge_gamma_equiv_micro = gamma_bridge_avg / 2.0
        gamma_for_T_micro = bridge_gamma_equiv_micro

    ex = microstrain(eps0_for_rosette_micro)
    ey = None
    if None not in (eps45_avg, epsm45_avg, eps0_for_rosette_micro):
        ey = microstrain(eps45_avg + epsm45_avg - eps0_for_rosette_micro)
    gamma = microstrain(gamma_rosette_micro)

    eps1, eps2, alpha_deg, sigma1, sigma2 = principal_results(E, mu, ex, ey, gamma)

    D, d, wall_thickness, D_std, d_std, wall_thickness_std, Wz, Wp = section(rows)
    G = None if E is None else E / (2.0 * (1.0 + mu))
    M_exp = None if None in (E, Wz, eps0_for_M_micro) else E * Wz * microstrain(eps0_for_M_micro)
    T_exp = None if None in (G, Wp, gamma_for_T_micro) else G * Wp * microstrain(gamma_for_T_micro)
    M_th = theory(rows, "M_theory_Nmm", "bending_arm_mm")
    T_th = theory(rows, "T_theory_Nmm", "torsion_arm_mm")
    sigma_x_th, tau_xy_th, sigma1_th, sigma2_th, angle_th = principal_theory(
        M_th, T_th, Wz, Wp
    )

    return {
        "load_case": load_case,
        "point": point,
        "surface": surface,
        "repeat_count": len(rows),
        "F0_N": F0,
        "Fmax_N": Fmax,
        "delta_F_N": delta_F,
        "epsilon_0_avg_micro": eps0_avg,
        "epsilon_0_std_micro": deviation(rows, "epsilon_0_micro", "eps0_micro"),
        "epsilon_p45_avg_micro": eps45_avg,
        "epsilon_p45_std_micro": deviation(rows, "epsilon_p45_micro", "epsilon_45_micro"),
        "epsilon_m45_avg_micro": epsm45_avg,
        "epsilon_m45_std_micro": deviation(rows, "epsilon_m45_micro", "epsilon_minus45_micro"),
        "eps0_bridge_reading_avg_micro": eps0_bridge_avg,
        "eps0_bridge_reading_std_micro": deviation(rows, "eps0_bridge_reading_micro"),
        "epsilon_0_from_half_bridge_micro": bridge_epsilon0_equiv_micro,
        "gamma_bridge_reading_avg_micro": gamma_bridge_avg,
        "gamma_bridge_reading_std_micro": deviation(rows, "gamma_bridge_reading_micro"),
        "gamma_xy_from_bridge_micro": bridge_gamma_equiv_micro,
        "epsilon_x": ex,
        "epsilon_y": ey,
        "gamma_xy_from_rosette": gamma,
        "epsilon_0_for_M_micro": eps0_for_M_micro,
        "gamma_xy_for_T_micro": gamma_for_T_micro,
        "principal_epsilon_1": eps1,
        "principal_epsilon_2": eps2,
        "principal_angle_deg": alpha_deg,
        "sigma_1_MPa": sigma1,
        "sigma_2_MPa": sigma2,
        "E_MPa": E,
        "mu": mu,
        "D_mm": D,
        "D_std_mm": D_std,
        "d_mm": d,
        "d_std_mm": d_std,
        "wall_thickness_mm": wall_thickness,
        "wall_thickness_std_mm": wall_thickness_std,
        "Wz_mm3": Wz,
        "Wp_mm3": Wp,
        "bending_arm_mm": bending_arm,
        "torsion_arm_mm": torsion_arm,
        "M_exp_Nmm": M_exp,
        "M_theory_Nmm": M_th,
        "M_error_pct": relative_error_pct(M_exp, M_th),
        "T_exp_Nmm": T_exp,
        "T_theory_Nmm": T_th,
        "T_error_pct": relative_error_pct(T_exp, T_th),
        "sigma_x_theory_MPa": sigma_x_th,
        "tau_xy_theory_MPa": tau_xy_th,
        "sigma_1_theory_MPa": sigma1_th,
        "sigma_1_error_pct": relative_error_pct(sigma1, sigma1_th),
        "sigma_2_theory_MPa": sigma2_th,
        "sigma_2_error_pct": relative_error_pct(sigma2, sigma2_th),
        "principal_angle_theory_deg": angle_th,
        "principal_angle_error_deg": principal_angle_error_deg(alpha_deg, angle_th),
    }


def process(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[group_key(row)].append(row)

    results = []
    for key, group_rows in groups.items():
        results.append(process_group(*key, group_rows))

    summary = {
        "experiment": "弯扭组合试验",
        "loading_scheme": "重复加载法：F0=500 N，Fmax=1500 N，Delta F=1000 N，重复4次；每个测点对应读数取平均后计算。",
        "bridge_rule": "弯矩半桥显示读数为 2epsilon_0，扭矩桥路显示读数为 2gamma_xy，计算 M 和 T 前均需除以 2。",
        "required_processing": "已覆盖讲义要求：尺寸平均、重复加载读数平均、应变花主应力与主方向、弯矩、扭矩、理论值比较和误差分析。",
        "groups": len(results),
        "mean_abs_M_error_pct": mean([
            abs(r["M_error_pct"]) for r in results if r["M_error_pct"] is not None
        ]),
        "mean_abs_T_error_pct": mean([
            abs(r["T_error_pct"]) for r in results if r["T_error_pct"] is not None
        ]),
        "mean_abs_sigma_1_error_pct": mean([
            abs(r["sigma_1_error_pct"]) for r in results
            if r["sigma_1_error_pct"] is not None
        ]),
        "mean_abs_sigma_2_error_pct": mean([
            abs(r["sigma_2_error_pct"]) for r in results
            if r["sigma_2_error_pct"] is not None
        ]),
        "mean_abs_principal_angle_error_deg": mean([
            abs(r["principal_angle_error_deg"]) for r in results
            if r["principal_angle_error_deg"] is not None
        ]),
        "mean_sigma_1_MPa": mean([r["sigma_1_MPa"] for r in results]),
        "mean_sigma_2_MPa": mean([r["sigma_2_MPa"] for r in results]),
    }
    return results, summary


def main():
    parser = argparse.ArgumentParser(
        description="实验七：弯扭组合重复加载数据处理，计算主应力、弯矩和扭矩"
    )
    add_io_arguments(parser)
    args = parser.parse_args()
    if run_or_template(parser, args, FIELDS, TEMPLATE):
        return
    results, summary = process(read_rows(args.input))
    write_rows(args.output or default_output(args.input), results)
    if args.summary:
        write_json(args.summary, summary)


if __name__ == "__main__":
    main()
