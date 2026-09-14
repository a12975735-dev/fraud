import pandas as pd
MAX_TRAIN=200000
train=pd.read_csv('data/processed/train.csv')
print('orig cols:', list(train.columns))
print('orig shape:', train.shape)
print('isFraud present:', 'isFraud' in train.columns)
label_col=None
for c in train.columns:
    if ''.join(ch for ch in str(c).lower() if ch.isalnum()) in ('isfraud','fraud'):
        label_col=c
        break
print('detected label_col:', label_col)
if len(train)>MAX_TRAIN:
    sampled = train.groupby(label_col, group_keys=False).apply(lambda x: x.sample(n=max(1,int(MAX_TRAIN*len(x)/len(train))), random_state=42)).reset_index(drop=True)
    print('sampled cols:', list(sampled.columns))
    print('sampled shape:', sampled.shape)
else:
    print('no sampling; len<=MAX_TRAIN')
print('done')
