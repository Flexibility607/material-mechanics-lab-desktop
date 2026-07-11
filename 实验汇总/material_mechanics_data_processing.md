# 材料力学八次实验数据处理梳理

## 实验清单

根据 `01-实验讲义/01-2025材料力学A实验讲义.doc` 与 `02-实验课件` 中 B011 到 B081 的课件，八次实验为：

| 序号 | 实验名称 | 主要数据处理程序 |
|---|---|---|
| 1 | 电测法基本原理及贴片实验 | `B011 应变片粘贴实验/exp01_strain_gauge_validation.py` |
| 2 | 材料在轴向拉伸、压缩和扭转时的力学性能 | `B021 材料在轴向拉伸、压缩和扭转时的力学性能/exp02_tensile_properties.py` |
| 3 | 测弹性常数实验：材料弹性常数 \(E,\mu\) 的测定 | `B031 材料弹性常数E、μ的测定/exp03_elastic_constants.py` |
| 4 | 切变模量 \(G\) 的测定 | `B041 材料切变模量G的测定/exp04_shear_modulus.py` |
| 5 | 直梁弯曲实验 | `B051 直梁弯曲实验/exp05_beam_bending.py` |
| 6 | 梁变形及光弹、疲劳演示实验 | `B061 梁变形及光弹、疲劳演示实验/exp06_beam_deformation.py` |
| 7 | 弯扭组合试验 | `B071 弯扭组合实验/exp07_bending_torsion.py` |
| 8 | 偏心拉伸实验 | `B081 偏心拉伸实验/exp08_eccentric_tension.py` |

运行方式统一为：

```bash
python "B011 应变片粘贴实验/exp01_strain_gauge_validation.py" --template exp01_template.csv
python "B011 应变片粘贴实验/exp01_strain_gauge_validation.py" exp01_data.csv --output exp01_result.csv --summary exp01_summary.json
```

其他程序同理。各脚本均支持 `--template` 生成输入 CSV 模板。

## 1. 电测法基本原理及贴片实验

本实验主要检查应变片粘贴与接线是否可靠。数据处理重点不是求材料常数，而是判断接线前后电阻是否异常，以及等增量加载时各级应变增量是否大致相等。

基本关系为：

\[
\frac{\Delta R}{R}=K\varepsilon
\]

式中，\(K\) 为应变片灵敏度系数。应变仪采用惠斯通电桥测量微小电阻变化；四臂等阻、等灵敏系数时，等效显示应变满足桥路加减关系：

\[
\varepsilon_{\text{display}}
=\varepsilon_1-\varepsilon_2+\varepsilon_3-\varepsilon_4
\]

处理步骤：

1. 用万用表记录应变片筛选时的初始电阻，以及接线后的电阻，检查应变片、焊点和导线连接是否明显异常。
2. 试件预加载后清零，按 2 到 3 级等增量加载，记录载荷 \(F\) 与应变仪读数 \(\varepsilon\)。
3. 计算相邻级差值：

   \[
   \Delta F_i=F_i-F_{i-1},\qquad
   \Delta\varepsilon_i=\varepsilon_i-\varepsilon_{i-1}
   \]

4. 对 \(F-\varepsilon\) 做线性拟合，给出斜率、截距和 \(R^2\)。
5. 统计载荷增量和应变增量的平均值、标准差、变异系数，并据此给出程序化参考判定。
6. 若各级 \(\Delta F_i\) 近似相等且 \(\Delta\varepsilon_i\) 也近似相等，说明贴片有效性较好。

脚本输出：每级增量、增量斜率、接线前后电阻差、电阻变化率、增量离散程度、线性拟合结果、讲义要求核对项和 `validity_judgement`。讲义没有规定“基本相等”的定量容差，脚本默认以载荷增量变异系数不超过 \(1\%\)、应变增量变异系数不超过 \(5\%\)、线性拟合 \(R^2\ge0.99\) 作为参考阈值，正式结论仍应结合原始记录与实验现象判断。

## 2. 材料在轴向拉伸、压缩和扭转时的力学性能

讲义中实验二的完整内容为材料在轴向拉伸、压缩和扭转时的力学性能。讲义“实验目的”要求覆盖低碳钢拉伸、铸铁拉伸、低碳钢和铸铁压缩、低碳钢和铸铁扭转；“实验结果处理”明确给出低碳钢拉伸的定量处理，并要求结合各工况的曲线、变形和断口形态说明破坏原因。因此本实验按“定量计算 + 观察结论”两条线处理：拉伸组计算强度与塑性指标，压缩组由载荷和原截面积换算压缩应力，扭转组由扭矩和抗扭截面系数换算切应力，同时输出各材料的现象观察和结论。

### 2.1 拉伸组

先由试样原始直径和断后最小直径计算截面积：

\[
A_0=\frac{\pi d_0^2}{4},\qquad A_1=\frac{\pi d_1^2}{4}
\]

低碳钢拉伸试验的数据处理以试验机自动给出的特征载荷为基础，求比例极限、屈服极限、强度极限、延伸率和断面收缩率：

\[
\sigma_p=\frac{F_p}{A_0},\qquad
\sigma_s=\frac{F_s}{A_0},\qquad
\sigma_b=\frac{F_b}{A_0}
\]

\[
\delta=\frac{l_1-l_0}{l_0}\times100\%,\qquad
\psi=\frac{A_0-A_1}{A_0}\times100\%
\]

若断口不在标距中段，需要断口移中：

\[
l_1=AB+2BC
\]

或：

\[
l_1=AB+BC+BC'
\]

铸铁拉伸主要用于观察脆性断裂现象。若记录了断裂载荷或最大载荷 \(F_b\)，则可补充计算：

\[
\sigma_b=\frac{F_b}{A_0}
\]

结论中应说明铸铁拉伸变形小，无明显屈服和缩颈，断口近似垂直于试样轴线，破坏主要由最大拉应力导致。

### 2.2 压缩组

压缩试件为圆柱形试件，原截面积仍按 \(A_0=\pi d_0^2/4\) 计算。低碳钢压缩时通常记录明显屈服对应的载荷，铸铁压缩时通常记录破坏或最大载荷：

\[
\sigma_{sc}=\frac{F_{sc}}{A_0},\qquad
\sigma_{bc}=\frac{F_{bc}}{A_0}
\]

式中，\(F_{sc}\) 为压缩屈服载荷，\(F_{bc}\) 为压缩破坏或最大载荷。若某种材料没有断裂载荷，例如低碳钢被压成腰鼓形而不破坏，则该项可留空。

结论中应分别写明：低碳钢压缩有屈服并最终呈腰鼓形，通常不发生断裂；铸铁压缩无明显屈服，压缩强度明显高于拉伸强度，断口常与轴线约成 \(55^\circ\)，破坏与切应力及端面摩擦有关。

### 2.3 扭转组

扭转试验记录扭矩-转角曲线 \(T-\theta\)，并观察断口形态。圆截面实心试样的抗扭截面系数为：

\[
W_p=\frac{\pi d_0^3}{16}
\]

低碳钢可由屈服扭矩、最大扭矩求扭转屈服强度和扭转强度；铸铁通常由破坏扭矩求扭转强度：

\[
\tau_s=\frac{T_s}{W_p},\qquad
\tau_b=\frac{T_b}{W_p}
\]

式中，\(T_s,T_b\) 的单位用 \(\text{N}\cdot\text{mm}\)，则 \(\tau\) 的单位为 \(\text{MPa}\)。

结论中应分别写明：低碳钢扭转先满足扭转胡克定律，随后屈服、强化，最终多沿垂直于轴线的截面剪断，破坏主要由切应力导致；铸铁扭转变形小，常沿约 \(45^\circ\) 螺旋面断裂，破坏主要由最大拉应力导致。

脚本输出：拉伸组的 \(\sigma_p,\sigma_s,\sigma_b,\delta,\psi\)，压缩组的 \(\sigma_{sc},\sigma_{bc}\)，扭转组的 \(\tau_s,\tau_b\)，由直径换算得到的 \(A_0,A_1,W_p\)，以及各工况的 `observation`、`conclusion`、`note`。样例汇总中 `coverage_complete=true`，表示低碳钢拉伸、铸铁拉伸、低碳钢压缩、铸铁压缩、低碳钢扭转、铸铁扭转六项均已覆盖。

## 3. 测弹性常数实验：材料弹性常数 \(E,\mu\) 的测定

本实验对应课件 `3-B031--测弹性常数--（2020.5）.pdf` 与讲义“实验三 材料弹性常数 \(E,\mu\) 的测定”。试件为 7075 铝合金矩形截面试件，名义尺寸 \(b\times t=(24\times8)\text{ mm}^2\)。讲义要求在标距两端及中间三处测量厚度和宽度，并将三处横截面面积的算术平均值作为原始横截面积：

\[
A_0=\frac{A_1+A_2+A_3}{3}
=\frac{b_1t_1+b_2t_2+b_3t_3}{3}
\]

本实验采用增量法。载荷依次取 \(2,6,10,14,18\text{ kN}\)，即相邻两级载荷增量为：

\[
\Delta F=4\text{ kN}
\]

每一级载荷下记录四个应变片读数 \(\varepsilon_1,\varepsilon_2,\varepsilon_3,\varepsilon_4\)，并重复三次实验。按课件的数据处理说明，\(\varepsilon_1,\varepsilon_2\) 用来消除附加弯曲影响并合成轴向拉伸应变，\(\varepsilon_3,\varepsilon_4\) 用来合成横向应变：

\[
\varepsilon_F=\frac{\varepsilon_1+\varepsilon_2}{2}
\]

\[
\varepsilon'=\frac{\varepsilon_3+\varepsilon_4}{2}
\]

对相邻两级载荷作差：

\[
\Delta\varepsilon_i=\varepsilon_{F,i}-\varepsilon_{F,i-1}
\]

\[
\Delta\varepsilon'_i=\varepsilon'_{i}-\varepsilon'_{i-1}
\]

主要公式：

\[
E_i=\frac{\Delta F_i}{A_0\Delta\varepsilon_i}
\]

\[
\mu_i=\left|\frac{\Delta\varepsilon'_i}{\Delta\varepsilon_i}\right|
\]

\[
E=\frac{1}{n}\sum_{i=1}^n E_i,\qquad
\mu=\frac{1}{n}\sum_{i=1}^n\mu_i
\]

同时应在 \(\sigma-\varepsilon\) 坐标系下描点并拟合直线，验证单向拉伸胡克定律。

重复三次实验后，脚本会对每一组分别计算 \(\sigma-\varepsilon_F\) 拟合 \(R^2\) 和 \(E_i\) 离散系数，选择线性最好且离散性最低的一组作为最终处理数据。若输入直接给出 `A0_mm2`，脚本优先使用该值；否则按三处截面尺寸自动计算 \(A_0\)，与讲义要求一致。

脚本输出：三组各自质量指标、被选中的组号、逐级 \(E_i,\mu_i\)、平均 \(E,\mu\)，以及被选中组的 \(\sigma-\varepsilon_F\) 拟合方程、拟合斜率、\(R^2\) 和胡克定律验证结论。

## 4. 切变模量 \(G\) 的测定

本实验包含扭角仪法和电测法两种处理路线。按 2026 讲义，实验记录应以分级加载的原始读数为主：每级记录载荷 \(F\)、千分表读数 \(\delta\)、半桥两个通道读数，并重复 3 到 4 组；若重复多组，则选取线性最好的一组进行处理。讲义给出的中碳钢圆轴试件名义直径为 \(D=50\text{ mm}\)，材料屈服极限为 \(220\text{ MPa}\)。

先由三次尺寸测量求平均 \(a,L,D,b\)，并计算圆截面参数：

\[
T=Fa
\]

\[
I_p=\frac{\pi D^4}{32},\qquad W_p=\frac{\pi D^3}{16}
\]

扭角仪法：

\[
\varphi=\frac{\delta}{b}
\]

\[
G_i=\frac{\Delta T_i L}{\Delta\varphi_i I_p}
=\frac{\Delta T_iLb}{\Delta\delta_i I_p}
\]

其中 \(L\) 为两测量截面距离，\(b\) 为百分表杆触点至试件轴线的距离。

电测法中，圆轴表面切应力为：

\[
\tau=\frac{T}{W_p}
\]

若输入的是单片 \(-45^\circ\) 应变，则按课件关系：

\[
\gamma\approx2\varepsilon_{-45^\circ}
\]

若输入的是半桥两个通道的等效剪应变读数，则先取平均作为 \(\gamma\)。逐差法计算：

\[
G_i=\frac{\Delta\tau_i}{\Delta\gamma_i}
\]

脚本输出：每组 \(T-\varphi\) 和 \(\tau-\gamma\) 拟合结果、逐级 \(G_i\)、逐差平均 \(G\)、拟合法 \(G\)、被选中的最佳组号、最大切应力弹性范围校核，以及“是否验证圆轴扭转胡克定律”的结论字段。

## 5. 直梁弯曲实验

本实验按讲义和课件分为纯弯状态与三点弯状态两部分。纯弯部分测定梁横截面上的纵向正应变分布；三点弯部分除测定某一横截面上的纵向正应变分布外，还利用中性层处 \(45^\circ\) 应变片求最大切应变。实验至少重复两次，数据稳定时对同一状态、同一测点取平均值后再处理。

理论关系：

\[
\bar\varepsilon(y)=\frac{1}{n}\sum_{j=1}^{n}\varepsilon_j(y)
\]

\[
\varepsilon(y)=\frac{My}{EI_z},\qquad
\sigma(y)=E\varepsilon(y)=\frac{My}{I_z}
\]

数据处理：

1. 对每个 `state + point` 的重复实验数据求平均，得到 \(\bar\varepsilon(y)\)、\(\bar\varepsilon'(y)\) 和必要时的 \(\bar\varepsilon_{45}\)。
2. 在 \(y-\bar\varepsilon\) 坐标系下描出实验点并线性拟合，与理论直线比较。
3. 由平均实验应变求实验应力：

   \[
   \sigma_{\text{exp}}(y)=E\bar\varepsilon(y)
   \]

4. 对同一 \(y\) 坐标计算理论应变、理论应力与实验结果的相对误差。
5. 计算上下表面横向应变增量与纵向应变增量之比：

   \[
   \left|\frac{\Delta\varepsilon'}{\Delta\varepsilon}\right|
   \approx
   \left|\frac{\bar\varepsilon'}{\bar\varepsilon}\right|
   \]

6. 对三点弯梁，在矩形截面中性层处计算最大切应变：

   \[
   G=\frac{E}{2(1+\mu)},\qquad
   \tau_{\max}=\frac{3Q}{2bh},\qquad
   \gamma_{\max,\text{theory}}=\frac{\tau_{\max}}{G}
   \]

   \[
   \gamma_{\max,\text{exp}}=2\bar\varepsilon_{45}
   \]

7. 对比纯弯状态和三点弯状态下相同 \(y\) 坐标的 \(\bar\varepsilon(y)\)，分析剪力对正应变分布的影响：

   \[
   \Delta\varepsilon_{\text{three-pure}}(y)
   =
   \bar\varepsilon_{\text{three-point}}(y)
   -
   \bar\varepsilon_{\text{pure}}(y)
   \]

脚本输出：各测点平均应变、理论值、相对误差、\(y-\varepsilon\) 拟合直线、上下表面横纵应变比、三点弯最大切应变、纯弯/三点弯对比结果，以及 `conclusion_checks` 和 `conclusions` 结论核对项。

## 6. 梁变形及光弹、疲劳演示实验

按 PPT 和讲义，本实验由梁变形定量实验、光弹性演示实验、疲劳演示实验三部分组成。梁变形部分需要进行公式计算和误差比较；光弹、疲劳部分以演示观察和规律整理为主，若给出条纹级数或疲劳寿命数据，也可作定量整理。

### 简支梁

中点集中载荷 \(P\) 作用下，取左支座为 \(x=0\)，当 \(0\le x\le l/2\)：

\[
f(x)=\frac{Px}{12EI}\left(x^2-\frac{3}{4}l^2\right)
\]

\[
f_{\max}=-\frac{Pl^3}{48EI}
\]

\[
\theta=\frac{df(x)}{dx}=\frac{Px^2}{4EI}-\frac{Pl^2}{16EI},\qquad
\theta_0=-\theta_B=-\frac{Pl^2}{16EI}
\]

支点处转角可由百分表读数估算：

\[
\theta_{\text{exp}}\approx\frac{\delta}{a}
\]

位移互等定理验证：

\[
P_1\Delta_{12}=P_2\Delta_{21}
\]

若 \(P_1=P_2\)，则应有：

\[
\Delta_{12}=\Delta_{21}
\]

### 悬臂梁

贴片截面最大弯曲正应变：

\[
\varepsilon_A=-\varepsilon_B=\varepsilon_{\max}=\frac{M}{EW_z}
\]

两加载位置法：

\[
\Delta\varepsilon=\frac{mg\,l_{12}}{EW_z}
\]

标准砝码比值法：

\[
\frac{m_x}{m_0}=\frac{\varepsilon_{\max-x}}{\varepsilon_{\max-0}}
\]

### 光弹性演示

光弹性部分主要记录偏振光场、条纹形态和对应力分布的判断。平面偏振光场中可同时出现等差线和等倾线；圆偏振光场主要用于观察等差线。暗场中整数级条纹为暗纹，亮场中半整数级条纹为暗纹。

若记录了条纹级数，可按应力光学定律计算主应力差：

\[
\sigma_1-\sigma_2=\frac{Nf_\sigma}{d}
\]

式中，\(N\) 为条纹级数，\(f_\sigma\) 为材料条纹值，\(d\) 为模型厚度。纯弯梁中，等差线应大致反映沿梁高方向线性变化的正应力分布；圆环对径受压中，内外边缘及加载点附近条纹密集，说明局部主应力差变化较快并存在应力集中。

### 疲劳演示

疲劳部分主要记录循环应力水平、应力比、循环次数、是否断裂及断口特征。应力比为：

\[
R=\frac{\sigma_{\min}}{\sigma_{\max}}
\]

疲劳寿命 \(N\) 表示试样从开始承受循环载荷到发生疲劳破坏时经历的循环次数。数据整理时可按应力幅或最大应力与 \(\log N\) 作图，得到 S-N 曲线趋势。通常应力水平越低，疲劳寿命越长；若达到指定循环次数仍未断裂，应作为未断裂点记录。典型疲劳断口可描述为裂纹源、裂纹扩展区和瞬断区。

脚本输出：挠度曲线理论值、最大挠度误差、支点转角误差、互等定理误差和位移差、悬臂梁未知质量、光弹主应力差或观察记录、疲劳寿命 \(\log_{10}N\) 与断口记录。

## 7. 弯扭组合试验

本实验处理三个任务：求主应力与主平面方位角，求某截面弯矩 \(M\)，求某截面扭矩 \(T\)，并与按名义尺寸和理论内力得到的理论值比较。

按讲义采用重复加载法：初载荷 \(F_0=500\text{ N}\)，最大载荷 \(F_{\max}=1500\text{ N}\)，载荷增量
\(\Delta F=1000\text{ N}\)，重复 \(n=4\) 次。每次加载后记录同一测点的 \(0^\circ,\pm45^\circ\) 应变花读数，数据处理时先对 4 次读数求平均，再代入后续公式。

试件尺寸按讲义要求多次测量并取平均。若输入外径 \(D\) 与壁厚 \(t\)，程序取：

\[
d=D-2t
\]

空心圆轴名义尺寸为 \(D=42\text{ mm}\)，壁厚 \(t=3\text{ mm}\)，故 \(d=36\text{ mm}\)。材料参数取 \(E=206\text{ GPa}\)，\(\mu=0.28\)。

0 度、\(\pm45^\circ\) 三向应变花平均读数满足：

\[
\varepsilon_x=\varepsilon_0
\]

\[
\varepsilon_y=\varepsilon_{45^\circ}+\varepsilon_{-45^\circ}-\varepsilon_0
\]

\[
\gamma_{xy}=\varepsilon_{-45^\circ}-\varepsilon_{45^\circ}
\]

主应变：

\[
\varepsilon_{1,2}=\frac{\varepsilon_x+\varepsilon_y}{2}
\pm
\sqrt{\left(\frac{\varepsilon_x-\varepsilon_y}{2}\right)^2+
\left(\frac{\gamma_{xy}}{2}\right)^2}
\]

主方向：

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

弯矩：

\[
M=EW_z\varepsilon_0
\]

若采用弯矩半桥测量，仪器显示应变为：

\[
\bar{\varepsilon}=2\varepsilon_0
\]

因此计算弯矩时应使用：

\[
\varepsilon_0=\frac{\bar{\varepsilon}}{2}
\]

扭矩：

\[
T=\frac{E}{2(1+\mu)}W_p(\varepsilon_{-45^\circ}-\varepsilon_{45^\circ})
\]

若采用扭矩桥路测量，仪器显示应变为：

\[
\bar{\varepsilon}=2\gamma_{xy}=2(\varepsilon_{-45^\circ}-\varepsilon_{45^\circ})
\]

因此计算扭矩时应使用：

\[
\gamma_{xy}=\frac{\bar{\varepsilon}}{2}
\]

理论弯矩、扭矩可直接输入，也可由载荷增量和力臂计算。课件给出形成扭矩的力臂 \(l_1=200\text{ mm}\)，形成弯矩的力臂 \(l_2=240\text{ mm}\)。若按本汇总采用的剪应变符号 \(\gamma_{xy}=\varepsilon_{-45^\circ}-\varepsilon_{45^\circ}\)，样例可取：

\[
M_{\text{th}}=\Delta F l_2,\qquad T_{\text{th}}=-\Delta F l_1
\]

由理论 \(M,T\) 得：

\[
\sigma_{x,\text{th}}=\frac{M_{\text{th}}}{W_z},\qquad
\tau_{xy,\text{th}}=\frac{T_{\text{th}}}{W_p}
\]

\[
\sigma_{1,2,\text{th}}=
\frac{\sigma_{x,\text{th}}}{2}
\pm
\sqrt{\left(\frac{\sigma_{x,\text{th}}}{2}\right)^2+\tau_{xy,\text{th}}^2}
\]

\[
\tan 2\alpha_{\text{th}}=-\frac{2\tau_{xy,\text{th}}}{\sigma_{x,\text{th}}}
\]

脚本输出：尺寸平均值和标准差、重复读数的平均值和标准差、\(\varepsilon_x,\varepsilon_y,\gamma_{xy}\)、主应变、主应力、主方向、半桥等效 \(\varepsilon_0\)、扭矩桥路等效 \(\gamma_{xy}\)、实验 \(M,T\)、理论 \(M,T\)、理论主应力/主方向及误差。结论部分应说明 \(M,T,\sigma_1,\sigma_2,\alpha\) 与理论值的误差，并分析应变片角度、接线、温度补偿、力臂、截面尺寸和装夹偏心等误差来源。

## 8. 偏心拉伸实验

偏心拉伸截面同时存在轴力与弯矩。按讲义，本实验采用重复加载法处理数据：\(F_0=2\text{ kN}\)，\(F_{\max}=12\text{ kN}\)，\(\Delta F=10\text{ kN}\)，重复次数 \(N=4\)。课件 PDF 第 8 页的示例载荷为 \(F_0=5\text{ kN}\)、\(F_{\max}=15\text{ kN}\)，与讲义不一致；本汇总以讲义为准。数据处理目标是求横截面最大正应变增量、材料弹性模量、最大正应力增量和圆孔偏心距。

截面参数：

\[
A=hb,\qquad W_z=\frac{hb^2}{6}
\]

全桥测轴向拉伸应变时，仪器显示值为两片工作片的组合输出：

\[
\varepsilon_{\text{full}}=2\varepsilon_F
\]

因此应先换算为：

\[
\Delta\varepsilon_F=\frac{\varepsilon_{\text{full}}}{2}
\]

半桥测偏心弯曲应变时，仪器显示值为两侧应变差：

\[
\varepsilon_{\text{half}}=\varepsilon_a-\varepsilon_b=2\varepsilon_{M1,\max}
\]

因此应先换算为：

\[
\Delta\varepsilon_{M1,\max}=\frac{\varepsilon_{\text{half}}}{2}
\]

若同时测得 \(R_1,R_2\) 方向的弯曲分量，则：

\[
\Delta\varepsilon_{\max}
=\Delta\varepsilon_F+\Delta\varepsilon_{M1,\max}+\Delta\varepsilon_{M2,\max}
\]

若最大正应变由 \(1/4\) 桥直接测得，则直接使用该读数作为 \(\Delta\varepsilon_{\max}\)。

每次重复加载的弹性模量：

\[
E_i=\frac{\Delta F}{A\Delta\varepsilon_{F,i}}
\]

最大正应力增量：

\[
\Delta\sigma_{\max,i}=E_i\Delta\varepsilon_{\max,i}
\]

偏心距：

\[
e_i=\frac{\Delta\varepsilon_{M1,i}E_iW_z}{\Delta F}
\]

最后对 4 次重复加载的 \(\Delta\varepsilon_{\max}\)、\(E\)、\(\Delta\sigma_{\max}\)、\(e\) 分别求平均值。结论中应同时说明最大正应变、材料弹性模量、最大正应力增量和圆孔偏心距，并检查最大正应力是否仍在弹性范围内。脚本输出每次重复加载的换算结果、平均结果、讲义要求核对项和结论字段，并兼容直接输入 \(\varepsilon_F,\varepsilon_M\) 或输入全桥、半桥显示读数两种方式。
