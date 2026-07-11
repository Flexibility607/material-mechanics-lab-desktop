import argparse
from collections import defaultdict

from common import (add_io_arguments, default_output, linear_regression, mean,
                    microstrain, read_rows, run_or_template, sample_std,
                    text_value, to_float, write_json, write_rows)


FIELDS = [
    "run", "level", "load_kN",
    "epsilon_1_micro", "epsilon_2_micro", "epsilon_3_micro", "epsilon_4_micro",
    "b1_mm", "t1_mm", "b2_mm", "t2_mm", "b3_mm", "t3_mm",
    "b_mm", "t_mm", "A0_mm2",
]

TEMPLATE = [
    {"run": 1, "level": 1, "load_kN": 2,
     "epsilon_1_micro": 105, "epsilon_2_micro": 103,
     "epsilon_3_micro": -32, "epsilon_4_micro": -33,
     "b1_mm": 24.02, "t1_mm": 7.98,
     "b2_mm": 24.00, "t2_mm": 8.01,
     "b3_mm": 23.98, "t3_mm": 8.00,
     "b_mm": "", "t_mm": "", "A0_mm2": ""},
    {"run": 1, "level": 2, "load_kN": 6,
     "epsilon_1_micro": 402, "epsilon_2_micro": 398,
     "epsilon_3_micro": -126, "epsilon_4_micro": -127,
     "b1_mm": 24.02, "t1_mm": 7.98,
     "b2_mm": 24.00, "t2_mm": 8.01,
     "b3_mm": 23.98, "t3_mm": 8.00,
     "b_mm": "", "t_mm": "", "A0_mm2": ""},
]


def area(row):
    A = to_float(row, "A0_mm2", "A_mm2")
    if A is not None:
        return A

    measured_areas = []
    for idx in range(1, 4):
        Ai = to_float(row, f"A{idx}_mm2")
        if Ai is not None:
            measured_areas.append(Ai)
            continue
        b_i = to_float(row, f"b{idx}_mm")
        t_i = to_float(row, f"t{idx}_mm", f"h{idx}_mm")
        if b_i is not None and t_i is not None:
            measured_areas.append(b_i * t_i)
    if measured_areas:
        return mean(measured_areas)

    b = to_float(row, "b_mm")
    t = to_float(row, "t_mm", "h_mm")
    return None if b is None or t is None else b * t


def force_N(row):
    F = to_float(row, "F_N", "load_N")
    if F is not None:
        return F
    F_kN = to_float(row, "load_kN", "F_kN")
    return None if F_kN is None else F_kN * 1000.0


def combined_strains(row):
    e1 = to_float(row, "epsilon_1_micro", "eps1_micro")
    e2 = to_float(row, "epsilon_2_micro", "eps2_micro")
    e3 = to_float(row, "epsilon_3_micro", "eps3_micro")
    e4 = to_float(row, "epsilon_4_micro", "eps4_micro")

    if e1 is not None and e2 is not None:
        axial = (e1 + e2) / 2.0
    else:
        axial = to_float(row, "strain_long_micro", "epsilon_long_micro")

    if e3 is not None and e4 is not None:
        transverse = (e3 + e4) / 2.0
    else:
        transverse = to_float(row, "strain_trans_micro", "epsilon_trans_micro")

    return e1, e2, e3, e4, axial, transverse


def coefficient_of_variation(values):
    m = mean(values)
    s = sample_std(values)
    if m in (None, 0) or s is None:
        return None
    return abs(s / m)


def run_quality(run_results):
    usable = [r for r in run_results if r["E_i_MPa"] is not None]
    fit = linear_regression(
        [r["strain_for_fit"] for r in run_results],
        [r["sigma_MPa_for_fit"] for r in run_results],
    )
    E_values = [r["E_i_MPa"] for r in usable]
    mu_values = [r["mu_i"] for r in usable]
    cv_E = coefficient_of_variation(E_values)
    r2 = fit.get("r2")
    score = float("inf") if r2 is None else (1.0 - r2) + (cv_E or 0.0)
    return {
        "fit": fit,
        "mean_E_MPa": mean(E_values),
        "mean_mu": mean(mu_values),
        "cv_E": cv_E,
        "score": score,
    }


def sigma_strain_equation(fit):
    slope = fit.get("slope")
    intercept = fit.get("intercept")
    if slope is None or intercept is None:
        return ""
    if abs(intercept) < 1e-9:
        intercept = 0.0
    return f"sigma_MPa = {slope:.6f} * epsilon_F + {intercept:.6f}"


def process(rows):
    groups = defaultdict(list)
    for idx, row in enumerate(rows):
        groups[text_value(row, "run", default="1")].append((idx, row))

    all_results = []
    qualities = {}
    for run, items in groups.items():
        run_results = []
        prev = None
        cumulative_F = 0.0
        cumulative_axial = 0.0

        for _, row in items:
            A = area(row)
            F = force_N(row)
            e1, e2, e3, e4, axial_strain, trans_strain = combined_strains(row)

            dF = to_float(row, "delta_F_N")
            d_axial = to_float(row, "delta_epsilon_F_micro", "delta_epsilon_long_micro")
            d_trans = to_float(row, "delta_epsilon_trans_micro")

            if dF is None and prev is not None and F is not None and prev["F"] is not None:
                dF = F - prev["F"]
            if d_axial is None and prev is not None and axial_strain is not None and prev["axial"] is not None:
                d_axial = axial_strain - prev["axial"]
            if d_trans is None and prev is not None and trans_strain is not None and prev["trans"] is not None:
                d_trans = trans_strain - prev["trans"]

            if F is None and dF is not None:
                cumulative_F += dF
                F_for_fit = cumulative_F
            else:
                F_for_fit = F
            if axial_strain is None and d_axial is not None:
                cumulative_axial += d_axial
                strain_for_fit_micro = cumulative_axial
            else:
                strain_for_fit_micro = axial_strain

            eps_increment = microstrain(d_axial)
            E_i = None
            if A not in (None, 0) and dF is not None and eps_increment not in (None, 0):
                E_i = dF / (A * eps_increment)

            mu_i = None
            if d_axial not in (None, 0) and d_trans is not None:
                mu_i = abs(d_trans / d_axial)

            sigma = None if A in (None, 0) or F_for_fit is None else F_for_fit / A
            strain_dimless = microstrain(strain_for_fit_micro)

            result = {
                "run": run,
                "level": text_value(row, "level"),
                "load_N": F,
                "A0_mm2": A,
                "epsilon_1_micro": e1,
                "epsilon_2_micro": e2,
                "epsilon_3_micro": e3,
                "epsilon_4_micro": e4,
                "epsilon_F_micro": axial_strain,
                "epsilon_trans_micro": trans_strain,
                "delta_F_N": dF,
                "delta_epsilon_F_micro": d_axial,
                "delta_epsilon_trans_micro": d_trans,
                "E_i_MPa": E_i,
                "mu_i": mu_i,
                "sigma_MPa_for_fit": sigma,
                "strain_for_fit": strain_dimless,
                "selected_run": "",
            }
            run_results.append(result)
            prev = {"F": F, "axial": axial_strain, "trans": trans_strain}

        qualities[run] = run_quality(run_results)
        all_results.extend(run_results)

    selected_run = min(qualities, key=lambda r: qualities[r]["score"]) if qualities else None
    for result in all_results:
        result["selected_run"] = "yes" if result["run"] == selected_run else "no"

    selected_quality = qualities.get(selected_run, {})
    selected_fit = selected_quality.get("fit", {})
    selected_r2 = selected_fit.get("r2")
    r2_threshold = 0.99
    hooke_law_verified = selected_r2 is not None and selected_r2 >= r2_threshold
    selected_results = [r for r in all_results if r["run"] == selected_run]
    summary = {
        "experiment": "材料弹性常数 E, mu 的测定",
        "load_sequence_kN": [2, 6, 10, 14, 18],
        "area_rule": "优先使用 A0_mm2；否则按三处截面面积 A0=(A1+A2+A3)/3；再退回 b_mm*t_mm",
        "strain_channels": "epsilon_1, epsilon_2 合成轴向应变；epsilon_3, epsilon_4 合成横向应变",
        "selection_rule": "选择 sigma-epsilon_F 线性拟合 R^2 高且 E_i 离散系数低的一组",
        "selected_run": selected_run,
        "mean_E_MPa": selected_quality.get("mean_E_MPa"),
        "mean_mu": selected_quality.get("mean_mu"),
        "sigma_strain_fit_E_MPa": selected_fit,
        "sigma_strain_equation": sigma_strain_equation(selected_fit),
        "hooke_law_r2_threshold": r2_threshold,
        "hooke_law_verified": hooke_law_verified,
        "required_processing_covered": [
            "三处截面面积平均得到 A0",
            "四片应变片合成轴向应变和横向应变",
            "相邻载荷级作差并逐级计算 E_i 和 mu_i",
            "sigma-epsilon_F 拟合验证单向拉伸胡克定律",
            "重复多遍时选择线性最好且离散性最低的一组",
            "输出平均 E 和 mu 作为实验结论",
        ],
        "conclusion": (
            f"选用第 {selected_run} 组数据；"
            f"sigma-epsilon_F 拟合 R^2={selected_r2:.6f}，满足线性验证要求；"
            f"最终 E={selected_quality.get('mean_E_MPa'):.4f} MPa，"
            f"mu={selected_quality.get('mean_mu'):.6f}。"
        ) if hooke_law_verified else "拟合线性不足，需检查加载、接线或应变读数。",
        "all_run_quality": qualities,
        "selected_rows": len([r for r in selected_results if r["E_i_MPa"] is not None]),
    }
    return all_results, summary


def main():
    parser = argparse.ArgumentParser(
        description="实验三：四片应变片、三次重复加载数据中选择最优组并计算 E 和泊松比"
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
