import argparse
from collections import defaultdict

from common import (add_io_arguments, default_output, linear_regression, mean,
                    microstrain, read_rows, relative_error_pct, run_or_template,
                    text_value, to_float, write_json, write_rows)


FIELDS = [
    "state", "run", "point", "y_mm", "moment_Nmm", "shear_force_N",
    "epsilon_long_micro", "epsilon_trans_micro", "epsilon_45_micro",
    "E_MPa", "mu", "G_MPa", "Iz_mm4", "b_mm", "h_mm",
]

STANDARD_LONGITUDINAL_POINTS = [
    ("S2", -25),
    ("S3", -20),
    ("S4", -10),
    ("S5", 0),
    ("S7", 10),
    ("S8", 20),
    ("S9", 25),
]

TEMPLATE_LONGITUDINAL = {
    "pure_bending": [
        [-188, -151, -75, 1, 77, 153, 189],
        [-191, -153, -76, -1, 75, 151, 192],
    ],
    "three_point": [
        [-194, -155, -78, 2, 79, 156, 193],
        [-196, -157, -80, 1, 78, 158, 196],
    ],
}

TEMPLATE_TRANSVERSE = {
    ("pure_bending", 1, "S2"): 53,
    ("pure_bending", 1, "S9"): -53,
    ("pure_bending", 2, "S2"): 54,
    ("pure_bending", 2, "S9"): -54,
    ("three_point", 1, "S2"): 54,
    ("three_point", 1, "S9"): -55,
    ("three_point", 2, "S2"): 55,
    ("three_point", 2, "S9"): -55,
}

TEMPLATE_EPS45 = {
    ("three_point", 1, "S6"): 61,
    ("three_point", 2, "S6"): 62,
}


def template_row(state, run, point, y_mm, eps_long="", eps_trans="", eps_45=""):
    return {
        "state": state,
        "run": run,
        "point": point,
        "y_mm": y_mm,
        "moment_Nmm": 500000,
        "shear_force_N": 10000 if state == "three_point" else "",
        "epsilon_long_micro": eps_long,
        "epsilon_trans_micro": eps_trans,
        "epsilon_45_micro": eps_45,
        "E_MPa": 210000,
        "mu": 0.28,
        "G_MPa": "",
        "Iz_mm4": "",
        "b_mm": 30,
        "h_mm": 50,
    }


def build_template():
    rows = []
    for state, runs in TEMPLATE_LONGITUDINAL.items():
        for run_index, eps_values in enumerate(runs, start=1):
            for (point, y_mm), eps_long in zip(STANDARD_LONGITUDINAL_POINTS, eps_values):
                eps_trans = TEMPLATE_TRANSVERSE.get((state, run_index, point), "")
                rows.append(template_row(state, run_index, point, y_mm, eps_long, eps_trans))
            if state == "three_point":
                rows.append(template_row(
                    state, run_index, "S6", 0,
                    eps_45=TEMPLATE_EPS45[(state, run_index, "S6")]
                ))
    return rows


TEMPLATE = build_template()


def inertia(row):
    Iz = to_float(row, "Iz_mm4")
    if Iz is not None:
        return Iz
    b = to_float(row, "b_mm")
    h = to_float(row, "h_mm")
    return None if b is None or h is None else b * h ** 3 / 12.0


def moment(row):
    return to_float(row, "moment_Nmm", "M_Nmm", "delta_M_Nmm")


def shear_force(row):
    Q = to_float(row, "shear_force_N", "Q_N", "V_N", "Fs_N")
    if Q is not None:
        return Q
    load = to_float(row, "load_N", "F_N")
    state = classify_state(text_value(row, "state", default="pure_bending"))
    if state == "three_point" and load is not None:
        return load / 2.0
    return None


def shear_modulus(row, E):
    G = to_float(row, "G_MPa")
    if G is not None:
        return G
    mu = to_float(row, "mu")
    if E is None or mu is None:
        return None
    return E / (2.0 * (1.0 + mu))


def classify_state(state):
    text = (state or "").lower()
    if "three" in text or "三" in text:
        return "three_point"
    if "pure" in text or "纯" in text:
        return "pure_bending"
    return text or "pure_bending"


def mean_field(rows, *names):
    return mean([to_float(row, *names) for row in rows])


def average_group(state, point, rows):
    y = mean_field(rows, "y_mm")
    E = mean_field(rows, "E_MPa")
    M = mean([moment(row) for row in rows])
    Q = mean([shear_force(row) for row in rows])
    Iz = mean([inertia(row) for row in rows])
    b = mean_field(rows, "b_mm")
    h = mean_field(rows, "h_mm")
    mu = mean_field(rows, "mu")
    G = mean([shear_modulus(row, to_float(row, "E_MPa")) for row in rows])

    eps_long_micro = mean_field(rows, "epsilon_long_micro", "strain_long_micro")
    eps_trans_micro = mean_field(rows, "epsilon_trans_micro", "strain_trans_micro")
    eps_45_micro = mean_field(rows, "epsilon_45_micro", "strain_45_micro")

    eps_theory = None
    if None not in (M, y, E, Iz) and E != 0 and Iz != 0:
        eps_theory = M * y / (E * Iz)

    sigma_exp = None
    eps_exp = microstrain(eps_long_micro)
    if E is not None and eps_exp is not None:
        sigma_exp = E * eps_exp

    sigma_theory = None
    if None not in (M, y, Iz) and Iz != 0:
        sigma_theory = M * y / Iz

    ratio = None
    if eps_long_micro not in (None, 0) and eps_trans_micro is not None:
        ratio = abs(eps_trans_micro / eps_long_micro)

    gamma_exp_micro = None if eps_45_micro is None else 2.0 * eps_45_micro
    gamma_theory_micro = None
    if eps_45_micro is not None and None not in (Q, b, h, G) and b != 0 and h != 0 and G != 0:
        tau_max = 3.0 * Q / (2.0 * b * h)
        gamma_theory_micro = tau_max / G * 1e6

    run_ids = sorted({text_value(row, "run", default="1") for row in rows})
    return {
        "state": state,
        "point": point,
        "y_mm": y,
        "n_runs": len(run_ids),
        "runs": ",".join(run_ids),
        "moment_Nmm": M,
        "shear_force_N": Q,
        "epsilon_exp_micro": eps_long_micro,
        "epsilon_theory_micro": None if eps_theory is None else eps_theory * 1e6,
        "strain_relative_error_pct": relative_error_pct(
            eps_long_micro, None if eps_theory is None else eps_theory * 1e6
        ),
        "sigma_exp_MPa": sigma_exp,
        "sigma_theory_MPa": sigma_theory,
        "sigma_relative_error_pct": relative_error_pct(sigma_exp, sigma_theory),
        "epsilon_trans_micro": eps_trans_micro,
        "abs_transverse_to_longitudinal_ratio": ratio,
        "epsilon_45_micro": eps_45_micro,
        "gamma_max_exp_micro": gamma_exp_micro,
        "gamma_max_theory_micro": gamma_theory_micro,
        "gamma_relative_error_pct": relative_error_pct(gamma_exp_micro, gamma_theory_micro),
        "E_MPa": E,
        "mu": mu,
        "G_MPa": G,
        "Iz_mm4": Iz,
    }


def run_fit(rows):
    usable = [
        row for row in rows
        if to_float(row, "y_mm") is not None
        and to_float(row, "epsilon_long_micro", "strain_long_micro") is not None
    ]
    return linear_regression(
        [to_float(row, "y_mm") for row in usable],
        [to_float(row, "epsilon_long_micro", "strain_long_micro") for row in usable],
    )


def compare_pure_and_three_point(results):
    by_kind = defaultdict(dict)
    for row in results:
        if row["epsilon_exp_micro"] is None:
            continue
        kind = classify_state(row["state"])
        by_kind[kind][row["point"]] = row

    comparisons = []
    for point, pure in by_kind.get("pure_bending", {}).items():
        three = by_kind.get("three_point", {}).get(point)
        if three is None:
            continue
        comparisons.append({
            "point": point,
            "y_mm": pure["y_mm"],
            "epsilon_pure_micro": pure["epsilon_exp_micro"],
            "epsilon_three_point_micro": three["epsilon_exp_micro"],
            "three_minus_pure_micro": three["epsilon_exp_micro"] - pure["epsilon_exp_micro"],
        })
    return comparisons


def theory_slope_micro_per_mm(rows):
    return mean([
        row["moment_Nmm"] / (row["E_MPa"] * row["Iz_mm4"]) * 1e6
        for row in rows
        if row["moment_Nmm"] is not None
        and row["E_MPa"] not in (None, 0)
        and row["Iz_mm4"] not in (None, 0)
    ])


def summarize_pure_three_point(comparisons):
    diffs = [
        row["three_minus_pure_micro"] for row in comparisons
        if row["three_minus_pure_micro"] is not None
    ]
    return {
        "n": len(diffs),
        "mean_abs_difference_micro": mean([abs(value) for value in diffs]),
        "max_abs_difference_micro": max([abs(value) for value in diffs]) if diffs else None,
    }


def build_conclusions(state_fits, comparison_summary):
    state_labels = {
        "pure_bending": "纯弯",
        "three_point": "三点弯",
    }
    conclusions = []
    for state, info in state_fits.items():
        state_label = state_labels.get(classify_state(state), state)
        fit = info["fit_epsilon_micro_vs_y_mm"]
        slope = fit["slope"]
        r2 = fit["r2"]
        theory_slope = info["theory_epsilon_slope_micro_per_mm"]
        slope_error = info["fit_slope_relative_error_pct"]
        mean_error = info["mean_abs_sigma_error_pct"]
        if slope is not None and r2 is not None:
            conclusions.append(
                f"{state_label}: y-epsilon 拟合斜率 {slope:.4g} με/mm，"
                f"理论斜率 {theory_slope:.4g} με/mm，"
                f"斜率误差 {slope_error:.4g}%，R^2={r2:.6g}，"
                f"平均应力相对误差 {mean_error:.4g}%。"
            )
        ratio = info["mean_abs_transverse_to_longitudinal_ratio"]
        ratio_error = info["transverse_ratio_vs_mu_error_pct"]
        if ratio is not None:
            conclusions.append(
                f"{state_label}: 上下表面横纵应变比平均值 {ratio:.4g}，"
                f"相对泊松比误差 {ratio_error:.4g}%，可作为单向受力假设校核。"
            )
        for gamma in info["gamma_max"]:
            conclusions.append(
                f"{state_label}: {gamma['point']} 最大切应变实验值 "
                f"{gamma['gamma_exp_micro']:.4g} με，理论值 "
                f"{gamma['gamma_theory_micro']:.4g} με，相对误差 "
                f"{gamma['gamma_relative_error_pct']:.4g}%。"
            )

    if comparison_summary["n"]:
        conclusions.append(
            "三点弯与纯弯同 y 测点的应变差平均绝对值 "
            f"{comparison_summary['mean_abs_difference_micro']:.4g} με，"
            f"最大绝对值 {comparison_summary['max_abs_difference_micro']:.4g} με，"
            "用于分析剪力对正应变分布的影响。"
        )
    return conclusions


def process(rows):
    grouped = defaultdict(list)
    run_groups = defaultdict(list)
    order = []

    for idx, row in enumerate(rows):
        state = text_value(row, "state", default="pure_bending")
        point = text_value(row, "point", default=f"P{idx + 1}")
        key = (state, point)
        if key not in grouped:
            order.append(key)
        grouped[key].append(row)
        run_groups[(state, text_value(row, "run", default="1"))].append(row)

    results = [average_group(state, point, grouped[(state, point)]) for state, point in order]

    state_rows = defaultdict(list)
    for row in results:
        state_rows[row["state"]].append(row)

    state_fits = {}
    for state, items in state_rows.items():
        fit = linear_regression(
            [row["y_mm"] for row in items],
            [row["epsilon_exp_micro"] for row in items],
        )
        theory_slope = theory_slope_micro_per_mm(items)
        transverse_ratio = mean([
            row["abs_transverse_to_longitudinal_ratio"] for row in items
        ])
        mu = mean([row["mu"] for row in items])
        state_fits[state] = {
            "fit_epsilon_micro_vs_y_mm": fit,
            "theory_epsilon_slope_micro_per_mm": theory_slope,
            "fit_slope_relative_error_pct": relative_error_pct(fit["slope"], theory_slope),
            "mean_abs_strain_error_pct": mean([
                abs(row["strain_relative_error_pct"]) for row in items
                if row["strain_relative_error_pct"] is not None
            ]),
            "mean_abs_sigma_error_pct": mean([
                abs(row["sigma_relative_error_pct"]) for row in items
                if row["sigma_relative_error_pct"] is not None
            ]),
            "mean_abs_transverse_to_longitudinal_ratio": transverse_ratio,
            "transverse_ratio_vs_mu_error_pct": relative_error_pct(transverse_ratio, mu),
            "gamma_max": [
                {
                    "point": row["point"],
                    "gamma_exp_micro": row["gamma_max_exp_micro"],
                    "gamma_theory_micro": row["gamma_max_theory_micro"],
                    "gamma_relative_error_pct": row["gamma_relative_error_pct"],
                }
                for row in items
                if row["gamma_max_exp_micro"] is not None
            ],
        }

    comparisons = compare_pure_and_three_point(results)
    comparison_summary = summarize_pure_three_point(comparisons)
    summary = {
        "experiment": "直梁弯曲实验",
        "source_based_correction": [
            "讲义和课件均要求在 y-epsilon 坐标系下拟合实验点并与理论结果比较",
            "讲义实验步骤要求重复加载至少两次，课件要求对多次实验结果取平均值",
            "讲义要求对比纯弯状态与三点弯状态，并分析剪力对正应变分布的影响",
            "三点弯中性层 45 度应变片用于求最大切应变：gamma_max=2*epsilon_45",
        ],
        "averaging_rule": "按 state + point 对重复加载结果取平均值后再计算理论值、误差和拟合直线",
        "state_fits": state_fits,
        "run_fits": {
            f"{state}__run_{run}": run_fit(items)
            for (state, run), items in run_groups.items()
        },
        "pure_vs_three_point": comparisons,
        "pure_vs_three_point_summary": comparison_summary,
        "conclusion_checks": {
            "has_repeated_average": all(
                row["n_runs"] >= 2 for row in results
                if row["epsilon_exp_micro"] is not None or row["epsilon_45_micro"] is not None
            ),
            "has_y_epsilon_fit": all(
                info["fit_epsilon_micro_vs_y_mm"]["n"] >= 2
                for info in state_fits.values()
            ),
            "has_theory_error_comparison": all(
                info["mean_abs_sigma_error_pct"] is not None
                for info in state_fits.values()
            ),
            "has_transverse_ratio_check": any(
                info["mean_abs_transverse_to_longitudinal_ratio"] is not None
                for info in state_fits.values()
            ),
            "has_three_point_shear_strain": any(
                info["gamma_max"] for info in state_fits.values()
            ),
            "has_pure_three_point_comparison": comparison_summary["n"] > 0,
        },
        "conclusions": build_conclusions(state_fits, comparison_summary),
    }
    return results, summary


def main():
    parser = argparse.ArgumentParser(
        description="实验五：直梁弯曲重复测量平均、纯弯/三点弯对比和最大切应变计算"
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
