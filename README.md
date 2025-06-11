# 📌 **多期发电扩展规划 (GEP) + 储能 + 可再生比例约束模型**

---

## **集合与索引**

* $I$ ：发电技术集合，$I = \{\text{coal}, \text{gas}, \text{wind}, \text{solar}\}$
* $t$ ：时间期（年），$t = 1, 2, \dots, T$

---

## **参数**

* $d_t$ ：第 $t$ 年的电力需求 (GW)

* $c_i$ ：发电技术 $i$ 的单位投资成本 (\$/GW)

* $o_i$ ：发电技术 $i$ 的单位运行成本 (\$/GWh)

* $\overline{B}_i$ ：发电技术 $i$ 每年最大新增容量 (GW)

* $\overline{C}_i$ ：发电技术 $i$ 的最大累计容量 (GW)

* $C_i^0$ ：发电技术 $i$ 的初始容量 (GW)

* $c_s$ ：储能投资成本 (\$/GWh)

* $o_s$ ：储能放电运行成本 (\$/GWh)

* $\eta_{ch}$：储能充电效率

* $\eta_{dis}$：储能放电效率

* $\overline{B}_s$：储能每年最大新增容量 (GWh)

* $\overline{C}_s$：储能总容量上限 (GWh)

* $C_s^0$：储能初始容量 (GWh)

* $r_t$ ：第 $t$ 年可再生能源比例要求

* $R \subset I$ ：可再生能源集合，$R = \{\text{wind}, \text{solar}\}$

---

## **决策变量**

* $\text{Build}_{i,t}$ ：第 $t$ 年为技术 $i$ 建设的新容量 (GW)

* $\text{TotalCap}_{i,t}$ ：第 $t$ 年技术 $i$ 累计总容量 (GW)

* $\text{Gen}_{i,t}$ ：第 $t$ 年技术 $i$ 发电量 (GWh)

* $\text{BuildS}_t$ ：第 $t$ 年新增储能容量 (GWh)

* $\text{TotalCapS}_t$ ：第 $t$ 年储能累计总容量 (GWh)

* $\text{SOC}_t$ ：第 $t$ 年储能荷电状态 (GWh)

* $\text{Charge}_t$ ：第 $t$ 年充电功率 (GW)

* $\text{Discharge}_t$ ：第 $t$ 年放电功率 (GW)

---

## **目标函数**

最小化总成本（投资 + 运行成本）：

$$
\min \sum_{t=1}^T \left[ \sum_{i \in I} \left( c_i \cdot \text{Build}_{i,t} + o_i \cdot \text{Gen}_{i,t} \right) + c_s \cdot \text{BuildS}_t + o_s \cdot \text{Discharge}_t \right]
$$

---

## **约束条件**

### 1. 容量积累平衡

$$
\text{TotalCap}_{i,t} =
\begin{cases}
C_i^0 + \text{Build}_{i,1} & \text{if } t=1 \\
\text{TotalCap}_{i,t-1} + \text{Build}_{i,t} & \text{if } t>1
\end{cases}
$$

$$
\text{TotalCapS}_t =
\begin{cases}
C_s^0 + \text{BuildS}_1 & \text{if } t=1 \\
\text{TotalCapS}_{t-1} + \text{BuildS}_t & \text{if } t>1
\end{cases}
$$

---

### 2. 储能荷电状态平衡 (SOC)

$$
\text{SOC}_t =
\begin{cases}
\eta_{ch} \cdot \text{Charge}_1 - \dfrac{\text{Discharge}_1}{\eta_{dis}} & \text{if } t=1 \\
\text{SOC}_{t-1} + \eta_{ch} \cdot \text{Charge}_t - \dfrac{\text{Discharge}_t}{\eta_{dis}} & \text{if } t>1
\end{cases}
$$

---

### 3. 储能容量限制

$$
\text{SOC}_t \leq \text{TotalCapS}_t, \quad \forall t
$$

$$
\text{BuildS}_t \leq \overline{B}_s, \quad \forall t
$$

$$
\text{TotalCapS}_t \leq \overline{C}_s, \quad \forall t
$$

---

### 4. 供需平衡 (含储能充放电)

$$
\sum_{i \in I} \text{Gen}_{i,t} + \text{Discharge}_t \geq d_t + \text{Charge}_t, \quad \forall t
$$

---

### 5. 发电容量约束

$$
\text{Gen}_{i,t} \leq \text{TotalCap}_{i,t}, \quad \forall i, t
$$

---

### 6. 投产速度及容量上限

$$
\text{Build}_{i,t} \leq \overline{B}_i, \quad \forall i, t
$$

$$
\text{TotalCap}_{i,t} \leq \overline{C}_i, \quad \forall i, t
$$

---

### 7. 可再生能源比例约束

$$
\sum_{i \in R} \text{Gen}_{i,t} \geq r_t \cdot \left( \sum_{i \in I} \text{Gen}_{i,t} + \text{Discharge}_t \right), \quad \forall t
$$

---
