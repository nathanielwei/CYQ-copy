import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def safe_division(asr, total_chip):
    if total_chip == 0 or pd.isna(total_chip) or pd.isna(asr):
        return float('nan')
    return asr / total_chip


# 活动筹码 ASR
def ASR(chip_row, close):
    # 上界和下界
    lower_bound = 0.9 * close
    upper_bound = 1.1 * close
    total_chip = sum(chip_row)
    asr = sum(chip_row[(chip_row.index.astype(float) > lower_bound) & (chip_row.index.astype(float) < upper_bound)].values)
    result = safe_division(asr, total_chip)

    return result


# 相对价位 CKDP
def CKDP(chip_row, close):
    # 归一化
    chip_row = chip_row / sum(chip_row)
    # 0.1%持有量近似视为显著不为0
    chip_row = chip_row[chip_row > 0.001]
    highest = float(chip_row.index[-1])
    lowest = float(chip_row.index[0])
    result = safe_division(close - lowest, highest - lowest)

    return result


# 成本重心 CKDW
def CKDW(chip_row):
    # 归一化
    chip_row = chip_row / sum(chip_row)
    # 0.1%持有量近似视为显著不为0
    chip_row = chip_row[chip_row > 0.001]
    # 再次归一化
    chip_row = chip_row / sum(chip_row)

    highest = float(chip_row.index[-1])
    lowest = float(chip_row.index[0])

    weighted_average = sum([float(x) for x in chip_row.index] * chip_row)

    result = safe_division(weighted_average - lowest, highest - lowest)
    return result


# 成本带宽 CBW
def CBW(chip_row):
    # 归一化
    chip_row = chip_row / sum(chip_row)
    # 0.1%持有量近似视为显著不为0
    chip_row = chip_row[chip_row > 0.001]
    # 再次归一化
    chip_row = chip_row / sum(chip_row)

    highest = float(chip_row.index[-1])
    lowest = float(chip_row.index[0])
    result = safe_division(highest - lowest, lowest)

    return result


# 绘制筹码分布图
def chip_plot(chip_df, code, end, bin_width=0.1):
    plt.figure(figsize=(10, 6))
    plt.bar(chip_df.columns, chip_df.iloc[-1], width=bin_width, edgecolor='k')
    plt.xlabel('price')
    plt.ylabel('stack')
    plt.title(f'{code} CYQ: {end}')
    plt.show()

