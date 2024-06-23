import numpy as np
from scipy.stats import spearmanr


# 计算两行数据的秩相关系数
def calculate_ic(row, keys):
    x = row[keys[0]]
    y = row[keys[1]]
    corr, _ = spearmanr(x, y)
    return corr


# 筛选每行最大的几个值
def top_stock(row, n=20):
    # 取出前 n 个最大的数的索引
    top_n_indices = row.nlargest(n).index
    # 将这些位置设置为 1，其他位置设置为 0
    row[:] = 0
    row[top_n_indices] = 1
    return row


def random_select(row, n=20):
    random_indices = np.random.choice(row.index, size=n, replace=False)
    row[:] = 0
    row[random_indices] = 1
    return row
