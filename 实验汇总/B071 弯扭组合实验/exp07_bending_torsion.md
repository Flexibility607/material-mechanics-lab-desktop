<!-- 由 B071 弯扭组合实验讲义与课件核对后修正。 -->

# 7. 弯扭组合试验

程序：`exp07_bending_torsion.py`

## 讲义要求核对

| 讲义要求 | 当前处理情况 |
|---|---|
| 采用重复加载法，参考 \(F_0=500\text{ N}\)、\(F_{\max}=1500\text{ N}\)、\(\Delta F=1000\text{ N}\)、\(n=4\) | 已在输入表中记录载荷制度，并按测点分组统计 4 次重复读数的平均值和标准差 |
| 试件尺寸测量三次，取平均值作为实验值 | 已支持 `D_mm/d_mm/wall_thickness_mm` 多行取平均，也支持 `D1_mm`~`D3_mm`、`d1_mm`~`d3_mm`、`wall_thickness1_mm`~`wall_thickness3_mm` |
| 用 \(0^\circ,\pm45^\circ\) 应变花求主应力大小和主平面方位角 | 已计算 \(\varepsilon_x,\varepsilon_y,\gamma_{xy}\)、\(\varepsilon_1,\varepsilon_2\)、\(\sigma_1,\sigma_2\) 和主方向角 |
| 计算贴片截面的弯矩 \(M\) | 已按半桥读数 \(2\varepsilon_0\) 折算，并由 \(M=EW_z\varepsilon_0\) 计算 |
| 计算贴片截面的扭矩 \(T\) | 已按桥路读数 \(2\gamma_{xy}\) 折算，并由 \(T=\frac{E}{2(1+\mu)}W_p\gamma_{xy}\) 计算 |
| 与理论值比较并分析误差 | 已支持由理论值直接输入，或由 \(\Delta F\) 与力臂自动计算理论 \(M,T\)，并输出 \(M,T,\sigma_1,\sigma_2\)、主方向角误差 |

结论：修正后，B071 已包括讲义要求的全部数据处理和结论过程。实际使用时只需把样例数据替换为实测数据，并按实验装置符号约定填写弯矩、扭矩力臂正负号。

## 样例数据

样例按讲义取 \(F_0=500\text{ N}\)，\(F_{\max}=1500\text{ N}\)，\(\Delta F=1000\text{ N}\)，重复 4 次。样例只列 A 截面上表面一个测点。试件外径与壁厚按 4 次记录取平均，结果为 \(D=42.00\text{ mm}\)、\(t=3.00\text{ mm}\)，故 \(d=36.00\text{ mm}\)。

课件给出形成扭矩的力臂 \(l_1=200\text{ mm}\)、形成弯矩的力臂 \(l_2=240\text{ mm}\)。样例按 \(\gamma_{xy}=\varepsilon_{-45^\circ}-\varepsilon_{45^\circ}\) 的符号约定取 \(T_{\text{th}}=-\Delta F l_1\)。

| 次数 | \(D\) / mm | \(t\) / mm | \(\varepsilon_0\) | \(\varepsilon_{45^\circ}\) | \(\varepsilon_{-45^\circ}\) | 弯矩半桥显示值 | 扭矩桥路显示值 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 42.02 | 3.01 | 348 | 311 | -61 | 696 | -744 |
| 2 | 42.00 | 3.00 | 350 | 313 | -59 | 700 | -746 |
| 3 | 41.98 | 2.99 | 347 | 310 | -62 | 694 | -742 |
| 4 | 42.00 | 3.00 | 349 | 312 | -60 | 698 | -744 |

材料参数按讲义取 \(E=206000\text{ MPa}\)，\(\mu=0.28\)。

## 程序关键过程

程序先按 `load_case + point + surface` 分组，对重复加载读数求平均和标准差。

应变花采用：

\[
\varepsilon_x=\varepsilon_0
\]

\[
\varepsilon_y=\varepsilon_{45^\circ}+\varepsilon_{-45^\circ}-\varepsilon_0
\]

\[
\gamma_{xy}=\varepsilon_{-45^\circ}-\varepsilon_{45^\circ}
\]

主应变和主方向角：

\[
\varepsilon_{1,2}=\frac{\varepsilon_x+\varepsilon_y}{2}
\pm
\sqrt{\left(\frac{\varepsilon_x-\varepsilon_y}{2}\right)^2+
\left(\frac{\gamma_{xy}}{2}\right)^2}
\]

\[
\tan 2\alpha_0=-\frac{\gamma_{xy}}{\varepsilon_x-\varepsilon_y}
\]

平面应力下主应力：

\[
\sigma_1=\frac{E}{1-\mu^2}\left(\varepsilon_1+\mu\varepsilon_2\right),\qquad
\sigma_2=\frac{E}{1-\mu^2}\left(\varepsilon_2+\mu\varepsilon_1\right)
\]

空心圆轴截面系数：

\[
W_z=\frac{\pi D^3}{32}\left[1-\left(\frac{d}{D}\right)^4\right],\qquad
W_p=\frac{\pi D^3}{16}\left[1-\left(\frac{d}{D}\right)^4\right]
\]

弯矩半桥读数为 \(2\varepsilon_0\)，计算前除以 2：

\[
M=EW_z\varepsilon_0
\]

扭矩桥路读数为 \(2\gamma_{xy}\)，计算前除以 2：

\[
T=\frac{E}{2(1+\mu)}W_p\gamma_{xy}
\]

理论值可直接输入 `M_theory_Nmm/T_theory_Nmm`，也可输入 `bending_arm_mm/torsion_arm_mm`，程序自动按 \(\Delta F l\) 计算。

## 数据处理关键过程

\[
\bar{\varepsilon}_0=\frac{348+350+347+349}{4}=348.5\ \mu\varepsilon
\]

\[
\bar{\varepsilon}_{45^\circ}=311.5\ \mu\varepsilon,\qquad
\bar{\varepsilon}_{-45^\circ}=-60.5\ \mu\varepsilon
\]

弯矩半桥显示值平均为：

\[
\bar{\varepsilon}_{M,\text{display}}=697.0\ \mu\varepsilon,\qquad
\varepsilon_{0,M}=\frac{697.0}{2}=348.5\ \mu\varepsilon
\]

扭矩桥路显示值平均为：

\[
\bar{\varepsilon}_{T,\text{display}}=-744.0\ \mu\varepsilon,\qquad
\gamma_{xy,T}=\frac{-744.0}{2}=-372.0\ \mu\varepsilon
\]

\[
\varepsilon_x=348.5\times10^{-6}=0.0003485
\]

\[
\varepsilon_y=(311.5-60.5-348.5)\times10^{-6}=-0.0000975
\]

\[
\gamma_{xy}=(-60.5-311.5)\times10^{-6}=-0.000372
\]

截面系数：

\[
W_z=3347.4792\text{ mm}^3,\qquad
W_p=6694.9583\text{ mm}^3
\]

弯矩：

\[
M=206000\times3347.4792\times0.0003485
=240318.8772\text{ N·mm}
\]

扭矩：

\[
T=\frac{206000}{2(1+0.28)}\times6694.9583\times(-0.000372)
=-200409.3937\text{ N·mm}
\]

理论对比：

\[
M_{\text{th}}=\Delta F l_2=1000\times240=240000\text{ N·mm}
\]

\[
T_{\text{th}}=-\Delta F l_1=-1000\times200=-200000\text{ N·mm}
\]

\[
\sigma_{x,\text{th}}=\frac{M_{\text{th}}}{W_z}=71.6957\text{ MPa},\qquad
\tau_{xy,\text{th}}=\frac{T_{\text{th}}}{W_p}=-29.8732\text{ MPa}
\]

由理论 \(\sigma_x,\tau_{xy}\) 得：

\[
\sigma_{1,\text{th}}=82.5113\text{ MPa},\qquad
\sigma_{2,\text{th}}=-10.8156\text{ MPa},\qquad
\alpha_{\text{th}}=19.9028^\circ
\]

## 程序输出核对

| 项目 | 结果 |
|---|---:|
| 重复次数 | 4 |
| \(\bar{\varepsilon}_0\) | 348.5 \(\mu\varepsilon\) |
| 半桥等效 \(\varepsilon_0\) | 348.5 \(\mu\varepsilon\) |
| 扭矩桥路等效 \(\gamma_{xy}\) | -372.0 \(\mu\varepsilon\) |
| \(\varepsilon_x\) | 0.0003485 |
| \(\varepsilon_y\) | -0.0000975 |
| \(\gamma_{xy}\) | -0.000372 |
| \(\varepsilon_1\) | 0.000415888 |
| \(\varepsilon_2\) | -0.000164888 |
| 主方向角 | 19.9154° |
| \(\sigma_1\) | 82.6412 MPa |
| \(\sigma_2\) | -10.8273 MPa |
| \(M_{\text{exp}}\) | 240318.8772 N·mm |
| \(M\) 误差 | 0.1329% |
| \(T_{\text{exp}}\) | -200409.3937 N·mm |
| \(T\) 误差 | 0.2047% |
| \(\sigma_1\) 误差 | 0.1574% |
| \(\sigma_2\) 误差 | 0.1084% |
| 主方向角误差 | 0.0126° |

## 结论与误差分析

1. 由应变花计算得到测点处 \(\sigma_1=82.6412\text{ MPa}\)、\(\sigma_2=-10.8273\text{ MPa}\)，主方向角 \(\alpha=19.9154^\circ\)。与按名义尺寸和理论内力计算的结果相比，主应力和主方向角误差很小，说明应变花换算过程完整。
2. 由半桥读数折算得到 \(M_{\text{exp}}=240318.8772\text{ N·mm}\)，与 \(M_{\text{th}}=240000\text{ N·mm}\) 的相对误差为 0.1329%，弯矩测量结果合理。
3. 由扭矩桥路读数折算得到 \(T_{\text{exp}}=-200409.3937\text{ N·mm}\)，与 \(T_{\text{th}}=-200000\text{ N·mm}\) 的相对误差为 0.2047%，扭矩测量结果合理。
4. 主要误差来源包括应变片粘贴角度偏差、桥路接线和温度补偿误差、力臂和截面尺寸测量误差、试件装夹偏心以及读数稳定性。报告中应结合实测误差大小判断装置安装和数据是否可靠。
