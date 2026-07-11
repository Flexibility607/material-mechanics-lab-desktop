import csv
import json
import math
from pathlib import Path


MISSING = {"", "na", "nan", "none", "null", "-"}


def to_float(row, *names, default=None):
    for name in names:
        if name not in row:
            continue
        value = row.get(name)
        if value is None:
            continue
        text = str(value).strip()
        if text.lower() in MISSING:
            continue
        text = text.replace(",", "")
        if text.endswith("%"):
            text = text[:-1]
        try:
            return float(text)
        except ValueError:
            continue
    return default


def text_value(row, *names, default=""):
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def microstrain(value):
    return None if value is None else value * 1e-6


def safe_div(a, b):
    if a is None or b in (None, 0):
        return None
    return a / b


def mean(values):
    vals = [v for v in values if v is not None and math.isfinite(v)]
    return sum(vals) / len(vals) if vals else None


def sample_std(values):
    vals = [v for v in values if v is not None and math.isfinite(v)]
    if len(vals) < 2:
        return None
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def relative_error_pct(exp_value, theory_value):
    if exp_value is None or theory_value in (None, 0):
        return None
    return (exp_value - theory_value) / theory_value * 100.0


def linear_regression(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys)
             if x is not None and y is not None and math.isfinite(x) and math.isfinite(y)]
    n = len(pairs)
    if n < 2:
        return {"n": n, "slope": None, "intercept": None, "r2": None}
    sx = sum(x for x, _ in pairs)
    sy = sum(y for _, y in pairs)
    mx = sx / n
    my = sy / n
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    if sxx == 0:
        return {"n": n, "slope": None, "intercept": None, "r2": None}
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    slope = sxy / sxx
    intercept = my - slope * mx
    ss_tot = sum((y - my) ** 2 for _, y in pairs)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in pairs)
    r2 = None if ss_tot == 0 else 1.0 - ss_res / ss_tot
    return {"n": n, "slope": slope, "intercept": intercept, "r2": r2}


def read_rows(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path, rows, fieldnames=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: format_value(row.get(k)) for k in fieldnames})


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_template(path, fieldnames, rows):
    write_rows(path, rows, fieldnames)


def format_value(value):
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.10g}"
    return value


def default_output(input_path, suffix="_result.csv"):
    p = Path(input_path)
    return p.with_name(p.stem + suffix)


def add_io_arguments(parser):
    parser.add_argument("input", nargs="?", help="输入 CSV 文件")
    parser.add_argument("--output", help="输出逐项结果 CSV")
    parser.add_argument("--summary", help="输出汇总 JSON")
    parser.add_argument("--template", help="生成输入 CSV 模板后退出")


def run_or_template(parser, args, fields, template_rows):
    if args.template:
        write_template(args.template, fields, template_rows)
        return True
    if not args.input:
        parser.error("需要提供输入 CSV，或使用 --template 生成模板")
    return False
