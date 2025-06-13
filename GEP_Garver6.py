import numpy as np
import gurobipy as gp
from gurobipy import GRB
from Garver6 import case_garver6

# =======================
# 读取Garver 6节点系统
# =======================

ppc = case_garver6()
bus = ppc["bus"]
branch = ppc["branch"]
baseMVA = ppc["baseMVA"]

nbus = bus.shape[0]
nbranch = branch.shape[0]

# 计算DC潮流导纳矩阵B
B = np.zeros((nbus, nbus))
for k in range(nbranch):
    i = int(branch[k, 0]) - 1
    j = int(branch[k, 1]) - 1
    x = branch[k, 3]
    b = 1 / x
    B[i, j] -= b
    B[j, i] -= b
    B[i, i] += b
    B[j, j] += b

# =======================
# 输入数据
# =======================

T = 5
I = ['coal', 'gas', 'wind', 'solar']
renewable = ['wind', 'solar']

# 用电需求（MW）
d = {1: 5000, 2: 9000, 3: 10000, 4: 10000, 5: 10000}

# 投资成本 ($/MW)
c = {'coal': 1000, 'gas': 800, 'wind': 120, 'solar': 900}

# 运行成本 ($/MWh)
o = {'coal': 50, 'gas': 60, 'wind': 10, 'solar': 5}

# 最大投资和容量
max_build = {'coal': 2000, 'gas': 3000, 'wind': 5000, 'solar': 5000}
max_cap = {'coal': 5000, 'gas': 3000, 'wind': 2000, 'solar': 4000}
initial_cap = {'coal': 2000, 'gas': 500, 'wind': 800, 'solar': 1600}

# 储能
c_s, o_s = 500, 5
eta_ch, eta_dis = 0.95, 0.95
max_build_s = 5000
max_cap_s = 2000
initial_cap_s = 0

# 可再生能源比例
r = {1: 0.4, 2: 0.4, 3: 0.4, 4: 0.4, 5: 0.4}

# 线路容量（MW）
line_limit = branch[:, 5]

# =======================
# 建立模型
# =======================

model = gp.Model("GEP_with_Storage_and_DCFlow")

# GEP部分变量
build = model.addVars(I, range(1, T+1), name="Build", lb=0)
gen = model.addVars(I, range(1, T+1), name="Gen", lb=0)
totalcap = model.addVars(I, range(1, T+1), name="TotalCap", lb=0)

# 储能部分变量
build_s = model.addVars(range(1, T+1), name="BuildStorage", lb=0)
totalcap_s = model.addVars(range(1, T+1), name="TotalCapStorage", lb=0)
soc = model.addVars(range(1, T+1), name="StateOfCharge", lb=0)
ch = model.addVars(range(1, T+1), name="Charge", lb=0)
dis = model.addVars(range(1, T+1), name="Discharge", lb=0)

# 潮流部分变量
theta = model.addVars(nbus, range(1, T+1), lb=-np.pi, ub=np.pi, name="Theta")
flow = model.addVars(nbranch, range(1, T+1), name="Flow")

# 目标函数
model.setObjective(
    gp.quicksum(c[i]*build[i,t] for i in I for t in range(1, T+1)) +
    gp.quicksum(o[i]*gen[i,t] for i in I for t in range(1, T+1)) +
    gp.quicksum(c_s*build_s[t] for t in range(1, T+1)) +
    gp.quicksum(o_s*dis[t] for t in range(1, T+1)),
    GRB.MINIMIZE
)

# 装机容量递推
for i in I:
    for t in range(1, T+1):
        model.addConstr(
            totalcap[i, t] == (initial_cap[i] + gp.quicksum(build[i, k] for k in range(1, t+1))),
            name=f"TotalCap_{i}_{t}"
        )
        model.addConstr(gen[i, t] <= totalcap[i, t], name=f"GenLimit_{i}_{t}")
        model.addConstr(build[i, t] <= max_build[i], name=f"BuildLimit_{i}_{t}")
        model.addConstr(totalcap[i, t] <= max_cap[i], name=f"MaxCap_{i}_{t}")

for t in range(1, T+1):
    model.addConstr(totalcap_s[t] == initial_cap_s + gp.quicksum(build_s[k] for k in range(1, t+1)), name=f"TotalCapStorage_{t}")
    model.addConstr(soc[t] <= totalcap_s[t], name=f"SocLimit_{t}")
    model.addConstr(build_s[t] <= max_build_s, name=f"BuildStorageLimit_{t}")
    model.addConstr(totalcap_s[t] <= max_cap_s, name=f"MaxCapStorage_{t}")
    model.addConstr(
        soc[t] == (soc[t-1] if t > 1 else 0) + eta_ch*ch[t] - dis[t]/eta_dis, name=f"SocBalance_{t}"
    )

# 可再生能源比例
for t in range(1, T+1):
    model.addConstr(
        gp.quicksum(gen[i, t] for i in renewable) >= r[t] * (
            gp.quicksum(gen[i, t] for i in I) + dis[t]
        ),
        name=f"RenewableShare_{t}"
    )

# 电力平衡 + 储能
for t in range(1, T+1):
    model.addConstr(
        gp.quicksum(gen[i, t] for i in I) + dis[t] >= d[t] + ch[t],
        name=f"PowerBalance_{t}"
    )

# 潮流平衡
for t in range(1, T+1):
    model.addConstr(theta[0, t] == 0, name=f"BalanceBus_{t}")  # 平衡节点固定

    for k in range(nbranch):
        i = int(branch[k, 0]) - 1
        j = int(branch[k, 1]) - 1
        model.addConstr(flow[k, t] == (theta[i, t] - theta[j, t]) / branch[k, 3], name=f"Flow_{k}_{t}")
        model.addConstr(flow[k, t] <= line_limit[k], name=f"FlowLimit_{k}_{t}")
        model.addConstr(flow[k, t] >= -line_limit[k], name=f"FlowLimitNeg_{k}_{t}")

    # 节点平衡
    total_injection = gp.quicksum(gen[i, t] for i in I) + dis[t] - ch[t] - d[t]
    model.addConstr(
        gp.quicksum(flow[k, t] for k in range(nbranch) if int(branch[k, 0]) - 1 == 0)
        - gp.quicksum(flow[k, t] for k in range(nbranch) if int(branch[k, 1]) - 1 == 0)
        == total_injection,
        name=f"NodeBalance_{t}"
    )

# 求解
model.optimize()

# 结果输出
if model.status == GRB.OPTIMAL:
    print("\n最优总成本：", model.objVal)
    for t in range(1, T+1):
        print(f"\nYear {t}:")
        for i in I:
            print(f"{i}: Build={build[i,t].X:.2f}, TotalCap={totalcap[i,t].X:.2f}, Gen={gen[i,t].X:.2f}")
        print(f"Storage: Build={build_s[t].X:.2f}, TotalCap={totalcap_s[t].X:.2f}, SOC={soc[t].X:.2f}")
else:
    print("模型未找到最优解")
    model.computeIIS()
    model.write("model.ilp")
    # model.write("model.iis")
    for c in model.getConstrs():
        if c.IISConstr:
            print(f"Infeasible constraint: {c.ConstrName}")