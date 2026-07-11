<!-- 由 material_mechanics_sample_data_processing_check.md 自动拆分。 -->

# 1. 电测法基本原理及贴片实验

程序：`exp01_strain_gauge_validation.py`

## 讲义要求核对与修正结论

| 讲义要求 | B011 当前覆盖情况 |
|---|---|
| 筛选应变片并测量初始电阻 | 已覆盖：输入 `resistance_before_ohm` |
| 接线后再次测量电阻，检查焊接与连接是否异常 | 已覆盖：输入 `resistance_after_ohm`，程序输出电阻差和变化率 |
| 预加载或清零后，分 2 到 3 级等增量加载 | 已覆盖：输入各级 `load_N`，程序检查增量级数和载荷增量离散度 |
| 记录每级载荷增量下的应变增量 | 已覆盖：输入 `strain_micro`，程序计算 `delta_strain_micro` |
| 若各级应变增量大致相等，则判断贴片有效 | 已修正补齐：程序输出应变增量离散度、线性拟合 \(R^2\) 和 `validity_judgement` |

因此，修正后的 B011 已包含讲义要求的数据处理与结论过程。需要注意的是，讲义没有给出“基本相等”的定量容差，程序采用载荷增量变异系数不超过 \(1\%\)、应变增量变异系数不超过 \(5\%\)、线性拟合 \(R^2\ge0.99\) 作为样例化判据；正式报告中仍应结合原始记录和实验现象说明。

## 基本原理

电阻应变片把构件表面沿应变片轴向的应变转换为电阻变化：

\[
\frac{\Delta R}{R}=K\varepsilon
\]

式中，\(R\) 为应变片电阻，\(\Delta R\) 为受力后的电阻改变量，\(K\) 为灵敏度系数，\(\varepsilon\) 为应变。应变仪用惠斯通电桥把微小电阻变化转换为电压变化，并按桥路加减关系显示等效应变。四臂等阻、等灵敏系数时，仪器等效读数可写为：

\[
\varepsilon_{\text{display}}
=\varepsilon_1-\varepsilon_2+\varepsilon_3-\varepsilon_4
\]

B011 的定量检验重点不是求材料常数，而是检查“贴片和接线是否可靠”：在等增量加载下，若各级应变增量基本相等，说明应变片能随试件表面稳定变形。

## 样例数据

| 级数 | 载荷 \(F\) / N | 应变 \(\varepsilon\) / \(\mu\varepsilon\) | 初始电阻 / \(\Omega\) | 接线后电阻 / \(\Omega\) |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 120.0 | 120.1 |
| 1 | 500 | 86 |  |  |
| 2 | 1000 | 171 |  |  |
| 3 | 1500 | 257 |  |  |

## 程序关键过程

程序逐行读取 `load_N`、`strain_micro`、`resistance_before_ohm` 和 `resistance_after_ohm`，完成以下处理：

1. 计算接线前后电阻差 \(\Delta R\) 及相对变化率，检查应变片筛选和焊接接线是否明显异常。
2. 计算相邻两级的 \(\Delta F_i\)、\(\Delta\varepsilon_i\) 和增量斜率 \(\Delta\varepsilon_i/\Delta F_i\)。
3. 对 \(\varepsilon-F\) 做线性回归，输出斜率、截距和 \(R^2\)。
4. 计算载荷增量和应变增量的离散程度，并给出贴片有效性判定。

## 数据处理关键过程

接线前后电阻检查：

\[
\Delta R=120.1-120.0=0.1\ \Omega
\]

\[
\frac{\Delta R}{R}\times100\%
=\frac{0.1}{120.0}\times100\%
=0.0833\%
\]

第 1 到第 3 级的载荷增量均为：

\[
\Delta F=500\text{ N}
\]

应变增量为：

\[
\Delta\varepsilon=86,\ 85,\ 86\ \mu\varepsilon
\]

平均应变增量和样本标准差为：

\[
\overline{\Delta\varepsilon}=85.667\ \mu\varepsilon,\qquad
s_{\Delta\varepsilon}=0.577\ \mu\varepsilon
\]

应变增量变异系数为：

\[
\frac{s_{\Delta\varepsilon}}{\overline{\Delta\varepsilon}}\times100\%
=0.674\%
\]

线性拟合结果：

\[
\varepsilon \approx 0.1712F+0.1000
\]

\[
R^2=0.999995
\]

## 程序输出核对

| 项目 | 结果 |
|---|---:|
| 加载增量段数 | 3 |
| 平均载荷增量 | 500 N |
| 载荷增量变异系数 | 0.000% |
| 平均应变增量 | 85.667 \(\mu\varepsilon\) |
| 应变增量标准差 | 0.577 \(\mu\varepsilon\) |
| 应变增量变异系数 | 0.674% |
| 最大应变增量相对偏离 | 0.778% |
| 拟合斜率 | 0.1712 \(\mu\varepsilon/\text{N}\) |
| 拟合 \(R^2\) | 0.999995 |
| 电阻变化率 | 0.0833% |
| 程序判定 | 贴片与接线有效性较好 |

结论：该样例按 3 级等增量加载，载荷增量完全一致，应变增量 \(86,85,86\ \mu\varepsilon\) 基本相等，\(\varepsilon-F\) 线性关系很好。因此可判定本次贴片与接线有效性较好，符合讲义要求的结论过程。
