import numpy as np
MODELS=['naive','seasonal_7','seasonal_28','moving_average','lightgbm']
def baseline(y, horizon, name):
    y=np.asarray(y,dtype=float)
    if name=='naive': return np.repeat(y[-1],horizon)
    if name=='moving_average': return np.repeat(y[-28:].mean(),horizon)
    period=int(name.split('_')[1])
    return np.resize(y[-period:],horizon)
