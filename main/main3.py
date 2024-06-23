# 获取股票涨跌幅
# 输出 /return/pct_chg.csv

import pandas as pd
import main as Data
from tqdm import tqdm
import tushare as ts
import os

pro = ts.pro_api("de54d694fac1733bfdf1147da469d799f48b0346937aecbd3cf8ad9e")

start = Data.start
end = Data.end
symbols = Data.symbols
# symbols = ["601600"]
stock_list = Data.stock_list
week_list = Data.week_list
return_path = Data.return_path

if not os.path.exists(os.path.join(return_path, f'pct_chg_{Data.index_code}.csv')):

    # 存储股票涨跌幅
    stock_return = pd.DataFrame(0, columns=symbols, index=week_list)

    # stock return of this period
    for symbol in tqdm(symbols, desc="Symbol"):
        if '.' in symbol:
            code = symbol
        else:
            code = stock_list[stock_list["symbol"] == symbol]["ts_code"].values[0]
        df = ts.pro_bar(ts_code=code, freq='W', start_date=start, end_date=end)
        df = pd.DataFrame(df[::-1]).set_index("trade_date")["pct_chg"]

        # 股票出现停牌，df长度与测试区间长度不符(reindex)
        aligned_series = df.reindex(stock_return.index, fill_value=0)
        stock_return.loc[:, symbol] = aligned_series

    # stock return of next period
    shift_return = stock_return.shift(-1)
    shift_return.dropna(how="all", inplace=True)
    shift_return.to_csv(os.path.join(return_path, f'pct_chg_{Data.index_code}.csv'))
