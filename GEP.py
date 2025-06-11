import gurobipy as gp
from gurobipy import GRB

# ============================
# 输入数据
# ============================

T = 5  # 规划期总年数
I = ['coal', 'gas', 'wind', 'solar']  # 发电技术种类

# 用电需求 (单位: GW)
d = {1: 50, 2: 55, 3: 60, 4: 65, 5: 70}

# 单位投资成本 ($/GW)
c = {'coal': 1000, 'gas': 800, 'wind': 1200, 'solar': 900}

# 单位运行成本 ($/GWh)
o = {'coal': 50, 'gas': 60, 'wind': 10, 'solar': 5}

# 每年最大新增容量 (GW)
max_build = {'coal': 200, 'gas': 300, 'wind': 500, 'solar': 500}

# 最大累计装机容量 (GW)
max_cap = {'coal': 10, 'gas': 15, 'wind': 20, 'solar': 20}

# 初始装机容量 (GW)
initial_cap = {'coal': 5, 'gas': 5, 'wind': 3, 'solar': 2}

# 储能参数
c_s = 500   # 储能投资成本 ($/GWh)
o_s = 5     # 储能运行成本 ($/GWh)
eta_ch = 0.95
eta_dis = 0.95
max_build_s = 500  # 每年最大新增储能容量 (GWh)
max_cap_s = 200   # 最大储能容量 (GWh)
initial_cap_s = 0  # 初始储能容量

# 可再生能源比例要求
r = {1: 0.30, 2: 0.35, 3: 0.40, 4: 0.45, 5: 0.50}
# r = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}


# ============================
# 模型建立
# ============================

model = gp.Model("GEP_with_Storage_and_Renewable_Share")

# 决策变量
build = model.addVars(I, range(1, T+1), name="Build", lb=0)
gen = model.addVars(I, range(1, T+1), name="Gen", lb=0)
totalcap = model.addVars(I, range(1, T+1), name="TotalCap", lb=0)

build_s = model.addVars(range(1, T+1), name="BuildStorage", lb=0)
totalcap_s = model.addVars(range(1, T+1), name="TotalCapStorage", lb=0)
soc = model.addVars(range(1, T+1), name="StateOfCharge", lb=0)
ch = model.addVars(range(1, T+1), name="Charge", lb=0)
dis = model.addVars(range(1, T+1), name="Discharge", lb=0)

# 目标函数: 投资 + 运行成本
model.setObjective(
    gp.quicksum(c[i]*build[i,t] for i in I for t in range(1, T+1)) +
    gp.quicksum(o[i]*gen[i,t] for i in I for t in range(1, T+1)) +
    gp.quicksum(c_s*build_s[t] for t in range(1, T+1)) +
    gp.quicksum(o_s*dis[t] for t in range(1, T+1)),
    GRB.MINIMIZE
)

# 装机容量递推约束
for i in I:
    for t in range(1, T+1):
        if t == 1:
            model.addConstr(totalcap[i, t] == initial_cap[i] + build[i, t])
        else:
            model.addConstr(totalcap[i, t] == totalcap[i, t-1] + build[i, t])

for t in range(1, T+1):
    if t == 1:
        model.addConstr(totalcap_s[t] == initial_cap_s + build_s[t])
    else:
        model.addConstr(totalcap_s[t] == totalcap_s[t-1] + build_s[t])

# 储能充放电与SOC平衡
for t in range(1, T+1):
    if t == 1:
        model.addConstr(soc[t] == 0 + eta_ch*ch[t] - dis[t]/eta_dis)
    else:
        model.addConstr(soc[t] == soc[t-1] + eta_ch*ch[t] - dis[t]/eta_dis)

# 储能容量限制
for t in range(1, T+1):
    model.addConstr(soc[t] <= totalcap_s[t])
    model.addConstr(build_s[t] <= max_build_s)
    model.addConstr(totalcap_s[t] <= max_cap_s)

# 需求平衡（加入储能放电）
for t in range(1, T+1):
    model.addConstr(gp.quicksum(gen[i, t] for i in I) + dis[t] >= d[t] + ch[t])

# 发电量不超过装机容量
for i in I:
    for t in range(1, T+1):
        model.addConstr(gen[i, t] <= totalcap[i, t])

# 投产速度与容量上限
for i in I:
    for t in range(1, T+1):
        model.addConstr(build[i, t] <= max_build[i])
        model.addConstr(totalcap[i, t] <= max_cap[i])

# 可再生能源比例约束
renewable = ['wind', 'solar']
for t in range(1, T+1):
    model.addConstr(
        gp.quicksum(gen[i, t] for i in renewable) >= r[t] * (
            gp.quicksum(gen[i, t] for i in I) + dis[t]
        ),
        name=f"RenewableShare_{t}"
    )

# ============================
# 求解
# ============================

model.optimize()

# ============================
# 结果输出
# ============================

if model.status == GRB.OPTIMAL:
    print("\n最优总成本：", model.objVal)
    print("\n装机计划与储能策略：")
    for i in I:
        for t in range(1, T+1):
            print(f"{i} - Year {t}: Build={build[i,t].X:.2f}, TotalCap={totalcap[i,t].X:.2f}, Gen={gen[i,t].X:.2f}")
    for t in range(1, T+1):
        print(f"Year {t}: BuildStorage={build_s[t].X:.2f}, TotalCapStorage={totalcap_s[t].X:.2f}, SOC={soc[t].X:.2f}, Charge={ch[t].X:.2f}, Discharge={dis[t].X:.2f}")
else:
    print("模型未找到最优解")
