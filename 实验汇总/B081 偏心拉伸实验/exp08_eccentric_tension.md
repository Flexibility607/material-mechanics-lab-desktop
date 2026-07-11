<!-- 由 material_mechanics_sample_data_processing_check.md 自动拆分。 -->

# 8. 偏心拉伸实验

程序：`exp08_eccentric_tension.py`

## 样例数据

载荷制度按讲义中的重复加载法：\(F_0=2\text{ kN}\)，\(F_{\max}=12\text{ kN}\)，\(\Delta F=10\text{ kN}\)，重复 \(N=4\) 次。课件 PDF 第 8 页给出的示例载荷为 \(F_0=5\text{ kN}\)、\(F_{\max}=15\text{ kN}\)，与讲义不同；本汇总按讲义口径处理。全桥读数用于求 \(\varepsilon_F\)，半桥读数用于求 \(\varepsilon_{M1}\)。

## 讲义要求核对

| 讲义要求 | 本文件/程序处理 |
|---|---|
| 分析单向偏心拉伸截面上的轴力与弯矩 | 用 \(\varepsilon_F\)、\(\varepsilon_{M1}\)、\(\varepsilon_{M2}\) 分解轴向拉伸与两个方向弯曲分量 |
| 用 \(1/4\) 桥测横截面最大正应变增量 | 输入 `epsilon_max_micro`；若未输入，则由 \(\Delta\varepsilon_F+\Delta\varepsilon_{M1}+\Delta\varepsilon_{M2}\) 合成 |
| 用全桥测 \(\varepsilon_F\)，求材料弹性模量 \(E\) | 全桥显示读数除以 2 得 \(\Delta\varepsilon_F\)，再用 \(E=\Delta F/(A\Delta\varepsilon_F)\) |
| 用半桥测弯曲应变，求圆孔偏心距 \(e\) | 半桥显示读数除以 2 得 \(\Delta\varepsilon_{M1}\)，再用 \(e=\Delta\varepsilon_{M1}EW_z/\Delta F\) |
| 重复加载后对几组数据取平均 | 对 4 次结果分别计算后输出平均 \(\bar{\varepsilon}_{\max}\)、\(\bar E\)、\(\overline{\Delta\sigma}_{\max}\)、\(\bar e\) |
| 给出最大正应力增量和结论 | 由 \(\Delta\sigma_{\max}=E\Delta\varepsilon_{\max}\) 计算，并在文末给出结论 |

| 次数 | \(F_0\) / kN | \(F_{\max}\) / kN | \(\Delta F\) / kN | \(1/4\)桥 \(\varepsilon_{\max}\) / \(\mu\varepsilon\) | 全桥读数 / \(\mu\varepsilon\) | 半桥 \(M_1\) 读数 / \(\mu\varepsilon\) | \(h\) / mm | \(b\) / mm |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 12 | 10 | 821 | 506 | 1136 | 24 | 8 |
| 2 | 2 | 12 | 10 | 823 | 504 | 1140 | 24 | 8 |
| 3 | 2 | 12 | 10 | 819 | 507 | 1134 | 24 | 8 |
| 4 | 2 | 12 | 10 | 822 | 505 | 1138 | 24 | 8 |

## 程序关键过程

程序先读取每次重复加载的 \(F_0,F_{\max},\Delta F\)，再由 \(h,b\) 计算 \(A,W_z\)。全桥读数除以 2 得到 \(\Delta\varepsilon_F\)，半桥读数除以 2 得到 \(\Delta\varepsilon_{M1}\)。若输入中给出 \(R_1,R_2\) 方向的第二弯曲分量，程序会继续加入 \(\Delta\varepsilon_{M2}\)；本样例未给出第二方向数据，故只处理 \(M_1\) 分量。

## 数据处理关键过程

\[
A=hb=24\times8=192\text{ mm}^2
\]

\[
W_z=\frac{hb^2}{6}
=\frac{24\times8^2}{6}
=256\text{ mm}^3
\]

第 1 次重复加载的桥路换算为：

\[
\Delta\varepsilon_F=\frac{506}{2}\times10^{-6}=253\times10^{-6}
\]

\[
\Delta\varepsilon_{M1}=\frac{1136}{2}\times10^{-6}=568\times10^{-6}
\]

\[
E_1=\frac{\Delta F}{A\Delta\varepsilon_F}
=\frac{10000}{192\times253\times10^{-6}}
=205862.9776\text{ MPa}
\]

\[
\Delta\sigma_{\max,1}=E_1\Delta\varepsilon_{\max,1}
=205862.9776\times821\times10^{-6}
=169.0135\text{ MPa}
\]

\[
e_1=\frac{\Delta\varepsilon_{M1}E_1W_z}{\Delta F}
=\frac{568\times10^{-6}\times205862.9776\times256}{10000}
=2.9934\text{ mm}
\]

4 次重复加载取平均：

\[
\bar{\varepsilon}_{\max}
=\frac{821+823+819+822}{4}\times10^{-6}
=0.00082125
\]

\[
\bar{\varepsilon}_F
=\frac{253+252+253.5+252.5}{4}\times10^{-6}
=0.00025275
\]

\[
\bar{\varepsilon}_{M1}
=\frac{568+570+567+569}{4}\times10^{-6}
=0.0005685
\]

\[
\bar{E}=206067.6088\text{ MPa},\qquad
\overline{\Delta\sigma}_{\max}=169.2337\text{ MPa},\qquad
\bar{e}=2.9990\text{ mm}
\]

## 程序输出核对

| 项目 | 结果 |
|---|---:|
| 重复次数 | 4 |
| \(\Delta F\) | 10 kN |
| \(A\) | 192 mm² |
| \(W_z\) | 256 mm³ |
| \(\bar{\varepsilon}_{\max}\) | 0.00082125 |
| \(\bar{\varepsilon}_F\) | 0.00025275 |
| \(\bar{\varepsilon}_{M1}\) | 0.0005685 |
| \(\bar{E}\) | 206067.6088 MPa |
| \(\overline{\Delta\sigma}_{\max}\) | 169.2337 MPa |
| \(\bar{e}\) | 2.9990 mm |

## 结论

本样例按讲义要求完成了偏心拉伸实验的全部数据处理：由 \(1/4\) 桥得到横截面最大正应变增量 \(\bar{\varepsilon}_{\max}=821.25\ \mu\varepsilon\)，由全桥轴向应变得到材料弹性模量 \(\bar E=206.07\text{ GPa}\)，由半桥弯曲应变得到圆孔偏心距 \(\bar e=2.999\text{ mm}\)。进一步计算最大正应力增量为 \(\overline{\Delta\sigma}_{\max}=169.23\text{ MPa}\)，小于中碳钢名义屈服极限 \(360\text{ MPa}\)，样例加载处于弹性范围，计算 \(E\) 与 \(e\) 的前提成立。
