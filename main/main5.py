# 构建投资组合

import pandas as pd
import numpy as np
import util.tools as tools
import matplotlib.pyplot as plt
import main4 as ic

factor_dict = ic.factor_dict
comb_df = pd.DataFrame(0, index=ic.week_list, columns=ic.symbols)[:-1]

for i, factor in enumerate(ic.selected_factors):
    factor_df = factor_dict[factor]
    comb_df += (ic.weight[i] * factor_df).values

selected_stock = comb_df.apply(tools.top_stock, axis=1)
return_df = ic.return_df
return_series = np.mean(return_df.values * selected_stock.values, axis=1)
return_series = np.cumprod(1+return_series)
x = ic.week_list[1:]

random_stock = comb_df.apply(tools.random_select, axis=1)
random_series = np.mean(return_df.values * random_stock.values, axis=1)
random_series = np.cumprod(1+random_series)

plt.figure(figsize=(10, 5))
plt.plot(x, return_series, label="top")
plt.plot(x, random_series, label="random")
plt.xticks(x[::25], rotation=30)
plt.title('CYQ Strategy')
plt.xlabel('Date')
plt.ylabel('Return')
plt.legend()
plt.tight_layout()
plt.show()

