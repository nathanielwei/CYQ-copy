# 计算筹码分布衍生指标
# 输出：存储在factors文件夹，每个因子为一个csv文件，x为时间，y为股票代码

import pandas as pd
import numpy as np
import main as Data
import util.FactorAPI as FactorAPI
from tqdm import tqdm
import tushare as ts
import os

pro = ts.pro_api("de54d694fac1733bfdf1147da469d799f48b0346937aecbd3cf8ad9e")

start = Data.start
end = Data.end
symbols = Data.symbols
# symbols = ["601360"]
cal_week = Data.cal_week
week_list = Data.week_list
stock_list = Data.stock_list
data_start = Data.data_start
data_end = Data.data_end
return_path = Data.return_path

if os.path.exists(os.path.join(return_path, f'week_close_{Data.index_code}.csv')):
    week_close = pd.read_csv(os.path.join(Data.return_path, f'week_close_{Data.index_code}.csv'), index_col=0)
else:
    # 每周收盘价数据
    week_close_dict = {}
    for symbol in tqdm(symbols, desc="Get close"):
        if '.' in symbol:
            code = symbol
        else:
            code = stock_list[stock_list["symbol"] == symbol]["ts_code"].values[0]

        week_close = ts.pro_bar(ts_code=code, freq='W', adj="qfq", start_date=start, end_date=end)
        week_close_dict[symbol] = pd.DataFrame(week_close[::-1]).set_index("trade_date")["close"]

    week_close = pd.DataFrame(week_close_dict).ffill()
    week_close.to_csv(os.path.join(Data.return_path, f'week_close_{Data.index_code}.csv'))

# 创建筹码因子dataframe
asr = pd.DataFrame(0, index=week_list, columns=symbols)
ckdp = pd.DataFrame(0, index=week_list, columns=symbols)
ckdw = pd.DataFrame(0, index=week_list, columns=symbols)
cbw = pd.DataFrame(0, index=week_list, columns=symbols)

# 读取计算得出的周频筹码分布
for k, symbol in enumerate(symbols):
    if '.' in symbol:
        code = symbol
    else:
        code = stock_list[stock_list["symbol"] == symbol]["ts_code"].values[0]
    df = pd.read_csv(os.path.join(Data.weekly_chips_path, f"{code}_week.csv"), index_col=0)
    df.index = pd.to_datetime(df.index).strftime("%Y%m%d")
    close = week_close[code]
    for i, (idx, row) in enumerate(df.iterrows()):
        try:
            # Ensure 'idx' is present in 'close' index
            if idx in close.index.astype(str):
                asr.loc[idx, symbol] = FactorAPI.ASR(row, close[int(idx)])
                ckdp.loc[idx, symbol] = FactorAPI.CKDP(row, close.loc[int(idx)])
                ckdw.loc[idx, symbol] = FactorAPI.CKDW(row)
                cbw.loc[idx, symbol] = FactorAPI.CBW(row)
            else:
                print(f"Date {idx} not found in close DataFrame index for symbol {symbol}.")
        except KeyError as e:
            print(f"KeyError: {e} for index {idx} and symbol {symbol}")
        except Exception as e:
            print(f"An unexpected error occurred: {e} for index {idx} and symbol {symbol}")

factor_list = [asr, ckdp, ckdw, cbw]
factor_names = ["asr", "ckdp", "ckdw", "cbw"]
for i in range(len(factor_list)):
    factor = factor_list[i]
    factor.replace(0, np.nan, inplace=True)
    factor_filled = factor.ffill().bfill()
    factor_filled.to_csv(os.path.join(Data.factor_path, f"{factor_names[i]}.csv"))
