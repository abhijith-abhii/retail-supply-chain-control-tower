import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import precision_score,recall_score,f1_score,roc_auc_score,average_precision_score,confusion_matrix

def delivery_risk(delivery,seed=42):
    x=delivery[delivery.delivery_eligible].sort_values(['order_date','order_id']).copy()
    dates=sorted(x.order_date.unique());cut=dates[int(.8*len(dates))]
    train=x[x.order_date<cut];test=x[x.order_date>=cut]
    if train.late_order.nunique()<2 or test.late_order.nunique()<2: raise ValueError('Risk model requires both outcomes in both time partitions')
    cats=['shipping_mode','market','region','customer_segment'];numeric=['scheduled_shipping_days']
    features=cats+numeric
    prep=lambda:ColumnTransformer([('cats',OneHotEncoder(handle_unknown='ignore'),cats),('num',make_pipeline(SimpleImputer(),StandardScaler()),numeric)])
    models={'logistic_regression':LogisticRegression(solver='liblinear',max_iter=1000,class_weight='balanced',random_state=seed),
     'decision_tree':DecisionTreeClassifier(max_depth=5,class_weight='balanced',random_state=seed),
     'random_forest':RandomForestClassifier(n_estimators=100,max_depth=8,class_weight='balanced',random_state=seed,n_jobs=2),
     'lightgbm':LGBMClassifier(n_estimators=100,class_weight='balanced',random_state=seed,n_jobs=2,verbosity=-1)}
    rows=[];importance=[]
    for name,m in models.items():
        pipe=make_pipeline(prep(),m);pipe.fit(train[features],train.late_order.astype(int))
        p=pipe.predict_proba(test[features])[:,1]
        if not np.isfinite(p).all(): raise ValueError('Non-finite delivery-risk predictions: '+name)
        pred=(p>=.5).astype(int);y=test.late_order.astype(int)
        tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
        rows.append(dict(model=name,precision=precision_score(y,pred,zero_division=0),recall=recall_score(y,pred),f1=f1_score(y,pred),roc_auc=roc_auc_score(y,p),pr_auc=average_precision_score(y,p),tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp),threshold=.5))
        vals=m.coef_[0] if hasattr(m,'coef_') else m.feature_importances_
        importance.extend(dict(model=name,feature=f,importance=float(v)) for f,v in zip(pipe.steps[0][1].get_feature_names_out(),vals))
    return pd.DataFrame(rows),pd.DataFrame(importance)
