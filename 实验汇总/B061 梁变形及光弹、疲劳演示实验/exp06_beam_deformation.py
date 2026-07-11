import argparse
import math

from common import (add_io_arguments, default_output, mean, microstrain, read_rows,
                    relative_error_pct, run_or_template, text_value, to_float,
                    write_json, write_rows)


FIELDS = [
    "case", "point", "x_mm", "deflection_mm", "P_N", "l_mm",
    "b_mm", "h_mm", "E_MPa", "theta_delta_mm", "theta_a_mm",
    "theta_exp_rad", "delta12_mm", "delta21_mm", "P1_N", "P2_N",
    "epsilon_max1_micro", "epsilon_max2_micro", "l12_mm", "Wz_mm3",
    "m0_kg", "epsilon_max_x_micro", "epsilon_max_0_micro",
    "demo_item", "light_field", "fringe_order",
    "material_fringe_value_N_per_mm", "thickness_mm", "stress_MPa",
    "stress_ratio", "cycle_count", "runout", "observation", "expected",
    "fracture_feature", "notes",
]

TEMPLATE = [
    {"case": "deflection", "point": "O", "x_mm": 0,
     "deflection_mm": 0, "P_N": 29.4, "l_mm": 600,
     "b_mm": 20, "h_mm": 5, "E_MPa": 210000},
    {"case": "deflection", "point": "A", "x_mm": 100,
     "deflection_mm": -1.42, "P_N": 29.4, "l_mm": 600,
     "b_mm": 20, "h_mm": 5, "E_MPa": 210000},
    {"case": "deflection", "point": "B", "x_mm": 200,
     "deflection_mm": -2.58, "P_N": 29.4, "l_mm": 600,
     "b_mm": 20, "h_mm": 5, "E_MPa": 210000},
    {"case": "deflection", "point": "C", "x_mm": 300,
     "deflection_mm": -3.01, "P_N": 29.4, "l_mm": 600,
     "b_mm": 20, "h_mm": 5, "E_MPa": 210000},
    {"case": "deflection", "point": "D", "x_mm": 400,
     "deflection_mm": -2.55, "P_N": 29.4, "l_mm": 600,
     "b_mm": 20, "h_mm": 5, "E_MPa": 210000},
    {"case": "deflection", "point": "E", "x_mm": 500,
     "deflection_mm": -1.40, "P_N": 29.4, "l_mm": 600,
     "b_mm": 20, "h_mm": 5, "E_MPa": 210000},
    {"case": "deflection", "point": "F", "x_mm": 600,
     "deflection_mm": 0, "P_N": 29.4, "l_mm": 600,
     "b_mm": 20, "h_mm": 5, "E_MPa": 210000},
    {"case": "slope", "point": "left_support", "theta_delta_mm": -1.50,
     "theta_a_mm": 100, "P_N": 29.4, "l_mm": 600, "b_mm": 20,
     "h_mm": 5, "E_MPa": 210000},
    {"case": "reciprocity", "point": "point_1_2", "delta12_mm": 0.86,
     "delta21_mm": 0.85, "P1_N": 29.4, "P2_N": 29.4},
    {"case": "cantilever_method1", "point": "unknown_mass",
     "epsilon_max1_micro": 120, "epsilon_max2_micro": 148,
     "l12_mm": 120, "E_MPa": 210000, "Wz_mm3": 80},
    {"case": "cantilever_method2", "point": "unknown_mass_ratio",
     "m0_kg": 0.2, "epsilon_max_x_micro": 410,
     "epsilon_max_0_micro": 205},
    {"case": "photoelastic", "demo_item": "pure_bending",
     "light_field": "circular_dark", "fringe_order": 2,
     "material_fringe_value_N_per_mm": 6.5, "thickness_mm": 5,
     "observation": "等差线近似平行且关于中性层对称",
     "expected": "纯弯梁等差线反映弯曲正应力沿高度近似线性变化"},
    {"case": "photoelastic", "demo_item": "ring_diametral_compression",
     "light_field": "circular_dark", "fringe_order": 3,
     "material_fringe_value_N_per_mm": 6.5, "thickness_mm": 5,
     "observation": "圆环内外边缘及加载点附近条纹密集",
     "expected": "圆环对径受压时应力分布不均并出现应力集中"},
    {"case": "fatigue", "demo_item": "high_stress", "stress_MPa": 360,
     "stress_ratio": -1, "cycle_count": 120000, "runout": "no",
     "fracture_feature": "裂纹源、扩展区和瞬断区较清楚",
     "expected": "应力水平较高时疲劳寿命较短"},
    {"case": "fatigue", "demo_item": "low_stress", "stress_MPa": 260,
     "stress_ratio": -1, "cycle_count": 850000, "runout": "no",
     "fracture_feature": "扩展区面积较大",
     "expected": "应力降低时疲劳寿命增加"},
    {"case": "fatigue", "demo_item": "runout", "stress_MPa": 220,
     "stress_ratio": -1, "cycle_count": 1000000, "runout": "yes",
     "notes": "记为未断裂点",
     "expected": "低于或接近疲劳极限时可能不发生破坏"},
]

G = 9.80665


def inertia(row):
    b = to_float(row, "b_mm")
    h = to_float(row, "h_mm")
    return None if b is None or h is None else b * h ** 3 / 12.0


def section_modulus(row):
    Wz = to_float(row, "Wz_mm3")
    if Wz is not None:
        return Wz
    b = to_float(row, "b_mm")
    h = to_float(row, "h_mm")
    return None if b is None or h is None else b * h ** 2 / 6.0


def deflection_theory(P, l, E, I, x):
    if None in (P, l, E, I, x) or E == 0 or I == 0:
        return None
    u = min(x, l - x)
    return P * u / (12.0 * E * I) * (u ** 2 - 0.75 * l ** 2)


def support_theta_theory(P, l, E, I):
    if None in (P, l, E, I) or E == 0 or I == 0:
        return None
    return -P * l ** 2 / (16.0 * E * I)


def yes_value(value):
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是", "未断裂", "runout"}


def log10_positive(value):
    if value is None or value <= 0:
        return None
    return math.log10(value)


def process(rows):
    results = []
    for row in rows:
        case = text_value(row, "case", default="deflection").lower()
        P = to_float(row, "P_N")
        l = to_float(row, "l_mm")
        E = to_float(row, "E_MPa")
        I = inertia(row)
        base = {"case": case, "point": text_value(row, "point")}

        if case in {"deflection", "simply_supported", ""}:
            x = to_float(row, "x_mm")
            f_exp = to_float(row, "deflection_mm")
            f_th = deflection_theory(P, l, E, I, x)
            results.append({
                **base,
                "x_mm": x,
                "deflection_exp_mm": f_exp,
                "deflection_theory_mm": f_th,
                "deflection_error_pct": relative_error_pct(f_exp, f_th),
                "I_mm4": I,
            })
        elif case == "slope":
            theta_exp = to_float(row, "theta_exp_rad")
            d = to_float(row, "theta_delta_mm")
            a = to_float(row, "theta_a_mm")
            if theta_exp is None and d is not None and a not in (None, 0):
                theta_exp = d / a
            theta_th = support_theta_theory(P, l, E, I)
            results.append({
                **base,
                "theta_exp_rad": theta_exp,
                "theta_theory_rad": theta_th,
                "theta_error_pct": relative_error_pct(theta_exp, theta_th),
                "I_mm4": I,
            })
        elif case == "reciprocity":
            d12 = to_float(row, "delta12_mm")
            d21 = to_float(row, "delta21_mm")
            P1 = to_float(row, "P1_N", default=P)
            P2 = to_float(row, "P2_N", default=P)
            lhs = None if P1 is None or d12 is None else P1 * d12
            rhs = None if P2 is None or d21 is None else P2 * d21
            results.append({
                **base,
                "P1_delta12_Nmm": lhs,
                "P2_delta21_Nmm": rhs,
                "reciprocity_error_pct": relative_error_pct(lhs, rhs),
                "delta_difference_mm": None if d12 is None or d21 is None else d12 - d21,
            })
        elif case == "cantilever_method1":
            e1 = to_float(row, "epsilon_max1_micro")
            e2 = to_float(row, "epsilon_max2_micro")
            de = None if e1 is None or e2 is None else microstrain(e2 - e1)
            l12 = to_float(row, "l12_mm")
            Wz = section_modulus(row)
            force_N = None if None in (de, E, Wz, l12) or l12 == 0 else de * E * Wz / l12
            m_kg = None if force_N is None else force_N / G
            results.append({
                **base,
                "delta_epsilon": de,
                "unknown_force_N": force_N,
                "unknown_mass_kg": m_kg,
                "Wz_mm3": Wz,
            })
        elif case == "cantilever_method2":
            m0 = to_float(row, "m0_kg")
            ex = to_float(row, "epsilon_max_x_micro")
            e0 = to_float(row, "epsilon_max_0_micro")
            mx = None if m0 is None or ex is None or e0 in (None, 0) else m0 * ex / e0
            results.append({**base, "unknown_mass_kg": mx})
        elif case == "photoelastic":
            fringe_order = to_float(row, "fringe_order")
            fringe_value = to_float(row, "material_fringe_value_N_per_mm")
            thickness = to_float(row, "thickness_mm")
            stress_diff = None
            if None not in (fringe_order, fringe_value, thickness) and thickness != 0:
                stress_diff = fringe_order * fringe_value / thickness
            results.append({
                **base,
                "demo_item": text_value(row, "demo_item"),
                "light_field": text_value(row, "light_field"),
                "fringe_order": fringe_order,
                "material_fringe_value_N_per_mm": fringe_value,
                "thickness_mm": thickness,
                "principal_stress_difference_MPa": stress_diff,
                "observation": text_value(row, "observation"),
                "expected": text_value(row, "expected"),
                "notes": text_value(row, "notes"),
            })
        elif case == "fatigue":
            runout_text = text_value(row, "runout")
            cycle_count = to_float(row, "cycle_count")
            results.append({
                **base,
                "demo_item": text_value(row, "demo_item"),
                "stress_MPa": to_float(row, "stress_MPa"),
                "stress_ratio": to_float(row, "stress_ratio"),
                "cycle_count": cycle_count,
                "log10_cycle_count": log10_positive(cycle_count),
                "runout": yes_value(runout_text),
                "observation": text_value(row, "observation"),
                "expected": text_value(row, "expected"),
                "fracture_feature": text_value(row, "fracture_feature"),
                "notes": text_value(row, "notes"),
            })

    fatigue_cycles = [
        r.get("cycle_count") for r in results
        if r.get("case") == "fatigue" and r.get("cycle_count") is not None
    ]
    deflection_count = sum(1 for r in results if r.get("case") == "deflection")
    reciprocity_diffs = [
        abs(r.get("delta_difference_mm")) for r in results
        if r.get("case") == "reciprocity" and r.get("delta_difference_mm") is not None
    ]
    unknown_mass_by_case = {
        r.get("case"): r.get("unknown_mass_kg") for r in results
        if r.get("case") in {"cantilever_method1", "cantilever_method2"}
        and r.get("unknown_mass_kg") is not None
    }
    fatigue_stress_life = [
        (r.get("stress_MPa"), r.get("cycle_count")) for r in results
        if r.get("case") == "fatigue"
        and r.get("stress_MPa") is not None
        and r.get("cycle_count") is not None
    ]
    fatigue_stress_life.sort(reverse=True)
    stress_life_trend_ok = all(
        fatigue_stress_life[i][1] <= fatigue_stress_life[i + 1][1]
        for i in range(len(fatigue_stress_life) - 1)
    ) if len(fatigue_stress_life) >= 2 else None
    photoelastic_items = {
        r.get("demo_item") for r in results if r.get("case") == "photoelastic"
    }
    summary = {
        "experiment": "梁变形及光弹、疲劳演示实验",
        "deflection_point_count": deflection_count,
        "deflection_point_requirement_ok": deflection_count >= 7,
        "photoelastic_record_count": sum(1 for r in results if r.get("case") == "photoelastic"),
        "photoelastic_required_items_present": (
            "pure_bending" in photoelastic_items
            and "ring_diametral_compression" in photoelastic_items
        ),
        "fatigue_record_count": sum(1 for r in results if r.get("case") == "fatigue"),
        "fatigue_runout_count": sum(1 for r in results if r.get("case") == "fatigue" and r.get("runout")),
        "fatigue_min_cycle_count": min(fatigue_cycles) if fatigue_cycles else None,
        "fatigue_max_cycle_count": max(fatigue_cycles) if fatigue_cycles else None,
        "fatigue_stress_life_trend_ok": stress_life_trend_ok,
        "max_reciprocity_delta_difference_abs_mm": max(reciprocity_diffs) if reciprocity_diffs else None,
        "reciprocity_delta_tolerance_ok": (
            max(reciprocity_diffs) <= 0.0100001 if reciprocity_diffs else None
        ),
        "unknown_mass_method_difference_kg": (
            abs(unknown_mass_by_case["cantilever_method1"]
                - unknown_mass_by_case["cantilever_method2"])
            if {"cantilever_method1", "cantilever_method2"} <= unknown_mass_by_case.keys()
            else None
        ),
        "mean_abs_deflection_error_pct": mean([
            abs(r["deflection_error_pct"]) for r in results
            if r.get("deflection_error_pct") is not None
        ]),
        "mean_abs_theta_error_pct": mean([
            abs(r["theta_error_pct"]) for r in results
            if r.get("theta_error_pct") is not None
        ]),
        "mean_unknown_mass_kg": mean([r.get("unknown_mass_kg") for r in results]),
        "mean_photoelastic_stress_difference_MPa": mean([
            r.get("principal_stress_difference_MPa") for r in results
        ]),
    }
    return results, summary


def main():
    parser = argparse.ArgumentParser(description="实验六：梁变形及光弹、疲劳演示实验")
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
