import pandas as pd
import pathlib as path

BASE_DIR=path.Path(__file__).resolve().parent.parent.parent
DATA_PATH=BASE_DIR/"media"/"ProcessedData.csv"
df=pd.read_csv(DATA_PATH)
# Checking out data types of each column and dividing them into categorical and numerical columns

print(df.dtypes)
categorical_cols=["preciptype","stations","icon","conditions"]
numeric_cols = [c for c in df.columns if c not in categorical_cols]
print(df[numeric_cols].corr())
print(df["generation"].describe())
import plotly.express as px
fig=px.histogram(df, x="generation", nbins=50, title="Generation Distribution")

fig.update_layout(bargap=0.1)
fig.show()
#approach
# 1. Understanding relationship between target and numeric features using correlation and scatter plots
# 2. Understanding relationship between target and categorical features using box plots and violin plots
# 3. If categorical features look important to the target we will do one hot encoding for that.
# (if there is only two possible values we can do binary encoding)
# 4. Plot the difference after encoding to see if there is any improvement in correlation
# 5. After all these steps we will standardize the numeric features using StandardScaler from sklearn so that weight is high for the most
#  affecting feature that affects the target the most.
# 6. Now whenever we get a new data point we will do the same transformations on that data point before feeding it to the model.