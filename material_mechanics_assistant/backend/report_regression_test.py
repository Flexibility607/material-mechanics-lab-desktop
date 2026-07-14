from __future__ import annotations

import copy
import difflib
import json
import re
from pathlib import Path

from server import (
    AUTO_REPORT_EXPERIMENTS,
    AUTO_REPORT_SAMPLE,
    REPORT_SOURCE_ROOT,
    abbreviate_raw_record_pages,
    calculate_auto_report,
    load_auto_report_module,
    replace_report_metadata,
)


VALIDATION_ROOT = Path(__file__).resolve().parents[1] / "validation"
GENERATED_ROOT = VALIDATION_ROOT / "generated_reports"


def headings(text: str) -> list[str]:
    return re.findall(r"^#{1,6}\s+.*$", text, flags=re.MULTILINE)


def image_urls(text: str) -> set[str]:
    return set(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text))


def comparison_text(text: str) -> str:
    text = re.sub(r"data:image/svg\+xml;base64,[A-Za-z0-9+/=]+", "<embedded-svg-chart>", text)
    text = re.sub(
        r"(?:验证胡克定律：|### 3\. 正应力—正应变关系与胡克定律验证).*?(?=^## 六、实验结论)",
        "<elastic-hooke-section>\n\n",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )
    text = re.sub(
        r"^## 六、实验数据记录与处理.*?(?=^## 七、实验结论)",
        "<shear-processing-section>\n\n",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )
    return re.sub(
        r"^## 五、实验数据记录与处理.*?(?=^## 六、实验结论)",
        "<beam-processing-section>\n\n",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )


MUTATIONS = {
    "B021": (["tension", 0, "yield_force_kN"], 24.62),
    "B031": (["width_mm", 0], 24.43),
    "B041": (["dial_run", "dial_mm", 4], 0.325),
    "B051": (["full_bridge", "readings_micro", 0], -623),
    "B061": (["cantilever", "strain_readings_micro", 0, 0], 150),
    "B071": (["rosettes", "lower", "measurement_points", 1, "readings_micro", 0], -627),
    "B081": (["full_bridge_2epsilon_F_micro", 0], 774),
}


def set_nested(root, path: list, value) -> None:
    target = root
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def core_headings(text: str) -> list[str]:
    appendix = re.search(r"^## 附：", text, flags=re.MULTILINE)
    return headings(text if appendix is None else text[:appendix.start()])


def fixed_text_checks(exp: dict, source: str, generated: str) -> tuple[bool, str]:
    if exp["id"] == "B061":
        simple_start = source.index("## 五、实验结果处理")
        cantilever_start = source.index("# 悬臂梁实验", simple_start)
        cantilever_data_start = source.index("## 五、实验数据处理", cantilever_start)
        thought_start = source.index("## 七、思考题", cantilever_data_start)
        prefix_ok = generated.startswith(source[:simple_start].rstrip())
        middle_ok = source[cantilever_start:cantilever_data_start].rstrip() in generated
        suffix_ok = generated.endswith(source[thought_start:].lstrip())
        return prefix_ok and middle_ok and suffix_ok, f"前段={prefix_ok}，中段={middle_ok}，后段={suffix_ok}"

    data_heading = "## 六、实验数据记录与处理" if exp["id"] == "B041" else "## 五、"
    data_start = source.index(data_heading)
    thought = re.search(r"^## [七八]、思考题", source[data_start:], flags=re.MULTILINE)
    if thought is None:
        return False, "未找到思考题边界"
    thought_start = data_start + thought.start()
    prefix_ok = generated.startswith(source[:data_start].rstrip())
    suffix_ok = generated.endswith(source[thought_start:].lstrip())
    return prefix_ok and suffix_ok, f"前段={prefix_ok}，后段={suffix_ok}"


def get_numeric_checks(results: dict) -> list[dict]:
    mp = results["mechanical_properties"]
    ec = results["elastic_constants"]
    sm = results["shear_modulus"]
    bb = results["beam_bending"]
    bd = results["beam_deformation"]
    bt = results["bending_torsion"]
    et = results["eccentric_tension"]
    return [
        {"exp": "B021", "item": "低碳钢屈服强度/MPa", "scan": 312.20, "calc": mp["tension"][0]["yield_strength_MPa"], "tol": 0.02},
        {"exp": "B021", "item": "低碳钢抗拉强度/MPa", "scan": 448.82, "calc": mp["tension"][0]["tensile_strength_MPa"], "tol": 0.02},
        {"exp": "B021", "item": "低碳钢延伸率/%", "scan": 30.73, "calc": mp["tension"][0]["elongation_pct"], "tol": 0.01},
        {"exp": "B021", "item": "低碳钢断面收缩率/%", "scan": 62.42, "calc": mp["tension"][0]["area_reduction_pct"], "tol": 0.02},
        {"exp": "B021", "item": "铸铁压缩强度/MPa", "scan": 573.47, "calc": mp["compression"][1]["compressive_strength_MPa"], "tol": 0.10},
        {"exp": "B031", "item": "弹性模量/GPa", "scan": 68.06, "calc": ec["E_mean_MPa"] / 1000.0, "tol": 0.01},
        {"exp": "B031", "item": "泊松比", "scan": 0.3263, "calc": ec["mu_mean"], "tol": 0.0002},
        {"exp": "B041", "item": "扭角仪切变模量/GPa", "scan": 27.727, "calc": sm["dial_method"]["G_report_MPa"] / 1000.0, "tol": 0.002},
        {"exp": "B041", "item": "半桥切变模量/GPa", "scan": 26.427, "calc": sm["half_bridge_method"]["G_report_MPa"] / 1000.0, "tol": 0.010},
        {"exp": "B051", "item": "全桥最大正应变/με", "scan": -156.0, "calc": bb["full_bridge"]["max_strain_micro"], "tol": 0.1},
        {"exp": "B061", "item": "跨中理论挠度/mm", "scan": 0.5572, "calc": bd["simply_supported"]["deflection_theoretical_mm"], "tol": 0.001},
        {"exp": "B061", "item": "悬臂梁质量/kg", "scan": 0.715, "calc": bd["cantilever"]["mass_kg"], "tol": 0.005},
        {"exp": "B071", "item": "上表面主应力1/MPa", "scan": 53.318, "calc": bt["surface_results"][0]["experimental"]["sigma_1_MPa"], "tol": 0.02},
        {"exp": "B071", "item": "下表面主应力1/MPa", "scan": 3.5799, "calc": bt["surface_results"][1]["experimental"]["sigma_1_MPa"], "tol": 0.02, "policy": "corrected"},
        {"exp": "B071", "item": "下表面主应力2/MPa", "scan": -54.658, "calc": bt["surface_results"][1]["experimental"]["sigma_2_MPa"], "tol": 0.02, "policy": "corrected"},
        {"exp": "B081", "item": "弹性模量/GPa", "scan": 194.301, "calc": et["E_MPa"] / 1000.0, "tol": 0.01},
        {"exp": "B081", "item": "偏心距/mm", "scan": 19.665, "calc": et["eccentricity_mm"], "tol": 0.01},
    ]


def main() -> None:
    sample = json.loads(AUTO_REPORT_SAMPLE.read_text(encoding="utf-8"))
    steel_tension = sample["experiments"]["mechanical_properties"]["tension"][0]
    steel_compression = sample["experiments"]["mechanical_properties"]["compression"][0]
    if steel_tension["l1_mm"][2] != 130.97 or steel_compression["d1_mm"] != 17.70:
        raise AssertionError("B021 第 5 页复核值未同步到扫描算例")
    metadata = sample.get("metadata", {})
    module = load_auto_report_module()
    all_results = module.calculate_all(sample)["results"]
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)

    rows = []
    mutation_rows = []
    for exp in AUTO_REPORT_EXPERIMENTS:
        payload = calculate_auto_report(exp["id"], sample["experiments"][exp["key"]], metadata)
        generated = payload["report_markdown"]
        correction_ok = True
        if exp["id"] == "B071":
            lower = payload["result"]["surface_results"][1]["experimental"]
            correction_ok = (
                f"{lower['sigma_1_MPa']:.4f}" in generated
                and f"{lower['sigma_2_MPa']:.4f}" in generated
                and "3.5799" not in generated
                and "-54.658" not in generated
            )
        source = replace_report_metadata(
            (REPORT_SOURCE_ROOT / exp["report_file"]).read_text(encoding="utf-8"),
            metadata,
        ).replace("](images/", "](/report-images/")
        source = abbreviate_raw_record_pages(source)
        fixed_ok, fixed_detail = fixed_text_checks(exp, source, generated)
        source_images = image_urls(source)
        generated_images = image_urls(generated)
        image_ok = source_images <= generated_images
        source_headings = set(headings(source))
        heading_coverage = len(source_headings & set(headings(generated))) / max(len(source_headings), 1)
        similarity = difflib.SequenceMatcher(
            None, comparison_text(source), comparison_text(generated)
        ).ratio()
        near_scan = similarity >= 0.95
        essential_ok = all(text in generated for text in ("实验目的", "实验结论", "思考题"))
        export_path = GENERATED_ROOT / f"{exp['id']}-{exp['title']}.md"
        export_path.write_text(generated, encoding="utf-8")
        rows.append({
            "id": exp["id"],
            "title": exp["title"],
            "fixed_ok": fixed_ok,
            "fixed_detail": fixed_detail,
            "image_ok": image_ok,
            "images": f"{len(generated_images & source_images)}/{len(source_images)}",
            "heading_coverage": heading_coverage,
            "similarity": similarity,
            "near_scan": near_scan,
            "essential_ok": essential_ok,
            "correction_ok": correction_ok,
            "chars": len(generated),
            "export": export_path.name,
        })

        mutated_data = copy.deepcopy(sample["experiments"][exp["key"]])
        mutation_path, mutation_value = MUTATIONS[exp["id"]]
        set_nested(mutated_data, mutation_path, mutation_value)
        mutated = calculate_auto_report(exp["id"], mutated_data, metadata)["report_markdown"]
        mutation_rows.append({
            "id": exp["id"],
            "changed": mutated != generated,
            "headings": set(core_headings(source)) <= set(core_headings(mutated)),
            "images": source_images <= image_urls(mutated),
            "no_scan_appendix": (
                "<details>" not in mutated
                and not re.search(r"/report-images/[^)]+/page-\d+\.png", mutated)
            ),
            "essential": all(text in mutated for text in ("实验目的", "实验结论", "思考题")),
        })

    numeric = get_numeric_checks(all_results)
    for item in numeric:
        item["difference"] = item["calc"] - item["scan"]
        item["status"] = "一致" if abs(item["difference"]) <= item["tol"] else (
            "程序修正手算" if item.get("policy") == "corrected" else "超差"
        )

    report_lines = [
        "# 七次实验自动报告与扫描件回归检查",
        "",
        "> 检查基准：03-实验报告/markdown 是逐页图像识别并人工补齐后的扫描件对照稿。内置算例采用扫描件对应原始数据，要求标题与原图 100% 覆盖、全文相似度不低于 95%；仅允许身份信息替换和已确认手算错误的程序校正。",
        "",
        "## 1. 结构、原图和可导出性",
        "",
        "| 实验 | 固定正文 | 原图覆盖 | 标题覆盖 | 全文相似度 | 近似扫描件 | 必要章节 | Markdown 导出 |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for row in rows:
        report_lines.append(
            f"| {row['id']} {row['title']} | {'通过' if row['fixed_ok'] else '失败'} | "
            f"{row['images']} | {row['heading_coverage']:.1%} | {row['similarity']:.1%} | "
            f"{'通过' if row['near_scan'] else '失败'} | {'通过' if row['essential_ok'] else '失败'} | {row['export']} |"
        )

    report_lines += [
        "",
        "说明：固定正文包括实验目的、设备、原理、数据处理说明、结论和思考题；七份扫描算例生成稿均已写入 generated_reports/，可直接在应用中再次生成并导出。",
        "",
        "## 2. 关键数值复核",
        "",
        "| 实验 | 项目 | 扫描稿 | 程序值 | 差值 | 判定 |",
        "|---|---|---:|---:|---:|---|",
    ]
    for item in numeric:
        report_lines.append(
            f"| {item['exp']} | {item['item']} | {item['scan']:.6g} | {item['calc']:.6g} | "
            f"{item['difference']:+.6g} | {item['status']} |"
        )

    report_lines += [
        "",
        "## 3. 已确认的扫描稿手算差异",
        "",
        "- B021 第 5 页原图复核：低碳钢断后标距第三次为 130.97 mm，低碳钢压缩后直径为 17.70 mm；已修正早期 OCR 的 130.87 mm 和 11.70 mm。",
        "- B071 下表面主应力：程序按三向应变花变换与平面应力本构完整重算，得到约 6.021 MPa 和 −52.198 MPa；扫描稿中的 3.5799 MPa 和 −54.658 MPa 属于手算/抄录差异。生成报告采用程序复核值。",
        "- B021 铸铁压缩：扫描稿用断后直径 11.62 mm 计算 573.47 MPa；算例保留这一报告口径，同时在生成报告中明确给出按初始截面积复核的结果，避免误解。",
        "- B041 扭转：报告按扫描稿采用五级逐差法给出主结果，不再附加相邻加载级的复核值。",
        "",
        "## 4. 单字段扰动检查",
        "",
        "| 实验 | 结果随输入变化 | 核心标题不变 | 原图完整 | 无旧扫描附录 | 必要章节 |",
        "|---|---|---|---|---|---|",
    ]
    for row in mutation_rows:
        report_lines.append(
            f"| {row['id']} | {'通过' if row['changed'] else '失败'} | "
            f"{'通过' if row['headings'] else '失败'} | {'通过' if row['images'] else '失败'} | "
            f"{'通过' if row['no_scan_appendix'] else '失败'} | {'通过' if row['essential'] else '失败'} |"
        )

    report_lines += [
        "",
        "## 5. 总体判定",
        "",
    ]
    structural_pass = all(
        row["fixed_ok"] and row["image_ok"] and row["essential_ok"]
        and row["heading_coverage"] == 1.0 and row["near_scan"] and row["correction_ok"]
        for row in rows
    )
    numeric_pass = all(item["status"] != "超差" for item in numeric)
    mutation_pass = all(all(value for key, value in row.items() if key != "id") for row in mutation_rows)
    report_lines.append(f"- 结构与扫描原图：{'通过' if structural_pass else '未通过'}。")
    report_lines.append(f"- 关键数值：{'通过' if numeric_pass else '未通过'}（明确列出的手算修正不视为程序故障）。")
    report_lines.append(f"- 单字段扰动：{'通过' if mutation_pass else '未通过'}。")
    report_lines.append(
        f"- 回归结论：{'七次算例均可生成可导出的完整报告。' if structural_pass and numeric_pass and mutation_pass else '仍有项目需要修正。'}"
    )

    output = VALIDATION_ROOT / "report_scan_comparison.md"
    output.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    if not structural_pass or not numeric_pass or not mutation_pass:
        raise AssertionError(f"回归检查未通过，详见 {output}")
    print(f"PASS reports={len(rows)} numeric_checks={len(numeric)}")
    print(output)


if __name__ == "__main__":
    main()
