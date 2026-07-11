import argparse
import math

from common import (add_io_arguments, default_output, mean, read_rows,
                    run_or_template, text_value, to_float, write_json,
                    write_rows)


FIELDS = [
    "group", "material", "specimen", "A0_mm2", "d0_mm", "d1_mm",
    "l0_mm", "l1_mm", "AB_mm", "BC_mm", "BCp_mm", "Fp_N", "Fs_N",
    "Fb_N", "h0_mm", "Ts_Nmm", "Tb_Nmm", "Wp_mm3", "theta_rad",
    "observation",
]

TEMPLATE = [
    {"group": "tension", "material": "low_carbon_steel", "specimen": "",
     "A0_mm2": "", "d0_mm": 10.0, "d1_mm": 6.6,
     "l0_mm": 100, "l1_mm": 126, "AB_mm": "", "BC_mm": "",
     "BCp_mm": "", "Fp_N": 18000, "Fs_N": 24000, "Fb_N": 36000,
     "h0_mm": "", "Ts_Nmm": "", "Tb_Nmm": "", "Wp_mm3": "",
     "theta_rad": "", "observation": "线性、屈服、强化、缩颈，杯状断口"},
    {"group": "tension", "material": "cast_iron", "specimen": "",
     "A0_mm2": "", "d0_mm": 10.0, "d1_mm": "",
     "l0_mm": 100, "l1_mm": "", "AB_mm": "", "BC_mm": "",
     "BCp_mm": "", "Fp_N": "", "Fs_N": "", "Fb_N": 16000,
     "h0_mm": "", "Ts_Nmm": "", "Tb_Nmm": "", "Wp_mm3": "",
     "theta_rad": "", "observation": "变形小，无屈服和缩颈，断口近垂直轴线"},
    {"group": "compression", "material": "low_carbon_steel",
     "specimen": "", "A0_mm2": "", "d0_mm": 15.0, "d1_mm": "",
     "l0_mm": "", "l1_mm": "", "AB_mm": "", "BC_mm": "",
     "BCp_mm": "", "Fp_N": "", "Fs_N": 56000, "Fb_N": "",
     "h0_mm": 30, "Ts_Nmm": "", "Tb_Nmm": "", "Wp_mm3": "",
     "theta_rad": "", "observation": "明显屈服，越压越扁，呈腰鼓形"},
    {"group": "compression", "material": "cast_iron",
     "specimen": "", "A0_mm2": "", "d0_mm": 15.0, "d1_mm": "",
     "l0_mm": "", "l1_mm": "", "AB_mm": "", "BC_mm": "",
     "BCp_mm": "", "Fp_N": "", "Fs_N": "", "Fb_N": 145000,
     "h0_mm": 30, "Ts_Nmm": "", "Tb_Nmm": "", "Wp_mm3": "",
     "theta_rad": "", "observation": "无明显屈服，断口与轴线约成55度"},
    {"group": "torsion", "material": "low_carbon_steel", "specimen": "",
     "A0_mm2": "", "d0_mm": 10.0, "d1_mm": "", "l0_mm": 50,
     "l1_mm": "", "AB_mm": "", "BC_mm": "", "BCp_mm": "",
     "Fp_N": "", "Fs_N": "", "Fb_N": "", "h0_mm": "",
     "Ts_Nmm": 95000, "Tb_Nmm": 155000, "Wp_mm3": "",
     "theta_rad": "", "observation": "先线性后屈服，最终沿垂直轴线截面剪断"},
    {"group": "torsion", "material": "cast_iron", "specimen": "",
     "A0_mm2": "", "d0_mm": 10.0, "d1_mm": "", "l0_mm": 50,
     "l1_mm": "", "AB_mm": "", "BC_mm": "", "BCp_mm": "",
     "Fp_N": "", "Fs_N": "", "Fb_N": "", "h0_mm": "",
     "Ts_Nmm": "", "Tb_Nmm": 72000, "Wp_mm3": "",
     "theta_rad": "", "observation": "变形小，沿约45度螺旋面断裂"},
]

OUTPUT_FIELDS = [
    "group", "group_label", "material", "A0_mm2", "A1_mm2",
    "Wp_mm3", "l1_used_mm", "tension_sigma_p_MPa",
    "tension_sigma_s_MPa", "tension_sigma_b_MPa",
    "elongation_delta_pct", "area_reduction_psi_pct",
    "compression_sigma_s_MPa", "compression_sigma_b_MPa",
    "torsion_tau_s_MPa", "torsion_tau_b_MPa", "observation",
    "conclusion", "note",
]

GROUP_LABELS = {
    "tension": "拉伸",
    "compression": "压缩",
    "torsion": "扭转",
}

EXPECTED_ITEMS = [
    ("tension", "low_carbon_steel", "低碳钢拉伸"),
    ("tension", "cast_iron", "铸铁拉伸"),
    ("compression", "low_carbon_steel", "低碳钢压缩"),
    ("compression", "cast_iron", "铸铁压缩"),
    ("torsion", "low_carbon_steel", "低碳钢扭转"),
    ("torsion", "cast_iron", "铸铁扭转"),
]

CONCLUSIONS = {
    ("tension", "low_carbon_steel"): (
        "低碳钢拉伸呈线性、屈服、强化和缩颈阶段；由屈服强度、"
        "强度极限、延伸率和断面收缩率评价强度与塑性。"
    ),
    ("tension", "cast_iron"): (
        "铸铁拉伸变形小，无明显屈服和缩颈，断口近似垂直于轴线，"
        "破坏主要由最大拉应力导致。"
    ),
    ("compression", "low_carbon_steel"): (
        "低碳钢压缩可出现明显屈服，随后越压越扁并呈腰鼓形，"
        "通常不以断裂载荷作为强度指标。"
    ),
    ("compression", "cast_iron"): (
        "铸铁压缩无明显屈服，压缩强度明显高于拉伸强度，"
        "断口常与轴线约成55度，破坏与切应力及端面摩擦有关。"
    ),
    ("torsion", "low_carbon_steel"): (
        "低碳钢扭转先满足扭转胡克定律，随后屈服并强化，"
        "最终多沿垂直于轴线的截面剪断，破坏主要由切应力导致。"
    ),
    ("torsion", "cast_iron"): (
        "铸铁扭转变形小，常沿约45度螺旋面断裂，"
        "破坏主要由最大拉应力导致。"
    ),
}


def area_from_diameter(d_mm):
    return None if d_mm is None else math.pi * d_mm ** 2 / 4.0


def polar_section_modulus_solid(d_mm):
    return None if d_mm is None else math.pi * d_mm ** 3 / 16.0


def normalized_group(row):
    raw = text_value(row, "group", "test_type", "loading", default="")
    if not raw:
        return "tension"
    value = raw.strip().lower()
    if value in {"tension", "tensile", "拉伸", "轴向拉伸"}:
        return "tension"
    if value in {"compression", "compressive", "压缩", "轴向压缩"}:
        return "compression"
    if value in {"torsion", "twist", "扭转"}:
        return "torsion"
    return value


def material_kind(material):
    value = str(material).strip().lower().replace(" ", "_").replace("-", "_")
    if value in {"low_carbon_steel", "mild_steel", "低碳钢"}:
        return "low_carbon_steel"
    if value in {"cast_iron", "铸铁"}:
        return "cast_iron"
    return value


def observation_text(row):
    return text_value(row, "observation", "phenomenon", "fracture_observation", default="")


def conclusion_for(row, group, material):
    entered = text_value(row, "conclusion", "result_conclusion", default="")
    if entered:
        return entered
    conclusion = CONCLUSIONS.get((group, material_kind(material)), "")
    observation = observation_text(row)
    if observation and conclusion:
        return f"观察：{observation}；结论：{conclusion}"
    return conclusion or observation


def first_not_none(*values):
    for value in values:
        if value is not None:
            return value
    return None


def force_n(row, *bases):
    for base in bases:
        value = to_float(row, f"{base}_N", base)
        if value is not None:
            return value
        value = to_float(row, f"{base}_kN")
        if value is not None:
            return value * 1000.0
    return None


def torque_nmm(row, *bases):
    for base in bases:
        value = to_float(row, f"{base}_Nmm", f"{base}_N_mm", base)
        if value is not None:
            return value
        value = to_float(row, f"{base}_Nm", f"{base}_N_m")
        if value is not None:
            return value * 1000.0
    return None


def common_geometry(row):
    d0 = to_float(row, "d0_mm", "diameter_mm")
    d1 = to_float(row, "d1_mm", "neck_d_mm", "fracture_d_mm")
    A0 = to_float(row, "A0_mm2", "A0")
    A1 = to_float(row, "A1_mm2", "A1")
    Wp = to_float(row, "Wp_mm3", "W_p_mm3")
    if A0 is None:
        A0 = area_from_diameter(d0)
    if A1 is None:
        A1 = area_from_diameter(d1)
    if Wp is None:
        Wp = polar_section_modulus_solid(d0)
    return d0, d1, A0, A1, Wp


def fracture_gauge_length(row):
    l1 = to_float(row, "l1_mm", "L1_mm")
    if l1 is not None:
        return l1

    AB = to_float(row, "AB_mm")
    BC = to_float(row, "BC_mm")
    BCp = to_float(row, "BCp_mm", "BC_prime_mm", "BC'_mm")
    if AB is None or BC is None:
        return None
    return AB + 2 * BC if BCp is None else AB + BC + BCp


def stress_from_force(force, area):
    if force is None or area in (None, 0):
        return None
    return force / area


def shear_from_torque(torque, section_modulus):
    if torque is None or section_modulus in (None, 0):
        return None
    return torque / section_modulus


def process_tension(row, material, A0, A1, Wp):
    l0 = to_float(row, "l0_mm", "L0_mm")
    l1 = fracture_gauge_length(row)
    Fp = force_n(row, "Fp", "F_p")
    Fs = force_n(row, "Fs", "F_s")
    Fb = force_n(row, "Fb", "F_b", "Fmax", "F_max")

    elongation = None if l0 in (None, 0) or l1 is None else (l1 - l0) / l0 * 100.0
    reduction = None if A0 in (None, 0) or A1 is None else (A0 - A1) / A0 * 100.0
    if material_kind(material) == "cast_iron":
        note = "铸铁拉伸以观察脆性断裂为主；若记录断裂载荷，可计算拉伸强度。"
    else:
        note = "若断口偏离标距中段，l1_used_mm 按 AB+2BC 或 AB+BC+BCp 得到。"

    return {
        "group": "tension",
        "group_label": GROUP_LABELS["tension"],
        "material": material,
        "A0_mm2": A0,
        "A1_mm2": A1,
        "Wp_mm3": "",
        "l1_used_mm": l1,
        "tension_sigma_p_MPa": stress_from_force(Fp, A0),
        "tension_sigma_s_MPa": stress_from_force(Fs, A0),
        "tension_sigma_b_MPa": stress_from_force(Fb, A0),
        "elongation_delta_pct": elongation,
        "area_reduction_psi_pct": reduction,
        "compression_sigma_s_MPa": "",
        "compression_sigma_b_MPa": "",
        "torsion_tau_s_MPa": "",
        "torsion_tau_b_MPa": "",
        "observation": observation_text(row),
        "conclusion": conclusion_for(row, "tension", material),
        "note": note,
    }


def process_compression(row, material, A0, A1, Wp):
    Fs = force_n(row, "Fsc", "Fs", "F_s", "Fc_yield")
    Fb = force_n(row, "Fbc", "Fb", "F_b", "Fcmax", "F_max")
    if material_kind(material) == "cast_iron":
        note = "铸铁压缩通常记录破坏或最大载荷。"
    else:
        note = "低碳钢压缩通常记录屈服载荷，破坏载荷可留空。"
    return {
        "group": "compression",
        "group_label": GROUP_LABELS["compression"],
        "material": material,
        "A0_mm2": A0,
        "A1_mm2": "",
        "Wp_mm3": "",
        "l1_used_mm": "",
        "tension_sigma_p_MPa": "",
        "tension_sigma_s_MPa": "",
        "tension_sigma_b_MPa": "",
        "elongation_delta_pct": "",
        "area_reduction_psi_pct": "",
        "compression_sigma_s_MPa": stress_from_force(Fs, A0),
        "compression_sigma_b_MPa": stress_from_force(Fb, A0),
        "torsion_tau_s_MPa": "",
        "torsion_tau_b_MPa": "",
        "observation": observation_text(row),
        "conclusion": conclusion_for(row, "compression", material),
        "note": note,
    }


def process_torsion(row, material, A0, A1, Wp):
    Ts = torque_nmm(row, "Ts", "T_s")
    Tb = torque_nmm(row, "Tb", "T_b", "Tmax", "T_max")
    if material_kind(material) == "cast_iron":
        note = "铸铁扭转通常由破坏扭矩计算扭转强度，并结合螺旋断口说明破坏原因。"
    else:
        note = "低碳钢扭转可由屈服扭矩和最大扭矩计算扭转屈服强度与扭转强度。"
    return {
        "group": "torsion",
        "group_label": GROUP_LABELS["torsion"],
        "material": material,
        "A0_mm2": A0,
        "A1_mm2": "",
        "Wp_mm3": Wp,
        "l1_used_mm": "",
        "tension_sigma_p_MPa": "",
        "tension_sigma_s_MPa": "",
        "tension_sigma_b_MPa": "",
        "elongation_delta_pct": "",
        "area_reduction_psi_pct": "",
        "compression_sigma_s_MPa": "",
        "compression_sigma_b_MPa": "",
        "torsion_tau_s_MPa": shear_from_torque(Ts, Wp),
        "torsion_tau_b_MPa": shear_from_torque(Tb, Wp),
        "observation": observation_text(row),
        "conclusion": conclusion_for(row, "torsion", material),
        "note": note,
    }


def missing_coverage(results):
    covered = {(row["group"], material_kind(row["material"])) for row in results}
    return [
        label for group, material, label in EXPECTED_ITEMS
        if (group, material) not in covered
    ]


def process(rows):
    results = []
    for row in rows:
        group = normalized_group(row)
        material = text_value(row, "material", "specimen", default="")
        _, _, A0, A1, Wp = common_geometry(row)

        if group == "compression":
            results.append(process_compression(row, material, A0, A1, Wp))
        elif group == "torsion":
            results.append(process_torsion(row, material, A0, A1, Wp))
        else:
            results.append(process_tension(row, material, A0, A1, Wp))

    counts = {}
    for row in results:
        counts[row["group"]] = counts.get(row["group"], 0) + 1

    missing = missing_coverage(results)
    summary = {
        "experiment": "材料在轴向拉伸、压缩和扭转时的力学性能",
        "rows": len(results),
        "counts_by_group": counts,
        "expected_coverage": [label for _, _, label in EXPECTED_ITEMS],
        "missing_required_items": missing,
        "coverage_complete": not missing,
        "mean_tension_sigma_s_MPa": mean([to_float(r, "tension_sigma_s_MPa") for r in results]),
        "mean_compression_sigma_s_MPa": mean([to_float(r, "compression_sigma_s_MPa") for r in results]),
        "mean_torsion_tau_s_MPa": mean([to_float(r, "torsion_tau_s_MPa") for r in results]),
        "formula": (
            "低碳钢拉伸: sigma=F/A0, delta=(l1-l0)/l0*100%, "
            "psi=(A0-A1)/A0*100%; 铸铁拉伸: 若记录Fb则sigma_b=Fb/A0; "
            "压缩: sigma=F/A0; 扭转: tau=T/Wp, Wp=pi*d0^3/16"
        ),
        "conclusion_requirement": (
            "除定量指标外，应记录铸铁拉伸、低碳钢/铸铁压缩、"
            "低碳钢/铸铁扭转的曲线特征、变形现象、断口形态和破坏原因。"
        ),
    }
    return results, summary


def main():
    parser = argparse.ArgumentParser(
        description="实验二：材料在轴向拉伸、压缩和扭转时的力学性能计算"
    )
    add_io_arguments(parser)
    args = parser.parse_args()
    if run_or_template(parser, args, FIELDS, TEMPLATE):
        return
    results, summary = process(read_rows(args.input))
    write_rows(args.output or default_output(args.input), results, OUTPUT_FIELDS)
    if args.summary:
        write_json(args.summary, summary)


if __name__ == "__main__":
    main()
