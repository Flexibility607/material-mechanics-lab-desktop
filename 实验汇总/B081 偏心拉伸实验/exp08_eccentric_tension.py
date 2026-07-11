import argparse
import math

from common import (add_io_arguments, default_output, mean, microstrain, read_rows,
                    run_or_template, text_value, to_float, write_json, write_rows)


FIELDS = [
    "run", "F0_kN", "Fmax_kN", "delta_F_kN",
    "epsilon_max_micro", "full_bridge_reading_micro",
    "half_bridge_M1_reading_micro", "half_bridge_M2_reading_micro",
    "epsilon_F_micro", "epsilon_M1_micro", "epsilon_M2_micro",
    "epsilon_a_micro", "epsilon_b_micro", "epsilon_1_micro", "epsilon_2_micro",
    "E_MPa", "h_mm", "b_mm", "A_mm2", "Wz_mm3", "Wy_mm3"
]

TEMPLATE = [
    {"run": 1, "F0_kN": 2, "Fmax_kN": 12, "delta_F_kN": 10,
     "epsilon_max_micro": 821, "full_bridge_reading_micro": 506,
     "half_bridge_M1_reading_micro": 1136, "half_bridge_M2_reading_micro": "",
     "epsilon_F_micro": "", "epsilon_M1_micro": "", "epsilon_M2_micro": "",
     "epsilon_a_micro": "", "epsilon_b_micro": "", "epsilon_1_micro": "", "epsilon_2_micro": "",
     "E_MPa": "", "h_mm": 24, "b_mm": 8, "A_mm2": "", "Wz_mm3": "", "Wy_mm3": ""},
    {"run": 2, "F0_kN": 2, "Fmax_kN": 12, "delta_F_kN": 10,
     "epsilon_max_micro": 823, "full_bridge_reading_micro": 504,
     "half_bridge_M1_reading_micro": 1140, "half_bridge_M2_reading_micro": "",
     "epsilon_F_micro": "", "epsilon_M1_micro": "", "epsilon_M2_micro": "",
     "epsilon_a_micro": "", "epsilon_b_micro": "", "epsilon_1_micro": "", "epsilon_2_micro": "",
     "E_MPa": "", "h_mm": 24, "b_mm": 8, "A_mm2": "", "Wz_mm3": "", "Wy_mm3": ""},
    {"run": 3, "F0_kN": 2, "Fmax_kN": 12, "delta_F_kN": 10,
     "epsilon_max_micro": 819, "full_bridge_reading_micro": 507,
     "half_bridge_M1_reading_micro": 1134, "half_bridge_M2_reading_micro": "",
     "epsilon_F_micro": "", "epsilon_M1_micro": "", "epsilon_M2_micro": "",
     "epsilon_a_micro": "", "epsilon_b_micro": "", "epsilon_1_micro": "", "epsilon_2_micro": "",
     "E_MPa": "", "h_mm": 24, "b_mm": 8, "A_mm2": "", "Wz_mm3": "", "Wy_mm3": ""},
    {"run": 4, "F0_kN": 2, "Fmax_kN": 12, "delta_F_kN": 10,
     "epsilon_max_micro": 822, "full_bridge_reading_micro": 505,
     "half_bridge_M1_reading_micro": 1138, "half_bridge_M2_reading_micro": "",
     "epsilon_F_micro": "", "epsilon_M1_micro": "", "epsilon_M2_micro": "",
     "epsilon_a_micro": "", "epsilon_b_micro": "", "epsilon_1_micro": "", "epsilon_2_micro": "",
     "E_MPa": "", "h_mm": 24, "b_mm": 8, "A_mm2": "", "Wz_mm3": "", "Wy_mm3": ""},
]


def force_n(row, n_names, kn_names):
    value = to_float(row, *n_names)
    if value is not None:
        return value
    value = to_float(row, *kn_names)
    return None if value is None else value * 1000.0


def loading(row):
    f0 = force_n(row, ("F0_N", "initial_F_N"), ("F0_kN", "initial_F_kN"))
    fmax = force_n(row, ("Fmax_N", "maximum_F_N"), ("Fmax_kN", "maximum_F_kN"))
    delta_f = force_n(
        row,
        ("delta_F_N", "Delta_F_N", "F_N"),
        ("delta_F_kN", "Delta_F_kN", "F_kN"),
    )
    if delta_f is None and f0 is not None and fmax is not None:
        delta_f = fmax - f0
    return f0, fmax, delta_f


def section(row):
    h = to_float(row, "h_mm")
    b = to_float(row, "b_mm")
    A = to_float(row, "A_mm2")
    Wz = to_float(row, "Wz_mm3", "W_mm3")
    Wy = to_float(row, "Wy_mm3")
    if A is None and h is not None and b is not None:
        A = h * b
    if Wz is None and h is not None and b is not None:
        Wz = h * b ** 2 / 6.0
    if Wy is None and h is not None and b is not None:
        Wy = b * h ** 2 / 6.0
    return A, Wz, Wy


def strain_components(row):
    eps_max = microstrain(to_float(
        row, "epsilon_max_micro", "delta_epsilon_max_micro",
        "quarter_bridge_reading_micro"
    ))
    eps_F = microstrain(to_float(row, "epsilon_F_micro", "delta_epsilon_F_micro"))
    eps_M1 = microstrain(to_float(row, "epsilon_M1_micro", "epsilon_M_micro", "delta_epsilon_M1_micro"))
    eps_M2 = microstrain(to_float(row, "epsilon_M2_micro", "delta_epsilon_M2_micro"))

    ea = to_float(row, "epsilon_a_micro", "epsilon_ra_micro")
    eb = to_float(row, "epsilon_b_micro", "epsilon_rb_micro")
    e1 = to_float(row, "epsilon_1_micro", "epsilon_r1_micro")
    e2 = to_float(row, "epsilon_2_micro", "epsilon_r2_micro")

    if eps_F is None and ea is not None and eb is not None:
        eps_F = microstrain((ea + eb) / 2.0)
    if eps_F is None and e1 is not None and e2 is not None:
        eps_F = microstrain((e1 + e2) / 2.0)
    if eps_M1 is None and ea is not None and eb is not None:
        eps_M1 = microstrain((ea - eb) / 2.0)
    if eps_M2 is None and e1 is not None and e2 is not None:
        eps_M2 = microstrain((e1 - e2) / 2.0)

    full_reading = to_float(
        row, "full_bridge_reading_micro", "full_bridge_ra_rb_reading_micro",
        "full_bridge_Ra_Rb_reading_micro"
    )
    full_reading_12 = to_float(
        row, "full_bridge_R1_R2_reading_micro", "full_bridge_r1_r2_reading_micro"
    )
    half_M1_reading = to_float(
        row, "half_bridge_M1_reading_micro", "half_bridge_reading_micro",
        "half_bridge_ra_rb_reading_micro", "half_bridge_Ra_Rb_reading_micro"
    )
    half_M2_reading = to_float(
        row, "half_bridge_M2_reading_micro",
        "half_bridge_R1_R2_reading_micro", "half_bridge_r1_r2_reading_micro"
    )

    if eps_F is None and full_reading is not None:
        eps_F = microstrain(full_reading / 2.0)
    if eps_F is None and full_reading_12 is not None:
        eps_F = microstrain(full_reading_12 / 2.0)
    if eps_M1 is None and half_M1_reading is not None:
        eps_M1 = microstrain(half_M1_reading / 2.0)
    if eps_M2 is None and half_M2_reading is not None:
        eps_M2 = microstrain(half_M2_reading / 2.0)

    if eps_max is None and eps_F is not None:
        eps_max = eps_F + (eps_M1 or 0.0) + (eps_M2 or 0.0)
    return eps_max, eps_F, eps_M1, eps_M2


def resultant(e1, e2):
    if e1 is None:
        return e2
    if e2 is None:
        return e1
    return math.sqrt(e1 ** 2 + e2 ** 2)


def process(rows):
    results = []
    for row in rows:
        f0, fmax, delta_f = loading(row)
        A, Wz, Wy = section(row)
        E_input = to_float(row, "E_MPa")
        eps_max, eps_F, eps_M1, eps_M2 = strain_components(row)

        E_calc = None if delta_f is None or A in (None, 0) or eps_F in (None, 0) else delta_f / (A * eps_F)
        E_used = E_input if E_input is not None else E_calc
        sigma_max = None if E_used is None or eps_max is None else E_used * eps_max
        e1_mm = None if None in (eps_M1, E_used, Wz, delta_f) or delta_f == 0 else eps_M1 * E_used * Wz / delta_f
        e2_mm = None if None in (eps_M2, E_used, Wy, delta_f) or delta_f == 0 else eps_M2 * E_used * Wy / delta_f

        results.append({
            "run": text_value(row, "run"),
            "F0_N": f0,
            "Fmax_N": fmax,
            "delta_F_N": delta_f,
            "A_mm2": A,
            "Wz_mm3": Wz,
            "Wy_mm3": Wy,
            "epsilon_max": eps_max,
            "epsilon_F": eps_F,
            "epsilon_M1": eps_M1,
            "epsilon_M2": eps_M2,
            "E_calc_MPa": E_calc,
            "E_used_MPa": E_used,
            "sigma_max_MPa": sigma_max,
            "eccentricity_e1_mm": e1_mm,
            "eccentricity_e2_mm": e2_mm,
            "eccentricity_e_mm": resultant(e1_mm, e2_mm),
        })

    summary = {
        "experiment": "偏心拉伸实验",
        "loading_scheme": {
            "mean_F0_kN": None if mean([r["F0_N"] for r in results]) is None else mean([r["F0_N"] for r in results]) / 1000.0,
            "mean_Fmax_kN": None if mean([r["Fmax_N"] for r in results]) is None else mean([r["Fmax_N"] for r in results]) / 1000.0,
            "mean_delta_F_kN": None if mean([r["delta_F_N"] for r in results]) is None else mean([r["delta_F_N"] for r in results]) / 1000.0,
            "repetition_count": len(results),
        },
        "mean_epsilon_max": mean([r["epsilon_max"] for r in results]),
        "mean_epsilon_F": mean([r["epsilon_F"] for r in results]),
        "mean_epsilon_M1": mean([r["epsilon_M1"] for r in results]),
        "mean_epsilon_M2": mean([r["epsilon_M2"] for r in results]),
        "mean_E_calc_MPa": mean([r["E_calc_MPa"] for r in results]),
        "mean_sigma_max_MPa": mean([r["sigma_max_MPa"] for r in results]),
        "mean_eccentricity_e1_mm": mean([r["eccentricity_e1_mm"] for r in results]),
        "mean_eccentricity_e2_mm": mean([r["eccentricity_e2_mm"] for r in results]),
        "mean_eccentricity_e_mm": mean([r["eccentricity_e_mm"] for r in results]),
        "lecture_requirements_check": [
            "按重复加载法记录 F0、Fmax、Delta F、N，并对各次结果求平均",
            "由 1/4 桥读数或应变分量合成横截面最大正应变增量",
            "由全桥读数或直接输入的 epsilon_F 求材料弹性模量 E",
            "由 E 和最大正应变增量求实验段横截面最大正应力增量",
            "由半桥弯曲应变分量求试件圆孔偏心距 e",
        ],
        "conclusion": {
            "mean_E_GPa": None if mean([r["E_calc_MPa"] for r in results]) is None else mean([r["E_calc_MPa"] for r in results]) / 1000.0,
            "mean_sigma_max_MPa": mean([r["sigma_max_MPa"] for r in results]),
            "mean_eccentricity_e_mm": mean([r["eccentricity_e_mm"] for r in results]),
            "note": "样例数据已覆盖讲义要求的最大正应变、弹性模量、最大正应力增量和偏心距计算。",
        },
    }
    return results, summary


def main():
    parser = argparse.ArgumentParser(description="实验八：偏心拉伸重复加载数据处理")
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
