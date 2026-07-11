import argparse

from common import (add_io_arguments, default_output, linear_regression, mean,
                    read_rows, relative_error_pct, run_or_template, sample_std,
                    text_value, to_float, write_json, write_rows)


LOAD_INCREMENT_CV_LIMIT_PCT = 1.0
STRAIN_INCREMENT_CV_LIMIT_PCT = 5.0
MIN_FIT_R2 = 0.99

FIELDS = [
    "step", "load_N", "strain_micro",
    "resistance_before_ohm", "resistance_after_ohm"
]

TEMPLATE = [
    {"step": 0, "load_N": 0, "strain_micro": 0,
     "resistance_before_ohm": 120.1, "resistance_after_ohm": 120.2},
    {"step": 1, "load_N": 500, "strain_micro": 85,
     "resistance_before_ohm": "", "resistance_after_ohm": ""},
    {"step": 2, "load_N": 1000, "strain_micro": 171,
     "resistance_before_ohm": "", "resistance_after_ohm": ""},
    {"step": 3, "load_N": 1500, "strain_micro": 256,
     "resistance_before_ohm": "", "resistance_after_ohm": ""},
]


def coefficient_of_variation_pct(values):
    avg = mean(values)
    std = sample_std(values)
    if avg in (None, 0) or std is None:
        return None
    return abs(std / avg) * 100.0


def max_deviation_from_mean_pct(values):
    vals = [v for v in values if v is not None]
    avg = mean(vals)
    if avg in (None, 0):
        return None
    return max(abs(v - avg) for v in vals) / abs(avg) * 100.0


def within_limit(value, limit):
    if value is None:
        return None
    return value <= limit


def process(rows):
    data = []
    for i, row in enumerate(rows):
        data.append({
            "row": i + 1,
            "step": text_value(row, "step", default=str(i)),
            "load_N": to_float(row, "load_N", "F_N"),
            "strain_micro": to_float(row, "strain_micro", "epsilon_micro"),
            "resistance_before_ohm": to_float(row, "resistance_before_ohm", "R_before_ohm"),
            "resistance_after_ohm": to_float(row, "resistance_after_ohm", "R_after_ohm"),
        })

    results = []
    for i, row in enumerate(data):
        prev = data[i - 1] if i > 0 else None
        d_load = None if prev is None else row["load_N"] - prev["load_N"]
        d_strain = None if prev is None else row["strain_micro"] - prev["strain_micro"]
        slope = None if d_load in (None, 0) or d_strain is None else d_strain / d_load
        r_before = row["resistance_before_ohm"]
        r_after = row["resistance_after_ohm"]
        r_change_pct = relative_error_pct(r_after, r_before)
        results.append({
            **row,
            "delta_load_N": d_load,
            "delta_strain_micro": d_strain,
            "increment_slope_micro_per_N": slope,
            "resistance_delta_ohm": None if r_before is None or r_after is None else r_after - r_before,
            "resistance_change_pct": r_change_pct,
        })

    fit = linear_regression(
        [r["load_N"] for r in results],
        [r["strain_micro"] for r in results],
    )
    d_loads = [r["delta_load_N"] for r in results[1:]]
    d_strains = [r["delta_strain_micro"] for r in results[1:]]
    resistance_changes = [abs(r["resistance_delta_ohm"]) for r in results
                          if r["resistance_delta_ohm"] is not None]
    resistance_change_pcts = [abs(r["resistance_change_pct"]) for r in results
                              if r["resistance_change_pct"] is not None]
    load_increment_cv_pct = coefficient_of_variation_pct(d_loads)
    strain_increment_cv_pct = coefficient_of_variation_pct(d_strains)
    max_strain_increment_deviation_pct = max_deviation_from_mean_pct(d_strains)
    load_equal_increment_ok = within_limit(
        load_increment_cv_pct, LOAD_INCREMENT_CV_LIMIT_PCT
    )
    strain_increment_stable_ok = within_limit(
        strain_increment_cv_pct, STRAIN_INCREMENT_CV_LIMIT_PCT
    )
    linearity_ok = None if fit["r2"] is None else fit["r2"] >= MIN_FIT_R2
    increment_count_in_lecture_range = 2 <= len(d_strains) <= 3
    validity_ok = all(x is True for x in [
        load_equal_increment_ok,
        strain_increment_stable_ok,
        linearity_ok,
        increment_count_in_lecture_range,
    ])
    validity_judgement = "贴片与接线有效性较好" if validity_ok else "需复查贴片、接线或加载数据"
    summary = {
        "experiment": "电测法基本原理及贴片实验",
        "lecture_required_checks": [
            "筛选应变片并测量初始电阻",
            "接线后再次测量电阻以检查焊接和连接是否异常",
            "预加载或清零后进行 2 到 3 级等增量加载",
            "计算各级载荷增量和应变增量",
            "以各级应变增量是否大致相等判断贴片有效性",
        ],
        "increment_count": len(d_strains),
        "increment_count_in_lecture_range": increment_count_in_lecture_range,
        "linear_fit_strain_micro_vs_load_N": fit,
        "mean_delta_load_N": mean(d_loads),
        "std_delta_load_N": sample_std(d_loads),
        "load_increment_cv_pct": load_increment_cv_pct,
        "mean_delta_strain_micro": mean(d_strains),
        "std_delta_strain_micro": sample_std(d_strains),
        "strain_increment_cv_pct": strain_increment_cv_pct,
        "max_strain_increment_deviation_pct": max_strain_increment_deviation_pct,
        "resistance_check": {
            "available_count": len(resistance_changes),
            "max_abs_resistance_delta_ohm": max(resistance_changes) if resistance_changes else None,
            "max_abs_resistance_change_pct": max(resistance_change_pcts) if resistance_change_pcts else None,
            "purpose": "两次电阻测量用于筛选应变片并检查焊接、接线是否明显异常。",
        },
        "judgement_criteria": {
            "load_increment_cv_pct_limit": LOAD_INCREMENT_CV_LIMIT_PCT,
            "strain_increment_cv_pct_limit": STRAIN_INCREMENT_CV_LIMIT_PCT,
            "min_linear_fit_r2": MIN_FIT_R2,
            "note": "讲义未给出定量容差；上述阈值作为程序化参考，最终应结合原始记录和实验现象判断。",
        },
        "load_equal_increment_ok": load_equal_increment_ok,
        "strain_increment_stable_ok": strain_increment_stable_ok,
        "linearity_ok": linearity_ok,
        "validity_judgement": validity_judgement,
        "conclusion": (
            "载荷按等增量施加，应变增量离散较小，载荷-应变关系近似线性，"
            "可判为贴片与接线有效性较好。"
            if validity_ok else
            "载荷等增量、应变增量稳定性或线性拟合未同时满足参考判据，需要复查贴片、接线或加载读数。"
        ),
    }
    return results, summary


def main():
    parser = argparse.ArgumentParser(description="实验一：贴片有效性与载荷-应变线性检查")
    add_io_arguments(parser)
    args = parser.parse_args()
    if run_or_template(parser, args, FIELDS, TEMPLATE):
        return
    rows = read_rows(args.input)
    results, summary = process(rows)
    write_rows(args.output or default_output(args.input), results)
    if args.summary:
        write_json(args.summary, summary)


if __name__ == "__main__":
    main()
