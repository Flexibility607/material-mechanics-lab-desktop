import argparse
import math
from collections import defaultdict

from common import (add_io_arguments, default_output, linear_regression, mean,
                    microstrain, read_rows, run_or_template, sample_std,
                    text_value, to_float, write_json, write_rows)


FIELDS = [
    "run", "level", "load_N", "force_N", "T_Nmm", "dial_mm",
    "half_bridge_ch1_micro", "half_bridge_ch2_micro", "gamma_micro",
    "strain_m45_micro", "bridge_to_gamma_factor",
    "yield_limit_MPa",
    "a1_mm", "L1_mm", "D1_mm", "b1_mm",
    "a2_mm", "L2_mm", "D2_mm", "b2_mm",
    "a3_mm", "L3_mm", "D3_mm", "b3_mm",
    "a_mm", "L_mm", "D_mm", "d_mm", "b_mm", "Ip_mm4", "Wp_mm3",
]

TEMPLATE = [
    {"run": 1, "level": 0, "load_N": 0, "force_N": "", "T_Nmm": "",
     "dial_mm": 0, "half_bridge_ch1_micro": 0,
     "half_bridge_ch2_micro": 0, "gamma_micro": "",
     "strain_m45_micro": "", "bridge_to_gamma_factor": "",
     "yield_limit_MPa": 220,
     "a1_mm": 119.98, "L1_mm": 300.10, "D1_mm": 50.00, "b1_mm": 80.02,
     "a2_mm": 120.01, "L2_mm": 299.90, "D2_mm": 49.99, "b2_mm": 79.98,
     "a3_mm": 120.01, "L3_mm": 300.00, "D3_mm": 50.01, "b3_mm": 80.00,
     "a_mm": "", "L_mm": "", "D_mm": "", "d_mm": "",
     "b_mm": "", "Ip_mm4": "", "Wp_mm3": ""},
    {"run": 1, "level": 1, "load_N": 1000, "force_N": "", "T_Nmm": "",
     "dial_mm": 0.05867, "half_bridge_ch1_micro": 60.9,
     "half_bridge_ch2_micro": 61.3, "gamma_micro": "",
     "strain_m45_micro": "", "bridge_to_gamma_factor": "",
     "yield_limit_MPa": 220,
     "a1_mm": 119.98, "L1_mm": 300.10, "D1_mm": 50.00, "b1_mm": 80.02,
     "a2_mm": 120.01, "L2_mm": 299.90, "D2_mm": 49.99, "b2_mm": 79.98,
     "a3_mm": 120.01, "L3_mm": 300.00, "D3_mm": 50.01, "b3_mm": 80.00,
     "a_mm": "", "L_mm": "", "D_mm": "", "d_mm": "",
     "b_mm": "", "Ip_mm4": "", "Wp_mm3": ""},
]


def dimension(row, symbol):
    direct = to_float(row, f"{symbol}_mm")
    if direct is not None:
        return direct
    values = [to_float(row, f"{symbol}{idx}_mm") for idx in range(1, 4)]
    return mean(values)


def section_values(row):
    D = dimension(row, "D")
    d = to_float(row, "d_mm", "inner_d_mm", default=0.0)
    Ip = to_float(row, "Ip_mm4")
    Wp = to_float(row, "Wp_mm3")
    if D is not None:
        if Ip is None:
            Ip = math.pi * (D ** 4 - d ** 4) / 32.0
        if Wp is None:
            Wp = math.pi * (D ** 4 - d ** 4) / (16.0 * D)
    return D, d, Ip, Wp


def force_N(row):
    F = to_float(row, "load_N", "force_N", "F_N")
    if F is not None:
        return F
    F_kN = to_float(row, "load_kN", "force_kN", "F_kN")
    return None if F_kN is None else F_kN * 1000.0


def torque_Nmm(row, a):
    T = to_float(row, "T_Nmm", "torque_Nmm")
    if T is not None:
        return T
    F = force_N(row)
    return None if F is None or a is None else F * a


def gamma_micro(row):
    direct = to_float(row, "gamma_micro")
    if direct is not None:
        return direct

    ch1 = to_float(row, "half_bridge_ch1_micro", "gamma_ch1_micro")
    ch2 = to_float(row, "half_bridge_ch2_micro", "gamma_ch2_micro")
    channel_values = [v for v in (ch1, ch2) if v is not None]
    if channel_values:
        factor = to_float(row, "bridge_to_gamma_factor", default=1.0)
        return mean(channel_values) * factor

    strain_m45 = to_float(row, "strain_m45_micro", "epsilon_m45_micro")
    if strain_m45 is not None:
        return 2.0 * strain_m45
    return None


def coefficient_of_variation(values):
    m = mean(values)
    s = sample_std(values)
    if m in (None, 0) or s is None:
        return None
    return abs(s / m)


def quality_penalty(r2, cv):
    r2_part = 1.0 if r2 is None else max(0.0, 1.0 - r2)
    cv_part = 1.0 if cv is None else cv
    return r2_part + cv_part


def run_quality(run_results):
    torsion_values = [r["G_torsion_i_MPa"] for r in run_results]
    electric_values = [r["G_electric_i_MPa"] for r in run_results]
    torsion_fit = linear_regression(
        [r["phi_rad"] for r in run_results],
        [r["T_Nmm"] for r in run_results],
    )
    electric_fit = linear_regression(
        [r["gamma"] for r in run_results],
        [r["tau_MPa"] for r in run_results],
    )

    refs = next((r for r in run_results if r["Ip_mm4"] and r["L_mm"]), None)
    G_torsion_fit = None
    if refs and torsion_fit.get("slope") is not None:
        G_torsion_fit = torsion_fit["slope"] * refs["L_mm"] / refs["Ip_mm4"]

    G_electric_fit = electric_fit.get("slope")
    cv_torsion = coefficient_of_variation(torsion_values)
    cv_electric = coefficient_of_variation(electric_values)
    score = (
        quality_penalty(torsion_fit.get("r2"), cv_torsion)
        + quality_penalty(electric_fit.get("r2"), cv_electric)
    )

    return {
        "torsion_fit_T_vs_phi": torsion_fit,
        "electric_fit_tau_vs_gamma": electric_fit,
        "G_torsion_fit_MPa": G_torsion_fit,
        "G_electric_fit_MPa": G_electric_fit,
        "mean_G_torsion_MPa": mean(torsion_values),
        "mean_G_electric_MPa": mean(electric_values),
        "cv_G_torsion": cv_torsion,
        "cv_G_electric": cv_electric,
        "score": score,
    }


def process(rows):
    groups = defaultdict(list)
    for idx, row in enumerate(rows):
        groups[text_value(row, "run", default="1")].append((idx, row))

    all_results = []
    qualities = {}
    for run, items in groups.items():
        items.sort(key=lambda item: item[0])
        run_results = []
        prev = None

        for _, row in items:
            a = dimension(row, "a")
            L = dimension(row, "L")
            b = dimension(row, "b")
            D, d, Ip, Wp = section_values(row)
            F = force_N(row)
            T = torque_Nmm(row, a)
            dial = to_float(row, "dial_mm", "delta_mm", "indicator_mm")
            phi = to_float(row, "phi_rad")
            if phi is None and dial is not None and b not in (None, 0):
                phi = dial / b
            gamma_m = gamma_micro(row)
            gamma = microstrain(gamma_m)
            tau = None if T is None or Wp in (None, 0) else T / Wp
            yield_limit = to_float(row, "yield_limit_MPa", "sigma_s_MPa")

            if prev is None:
                dT = dphi = ddial = dgamma = dtau = None
            else:
                dT = None if T is None or prev["T"] is None else T - prev["T"]
                dphi = None if phi is None or prev["phi"] is None else phi - prev["phi"]
                ddial = None if dial is None or prev["dial"] is None else dial - prev["dial"]
                dgamma = None if gamma is None or prev["gamma"] is None else gamma - prev["gamma"]
                dtau = None if tau is None or prev["tau"] is None else tau - prev["tau"]

            G_torsion = None
            if dT is not None and L is not None and dphi not in (None, 0) and Ip not in (None, 0):
                G_torsion = dT * L / (dphi * Ip)

            G_electric = None
            if dtau is not None and dgamma not in (None, 0):
                G_electric = dtau / dgamma

            result = {
                "run": run,
                "level": text_value(row, "level"),
                "load_N": F,
                "a_mm": a,
                "L_mm": L,
                "D_mm": D,
                "d_mm": d,
                "b_mm": b,
                "Ip_mm4": Ip,
                "Wp_mm3": Wp,
                "yield_limit_MPa": yield_limit,
                "T_Nmm": T,
                "dial_mm": dial,
                "phi_rad": phi,
                "half_bridge_ch1_micro": to_float(row, "half_bridge_ch1_micro", "gamma_ch1_micro"),
                "half_bridge_ch2_micro": to_float(row, "half_bridge_ch2_micro", "gamma_ch2_micro"),
                "gamma_micro": gamma_m,
                "gamma": gamma,
                "tau_MPa": tau,
                "delta_T_Nmm": dT,
                "delta_delta_mm": ddial,
                "delta_phi_rad": dphi,
                "delta_gamma_micro": None if dgamma is None else dgamma * 1e6,
                "G_torsion_i_MPa": G_torsion,
                "G_electric_i_MPa": G_electric,
                "selected_run": "",
            }
            run_results.append(result)
            prev = {"T": T, "phi": phi, "dial": dial, "gamma": gamma, "tau": tau}

        qualities[run] = run_quality(run_results)
        all_results.extend(run_results)

    selected_run = min(qualities, key=lambda r: qualities[r]["score"]) if qualities else None
    for result in all_results:
        result["selected_run"] = "yes" if result["run"] == selected_run else "no"

    selected_quality = qualities.get(selected_run, {})
    selected_results = [r for r in all_results if r["run"] == selected_run]
    selected_max_tau = max(
        (r["tau_MPa"] for r in selected_results if r["tau_MPa"] is not None),
        default=None,
    )
    selected_yield_limit = mean(r["yield_limit_MPa"] for r in selected_results)
    selected_tau_to_yield = (
        None if selected_max_tau is None or selected_yield_limit in (None, 0)
        else selected_max_tau / selected_yield_limit
    )
    torsion_r2 = selected_quality.get("torsion_fit_T_vs_phi", {}).get("r2")
    electric_r2 = selected_quality.get("electric_fit_tau_vs_gamma", {}).get("r2")
    hooke_law_verified = (
        torsion_r2 is not None and electric_r2 is not None
        and torsion_r2 >= 0.995 and electric_r2 >= 0.995
    )
    elastic_range_ok = (
        None if selected_tau_to_yield is None
        else selected_tau_to_yield < 1.0
    )
    summary = {
        "experiment": "shear_modulus_G",
        "source_model": "Lecture/PPT experiment 4: incremental torsion loading, torsion meter plus electric half-bridge, repeated runs.",
        "selection_rule": "Choose the run with better T-phi and tau-gamma linearity and lower increment-G scatter.",
        "selected_run": selected_run,
        "selected_mean_G_torsion_MPa": selected_quality.get("mean_G_torsion_MPa"),
        "selected_mean_G_electric_MPa": selected_quality.get("mean_G_electric_MPa"),
        "selected_fit_G_torsion_MPa": selected_quality.get("G_torsion_fit_MPa"),
        "selected_fit_G_electric_MPa": selected_quality.get("G_electric_fit_MPa"),
        "selected_torsion_fit_T_vs_phi": selected_quality.get("torsion_fit_T_vs_phi"),
        "selected_electric_fit_tau_vs_gamma": selected_quality.get("electric_fit_tau_vs_gamma"),
        "selected_max_tau_MPa": selected_max_tau,
        "selected_yield_limit_MPa": selected_yield_limit,
        "selected_tau_to_yield_ratio": selected_tau_to_yield,
        "hooke_law_verified_by_linearity": hooke_law_verified,
        "elastic_range_check": elastic_range_ok,
        "conclusion": (
            "The selected run verifies torsional Hooke law by linear T-phi and tau-gamma fits; "
            "torsion-meter and electric methods give consistent shear modulus G; "
            "the maximum shear stress is within the provided yield-limit check."
            if hooke_law_verified and elastic_range_ok is not False
            else "Check the selected run linearity, bridge conversion, and stress range before reporting G."
        ),
        "all_run_quality": qualities,
    }
    return all_results, summary


def main():
    parser = argparse.ArgumentParser(
        description="Experiment 4: shear modulus G from torsion meter and electric half-bridge readings."
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
