import numpy as np

def rmsse_scale(y):
    y=np.asarray(y,dtype=float);nz=np.flatnonzero(y)
    if len(nz)==0: return np.nan
    y=y[nz[0]:]
    return float(np.mean(np.diff(y)**2)) if len(y)>1 and np.any(np.diff(y)) else np.nan

def metrics(actual,pred,scales=None):
    y=np.asarray(actual,float);p=np.asarray(pred,float);e=p-y
    total=y.sum();valid=y!=0
    result={'mae':float(np.abs(e).mean()),'rmse':float(np.sqrt(np.mean(e**2))),
     'wape':float(np.abs(e).sum()/total) if total else np.nan,
     'mape':float(np.mean(np.abs(e[valid]/y[valid]))) if valid.any() else np.nan,
     'bias':float(e.sum()/total) if total else np.nan,'rmsse':np.nan}
    if scales is not None:
        s=np.asarray(scales,float);v=np.isfinite(s)&(s>0)
        if v.any(): result['rmsse']=float(np.sqrt(np.mean(e[v]**2/s[v])))
    return result
