# 因子有效性测试
# 1.读取股票涨跌幅
# 2.读取因子值
# 3.IC测试
# 输出/result/ic.csv，/result/ic_measures.csv

import pandas as pd
import numpy as np
import main as Data
import util.tools as tools
from tqdm import tqdm
import tushare as ts
import os

pro = ts.pro_api("de54d694fac1733bfdf1147da469d799f48b0346937aecbd3cf8ad9e")

start = Data.start
end = Data.end
symbols = Data.symbols
# symbols = ["601600"]
week_list = Data.week_list
factor_path = Data.factor_path
return_path = Data.return_path
result_path = r'../result'
if not os.path.exists(result_path):
    os.mkdir(result_path)

# 1.读取股票涨跌幅
return_df = pd.read_csv(os.path.join(return_path, f'pct_chg_{Data.index_code}.csv'), index_col=0)

# 2.读取因子值
# 3.计算RankIC

factor_dict = {}
ic_dict = {}
factor_names = os.listdir(factor_path)
factor_names = [x.split('.')[0] for x in factor_names]
for factor in tqdm(factor_names, desc='Factor'):
    factor_df = pd.read_csv(os.path.join(factor_path, f'{factor}.csv'), index_col=0)
    factor_df = factor_df.iloc[:-1]
    keys = ['fac', 'ret']
    merged_df = pd.concat([factor_df, return_df], axis=1, keys=keys)
    ic_list = merged_df.apply(lambda row: tools.calculate_ic(row, keys), axis=1)
    ic_dict[factor] = ic_list
    factor_dict[factor] = factor_df

ic_df = pd.DataFrame(ic_dict)

# 处理IC时序数列，计算统计指标
measures = ["mean", "max", "min", "std"]
result = np.zeros([len(measures), len(factor_names)])

for j, measure in enumerate(measures):
    for i, factor in enumerate(factor_names):
        result[i][j] = getattr(np, measure)(ic_df[factor])

result = pd.DataFrame(result, index=factor_names, columns=measures)
result["ir"] = result["mean"] / result["std"]

# 合成因子

mean_ic = result["mean"].values
selected_factors = [name for name, ic in zip(factor_names, mean_ic) if np.abs(ic) > 0.01]
weight = mean_ic[np.abs(mean_ic) > 0.01]
weight /= np.sum(np.abs(weight))

valid_ic_df = ic_df[selected_factors]
comb = np.sum(valid_ic_df * weight, axis=1)
ic_df["comb"] = comb
ic_df.to_csv(os.path.join(result_path, 'ic.csv'))

comb_result = np.zeros([len(measures)])
for i, measure in enumerate(measures):
    comb_result[i] = getattr(np, measure)(comb)

comb_result = pd.DataFrame(comb_result.reshape(1, 4), columns=measures, index=["comb"])
comb_result["ir"] = comb_result["mean"] / comb_result["std"]
comb_result = pd.concat([result, comb_result])
comb_result.to_csv(os.path.join(result_path, "ic_measures.csv"))
