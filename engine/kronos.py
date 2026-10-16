"""Argon v2's own Kronos (Kronos-small, 24.7M parameters, CPU). Forecasts the next hour for each market from the
latest 5-minute candles and writes data/kronos.json, which the desk bots read before every call.
Model: NeoQuasar/Kronos-small on Hugging Face; code from github.com/shiyu-coder/Kronos (MIT)."""
import os,sys,json,datetime as dt
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(ROOT,'vendor','Kronos'))
import pandas as pd
from model import Kronos, KronosTokenizer, KronosPredictor
tok=KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base"); mdl=Kronos.from_pretrained("NeoQuasar/Kronos-small")
pred=KronosPredictor(mdl,tok,device="cpu",max_context=512)
OUT={}; PRED_LEN=12   # 12 five-minute candles = the next hour
for s in ('NQ','ES','YM','RTY'):
    r=json.load(open(os.path.join(ROOT,'data','futures',f'{s}F.json')))['chart']['result'][0]; q=r['indicators']['quote'][0]
    rows=[(t,q['open'][i],q['high'][i],q['low'][i],q['close'][i],q['volume'][i] or 0) for i,t in enumerate(r['timestamp']) if None not in (q['open'][i],q['high'][i],q['low'][i],q['close'][i])][-400:]
    df=pd.DataFrame(rows,columns=['ts','open','high','low','close','volume']); df['amount']=df['close']*df['volume']
    xt=pd.to_datetime(df['ts'],unit='s'); yt=pd.Series(pd.date_range(xt.iloc[-1]+pd.Timedelta(minutes=5),periods=PRED_LEN,freq='5min'))
    paths=[pred.predict(df=df[['open','high','low','close','volume','amount']],x_timestamp=xt,y_timestamp=yt,pred_len=PRED_LEN,T=1.0,top_p=0.9,sample_count=1) for _ in range(5)]
    last=df['close'].iloc[-1]; ends=[p['close'].iloc[-1] for p in paths]; up=sum(1 for e in ends if e>last)
    OUT[s]=dict(direction='up' if up>=3 else 'down',confidence=round(max(up,5-up)/5,2),horizon='1h',expected_move=round(sum(ends)/5-last,2),updated=dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%MZ'),model='Kronos-small')
json.dump(OUT,open(os.path.join(ROOT,'data','kronos.json'),'w'),indent=1); print(OUT)
