# Generation Expansion Planning with Storage and DC Power Flow

## 项目简介

本项目实现了一个**代内多期发电扩建规划模型**，综合考虑了：

* 多种发电技术（煤电、燃气、风电、光伏）
* 储能系统（电池储能）
* DC潮流模型（直流潮流近似）
* 可再生能源比例约束
* 投资与运行成本优化

模型使用 Gurobi 求解器编写，基于 Garver 6 节点系统进行测试。

---

## 模型符号定义

### 集合与索引

* $T$：规划期集合（年份）
* $I$：发电技术集合（煤电、燃气、风电、光伏）
* $R \subseteq I$：可再生能源集合（风电、光伏）
* $N$：节点集合
* $L$：线路集合

### 参数

| 参数                      | 含义                       |
| ----------------------- | ------------------------ |
| $d_t$                   | 第 $t$ 年负荷需求（MW）          |
| $c_i$                   | 技术 $i$ 的单位容量投资成本（\$/MW）  |
| $o_i$                   | 技术 $i$ 的单位发电运行成本（\$/MWh） |
| $c_s$                   | 储能单位投资成本（\$/MW）          |
| $o_s$                   | 储能单位放电运行成本（\$/MWh）       |
| $\eta_{ch}, \eta_{dis}$ | 储能充放电效率                  |
| $r_t$                   | 第 $t$ 年可再生能源最低占比         |
| $\overline{B}_i$        | 每期技术 $i$ 最大可新增容量（MW）     |
| $\overline{C}_i$        | 技术 $i$ 最大总容量（MW）         |
| $\overline{B}_s$        | 储能最大新增容量（MW）             |
| $\overline{C}_s$        | 储能最大总容量（MW）              |
| $\overline{F}_l$        | 线路 $l$ 容量极限（MW）          |
| $x_l$                   | 线路 $l$ 电抗值（p.u.）         |
| $B$                     | DC 潮流导纳矩阵（节点间）           |

### 决策变量

| 变量                                      | 含义                       |
| --------------------------------------- | ------------------------ |
| $\text{Build}_{i,t}$                    | 第 $t$ 年技术 $i$ 新增容量（MW）   |
| $\text{TotalCap}_{i,t}$                 | 第 $t$ 年技术 $i$ 总装机容量（MW）  |
| $\text{Gen}_{i,t}$                      | 第 $t$ 年技术 $i$ 实际发电量（MWh） |
| $\text{BuildStorage}_t$                 | 储能新增容量（MW）               |
| $\text{TotalCapStorage}_t$              | 储能总容量（MW）                |
| $\text{SOC}_t$                          | 储能荷电状态（MWh）              |
| $\text{Charge}_t$, $\text{Discharge}_t$ | 储能充放电量（MWh）              |
| $\theta_{n,t}$                          | 第 $t$ 年节点 $n$ 相角（弧度）     |
| $\text{Flow}_{l,t}$                     | 第 $t$ 年线路 $l$ 潮流（MW）     |

---

## 数学模型

### 目标函数

最小化多期总成本（投资成本 + 运行成本）：

$$
\min \sum_{t=1}^T \left( \sum_{i \in I} \left( c_i \cdot \text{Build}_{i,t} + o_i \cdot \text{Gen}_{i,t} \right) + c_s \cdot \text{BuildStorage}_t + o_s \cdot \text{Discharge}_t \right)
$$

---

### 约束条件

#### 1. 装机容量递推约束

$$\text{TotalCap}_{i,t} = \text{initial\_cap}_i + \sum_{k=1}^{t} \text{Build}_{i,k}, \quad \forall i \in I, \forall t$$

$$\text{TotalCapStorage}_{t} = \text{initial\_cap}_s + \sum_{k=1}^{t} \text{BuildStorage}_k, \quad \forall t$$

#### 2. 装机容量限制

$$\text{Build}_{i,t} \leq \overline{B}_i, \quad \text{TotalCap}_{i,t} \leq \overline{C}_i, \quad \forall i, t$$

$$\text{BuildStorage}_t \leq \overline{B}_s, \quad \text{TotalCapStorage}_t \leq \overline{C}_s, \quad \forall t$$

#### 3. 发电出力限制

$$\text{Gen}_{i,t} \leq \text{TotalCap}_{i,t}, \quad \forall i, t$$

#### 4. 储能荷电平衡

$$\text{SOC}_t = \text{SOC}_{t-1} + \eta_{ch} \cdot \text{Charge}_t - \frac{1}{\eta_{dis}} \cdot \text{Discharge}_t, \quad \forall t$$

其中当 $t=1$ 时，$\text{SOC}_0 = 0$。

#### 5. 储能荷电上限

$$\text{SOC}_t \leq \text{TotalCapStorage}_t, \quad \forall t$$

#### 6. 可再生能源占比约束

$$\sum_{i \in R} \text{Gen}_{i,t} \geq r_t \cdot \left( \sum_{i \in I} \text{Gen}_{i,t} + \text{Discharge}_t \right), \quad \forall t$$

#### 7. 功率平衡约束（含储能充放电）

$$\sum_{i \in I} \text{Gen}_{i,t} + \text{Discharge}_t \geq d_t + \text{Charge}_t, \quad \forall t$$

#### 8. 潮流平衡方程（DC潮流）

* 平衡节点角度固定：

$$\theta_{1,t} = 0, \quad \forall t$$

* 线路潮流：

$$\text{Flow}_{l,t} = \frac{\theta_{i,t} - \theta_{j,t}}{x_l}, \quad \forall l = (i,j), \forall t$$

* 线路容量限制：

$$-\overline{F}_l \leq \text{Flow}_{l,t} \leq \overline{F}_l, \quad \forall l, t$$

#### 9. 节点功率平衡（仅对平衡节点写出）

$$\sum_{l \in \delta^+(n)} \text{Flow}_{l,t} - \sum_{l \in \delta^-(n)} \text{Flow}_{l,t} = \sum_{i \in I} \text{Gen}_{i,t} + \text{Discharge}_t - \text{Charge}_t - d_t$$

其中，$\delta^+(n)$、$\delta^-(n)$ 分别为节点 $n$ 的流入、流出线路集合。你的代码中暂时只对平衡节点（节点 0）进行了平衡约束建模。

---

## 运行环境

* Python 3.x
* Gurobi 10.x
* NumPy

## 数据说明

* 系统数据文件：`Garver6.py` (需放置在同级目录下)
* 规划年数：5年
* 各类成本、容量上限、需求、可再生比例等均在代码中以字典形式硬编码，便于修改扩展

## 后续可扩展方向

* 增加负荷不确定性与场景分析
* 纳入二氧化碳排放约束
* 扩展 AC 潮流模型
* 引入投资折现、利率、生命周期成本等现实要素
