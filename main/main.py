# 计算并输出筹码时序数据（周频）
# 输出：存储在weekly_chips文件夹，每只股票为一个csv文件，行(x)为时间，列(y)为股价
# 可视化筹码分布图

import sys
import numpy as np
import pandas as pd
import tushare as ts
import matplotlib.pyplot as plt
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import util.FactorAPI as FactorAPI
import time
import os
from tqdm import tqdm

# file_path
factor_path = r'../data/factors'
daily_chips_path = r'../data/daily_chips'
weekly_chips_path = r'../data/weekly_chips'
return_path = r'../data/return'
raw_data_path = r'../data/raw_data'  # 由ts.pro_bar获取的周频行情数据

pro = ts.pro_api("de54d694fac1733bfdf1147da469d799f48b0346937aecbd3cf8ad9e")

# 股票列表
stock_list = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')

# 设定测试区间(不轻易改，否则raw_data的数据要更新)
start = "20170531"
end = "20240531"  # 填周五/六/日
data_start = (dt.strptime(start, "%Y%m%d") - relativedelta(months=4)).strftime("%Y%m%d")
data_end = end

# 指数：000044.SH 上证中盘，000045.SH 上证小盘, 000046.SH 上证中小盘，000905.SH中证500，000300.SH沪深300
index_code = 'all'

# 按指数选股票池
symbols = pro.index_weight(index_code=index_code, start_date="20240501", end_date="20240601")["con_code"].unique()
# symbols = symbols[:100]  # 阉割版
symbols = [x for x in symbols if (stock_list[stock_list["ts_code"] == x]["list_date"] < data_start).any()]

# 单独选股
# symbols = ['002714.SZ']

# 文件夹内所有股票
# symbols = os.listdir(weekly_chips_path)
# symbols = [x.split("_")[0] for x in symbols]
# symbols = [x for x in symbols if x != '.DS']

# 交易日历(index: 每周周日，value: 每周最后一个交易日)
cal = pro.trade_cal(exchange="", start_date=start, end_date=end)
cal_date = cal[cal["is_open"] == 1]["cal_date"]
cal_date = pd.DataFrame(cal_date[::-1])
cal_date.index = pd.to_datetime(cal_date["cal_date"])
# 每周最后一个交易日
cal_week = cal_date.groupby(pd.Grouper(freq='W')).apply(lambda x: x.index.max())
cal_week = cal_week[pd.notna(cal_week)]
cal_week.name = "cal_week"
day_list = [x for x in cal_date.to_numpy().flatten()]
week_list = [x.strftime("%Y%m%d") for x in cal_week]


if __name__ == '__main__':

    # raw_data文件夹中存储的symbols
    exist_symbols = os.listdir(raw_data_path)
    exist_symbols = [x.rsplit(".", 1)[0] for x in exist_symbols]  # with market sign
    for symbol in tqdm(symbols, desc="Data"):   # symbol with market sign
        try:
            if symbol in exist_symbols:
                continue
            if '.' in symbol:
                code = symbol
            else:
                code = stock_list[stock_list["symbol"] == symbol]["ts_code"].values[0]

            raw_data = ts.pro_bar(ts_code=code, adj='qfq', freq='D', start_date=data_start, end_date=data_end)
            basic = pro.daily_basic(ts_code=code, start_date=data_start, end_date=data_end)

            # 退市则没有数据
            if raw_data is None:
                print(f"{symbol} not found")
                continue

            raw_data["turnover"] = basic["turnover_rate_f"] * 0.01  # 百分数
            raw_data["free_share"] = basic["free_share"]  # 万股
            raw_data = raw_data[::-1]
            raw_data = raw_data.ffill()
            raw_data.set_index("trade_date", inplace=True)
            raw_data.to_csv(os.path.join(raw_data_path, f'{symbol}.csv'))

        except IndexError:
            print(f"IndexError: {symbol} code not found in stock list.")
        except KeyError:
            print(f"KeyError: Missing data for {symbol}.")
        except Exception as e:
            print(f"An error occurred with {symbol}: {e}")

    # 提前获取数据
    raw_data_dict = {}
    for symbol in tqdm(symbols, desc="Reading"):    # symbol with market sign
        raw_data = pd.read_csv(os.path.join(raw_data_path, f'{symbol}.csv'))
        raw_data_dict[symbol] = raw_data

    # 创建周频筹码字典
    week_chip_dict = {}

    # daily_chips文件夹中存储的symbols
    exist_chips_symbols = os.listdir(daily_chips_path)
    exist_chips_symbols = [x.split("_")[0] for x in exist_chips_symbols]   # 命名格式为 600415.SH_chip.csv
    for k, symbol in enumerate(tqdm(symbols, desc="Daily chips")):
        try:
            if symbol in exist_chips_symbols:
                continue

            # 调用数据
            raw_data = raw_data_dict.get(symbol)

            # 已退市则数据为空
            if raw_data.empty or raw_data is None:
                print("数据为空")
                continue

            # 确定价格区间(前复权)
            price_min = raw_data['low'].min()
            price_max = raw_data['high'].max()

            # 初始化时序筹码分布
            if price_max - price_min > 5:
                bin_width = 0.1
            else:
                bin_width = 0.01

            price_bins = np.arange(price_min, price_max + bin_width, bin_width)
            chip_df = pd.DataFrame(0, columns=price_bins[:-1], index=raw_data['trade_date'])

            # 初始化截面筹码分布
            chip_distribution = np.zeros(len(price_bins) - 1)

            # 昨日总自由流通股本
            C0 = raw_data.iloc[0]["free_share"]
            low_prices = raw_data['low'].values
            high_prices = raw_data['high'].values
            free_shares = raw_data['free_share'].values
            turnovers = raw_data['turnover'].values

            for j in range(len(raw_data)):
                try:
                    # 今日总自由流通股本，成交量
                    C1 = free_shares[j]
                    vol = int(raw_data.iloc[j]["vol"])

                    # 今日股价波动范围
                    today_price_range = np.linspace(low_prices[j], high_prices[j], num=vol)

                    # 假设交易量均匀分布
                    hist, _ = np.histogram(today_price_range, bins=price_bins)

                    # 移入筹码
                    chip_distribution += hist

                    # 移出筹码（假设等比例）
                    chip_distribution /= (C0 / C1 + turnovers[j])

                    # 更新昨日总自由流通股本
                    C0 = C1

                    # 存入筹码分布
                    chip_df.iloc[j] = chip_distribution
                    sys.stdout.write(f"\rSymbol: {symbol} {k + 1}/{len(symbols)}, date {j + 1}/{len(raw_data)}")
                except Exception as e:
                    print(f"Error processing data for {symbol} on date index {j}: {e}")

            chip_df = chip_df.loc[start:end]
            chip_df.to_csv(os.path.join(daily_chips_path, f"{symbol}_chip.csv"))
            # FactorAPI.chip_plot(chip_df, symbol, end)

        except Exception as e:
            print(f"Error processing symbol {symbol}: {e}")

    # weekly_chips文件夹中存储的symbols
    exist_weekly_chips_symbols = os.listdir(weekly_chips_path)
    exist_weekly_chips_symbols = [x.split("_")[0] for x in exist_weekly_chips_symbols]  # 命名格式为 600415.SH_week.csv
    for k, symbol in enumerate(tqdm(symbols, desc="Weekly chips")):
        if symbol in exist_weekly_chips_symbols:
            continue

        chip_df = pd.read_csv(os.path.join(daily_chips_path, f"{symbol}_chip.csv"))
        chip_df['trade_date'] = chip_df['trade_date'].astype(str)
        chip_df['trade_date'] = pd.to_datetime(chip_df['trade_date'], format='%Y%m%d')
        chip_df.set_index('trade_date', inplace=True)
        # 将日频筹码按周加和
        week_chip = chip_df.groupby(pd.Grouper(freq='W')).sum()
        week_chip = week_chip.join(cal_week)
        week_chip.set_index("cal_week", inplace=True)
        week_chip = week_chip[pd.notna(week_chip.index)]
        week_chip = week_chip.loc[start:end]
        # FactorAPI.chip_plot(week_chip, symbol, end)
        week_chip.to_csv(os.path.join(weekly_chips_path, f"{symbol}_week.csv"))
