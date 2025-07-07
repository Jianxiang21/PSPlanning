import pandas as pd
import numpy as np

def casejiangsu():
    """
    Reads the case data from Jiangsu province and returns it as a DataFrame.
    
    Returns:
        pd.DataFrame: DataFrame containing the case data.
    """
    # Define the file path
    file_path = '江苏500kV数据.xlsx'
    
    # Read the CSV file into a DataFrame
    sheets_dict = pd.read_excel(file_path,sheet_name=None)
    print(sheets_dict.keys())
    bus_sheet = sheets_dict['Bus']
    branch_sheet = sheets_dict['Branch']
    thermal_sheet = sheets_dict['火电燃机']
    hydro_sheet = sheets_dict['抽水蓄能']
    wind_sheet = sheets_dict['风电']
    solar_sheet = sheets_dict['光伏']
    bio_sheet = sheets_dict['生物质']

    # 0: BUS_I       母线编号（从1开始）
    # 1: BUS_TYPE    母线类型（1 PQ, 2 PV, 3 平衡母线）
    # 2: PD          有功负荷（MW）
    # 3: QD          无功负荷（MVAr）
    # 4: GS          并联电导（MW at V = 1.0 p.u.）
    # 5: BS          并联电纳（MVAr at V = 1.0 p.u.）
    # 6: BUS_AREA    区域编号（可选）
    # 7: VM          电压幅值（p.u.）
    # 8: VA          电压相角（度）
    # 9: BASE_KV     基准电压（kV）
    # 10: ZONE       区域编号（可选）
    # 11: VMAX       最大电压（p.u.）
    # 12: VMIN       最小电压（p.u.）
    bus = bus_sheet[['编号', '类型', '负载有功', '负载无功', '电压标幺值','相角', '电压']]
    bus.columns = ['BUS_I', 'BUS_TYPE', 'PD', 'QD', 'VM', 'VA', 'BASE_KV']
    bus['GS'] = 0.0  # 并联电导
    bus['BS'] = 0.0  # 并联电纳
    bus['BUS_AREA'] = 1  # 默认区域编号为1
    bus['ZONE'] = 1  # 默认区域编号为1
    bus['VMAX'] = 1.1  # 最大电压（p.u.）
    bus['VMIN'] = 0.9  # 最小电压（p.u.）
    bus = bus[['BUS_I', 'BUS_TYPE', 'PD', 'QD', 'GS', 'BS', 'BUS_AREA', 'VM', 'VA', 'BASE_KV', 'ZONE', 'VMAX', 'VMIN']]

    # 0: F_BUS       起点母线编号
    # 1: T_BUS       终点母线编号
    # 2: R           电阻（p.u.）
    # 3: X           电抗（p.u.）
    # 4: B           并联电纳（p.u.）
    # 5: RATE_A      容量A（MVA）
    # 6: RATE_B      容量B（MVA）
    # 7: RATE_C      容量C（MVA）
    # 8: TAP         变比（若有变压器；否则为1）
    # 9: SHIFT       相角差（度）
    # 10: BR_STATUS  状态（1：在线，0：断开）
    # 11: ANGMIN     最小相角差（度）
    # 12: ANGMAX     最大相角差（度）

    branch = branch_sheet[['起点', '终点', '电阻', '电抗', '导纳']]
    branch.columns = ['F_BUS', 'T_BUS', 'R', 'X', 'B']
    branch['RATE_A'] = 9999.0  # 容量A（MVA）
    branch['RATE_B'] = 9999.0  # 容量B（MVA）
    branch['RATE_C'] = 9999.0  # 容量C（MVA）
    branch['TAP'] = 1.0  # 变比（若有变压器；否则为1）
    branch['SHIFT'] = 0.0  # 相角差（度）
    branch['BR_STATUS'] = 1  # 状态（1：在线，0：断开）
    branch['ANGMIN'] = -360.0  # 最小相角差（度）
    branch['ANGMAX'] = 360.0  # 最大相角差（度）
    branch = branch[['F_BUS', 'T_BUS', 'R', 'X', 'B', 'RATE_A', 'RATE_B', 'RATE_C', 'TAP', 'SHIFT', 'BR_STATUS', 'ANGMIN', 'ANGMAX']]
    
    # 0: BUS         所在母线编号
    # 1: PG          有功出力（MW）
    # 2: QG          无功出力（MVAr）
    # 3: QMAX        无功上限
    # 4: QMIN        无功下限
    # 5: VG          电压设定值（p.u.）
    # 6: MBASE       基准容量（通常等于 baseMVA）
    # 7: GEN_STATUS  状态（1：在线，0：停机）
    # 8: PMAX        有功上限（MW）
    # 9: PMIN        有功下限（MW）
    gen = pd.concat([
        thermal_sheet[['所在节点', '功率']],
        hydro_sheet[['所在节点', '功率']],
        wind_sheet[['所在节点', '功率']],
        solar_sheet[['所在节点', '功率']],
        bio_sheet[['所在节点', '功率']]
    ], ignore_index=True)
    gen.columns = ['BUS', 'PG']
    gen['QG'] = 0.0  # 无功出力（MVAr）
    gen['QMAX'] = 9999.0  # 无功上限
    gen['QMIN'] = -9999.0  # 无功下限
    gen['VG'] = 1.0  # 电压设定值（p.u.）
    gen['MBASE'] = 100.0  # 基准容量（通常等于 baseMVA）
    gen['GEN_STATUS'] = 1  # 状态（1：在线，0：停机）
    gen['PMAX'] = gen['PG'] * 1.2  # 有功上限（MW），假设为出力的1.2倍
    gen['PMIN'] = 0.0  # 有功下限（MW）
    gen = gen[['BUS', 'PG', 'QG', 'QMAX', 'QMIN', 'VG', 'MBASE', 'GEN_STATUS', 'PMAX', 'PMIN']]

    ppc = {
        "version": '2',
        "baseMVA": 100.0,
        "bus": bus.to_numpy(),
        "branch": branch.to_numpy(),
        "gen": gen.to_numpy(),
        "gencost": np.array([])  # 这里可以添加发电机成本数据，如果有的话
    }


    # Return the DataFrame
    return ppc

if __name__ == "__main__":
    # Read the case data
    case_data = casejiangsu()
    print(case_data)
    
    # Display the first few rows of the DataFrame
    # print(case_data.head())
    
    # Optionally, you can save it to a CSV file if needed
    # case_data.to_csv('casejiangsu.csv', index=False)