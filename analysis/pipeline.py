import json
BASE="/tmp/claude-0/-home-user-Claude/acfda38c-f805-5d0e-9f01-51d2c4d57305/scratchpad/"
TR="/root/.claude/projects/-home-user-Claude/acfda38c-f805-5d0e-9f01-51d2c4d57305/tool-results/"
files=[TR+"mcp-Webull-get_stock_bars-1789842145121.txt", TR+"mcp-Webull-get_stock_bars-1789853923006.txt", TR+"mcp-Webull-get_stock_bars-1789856168811.txt"]

def load_bars():
    out={}
    for f in files:
        d=json.loads(open(f).read())["result"]
        for it in d: out[it["symbol"]]=it["result"]  # newest-first
    return out
BARS=load_bars()

def sma(x,n): return sum(x[:n])/n if len(x)>=n else (sum(x)/len(x) if x else None)
def rsi(co,n=14):
    if len(co)<n+1: return None
    g=[];l=[]
    for i in range(1,len(co)):
        c=co[i]-co[i-1]; g.append(max(c,0)); l.append(max(-c,0))
    ag=sum(g[:n])/n; al=sum(l[:n])/n
    for i in range(n,len(g)):
        ag=(ag*(n-1)+g[i])/n; al=(al*(n-1)+l[i])/n
    if al==0: return 100.0
    return 100-100/(1+ag/al)
def stdev(x):
    if len(x)<2: return 0
    m=sum(x)/len(x); return (sum((v-m)**2 for v in x)/len(x))**.5

def atr(bars,n=14):
    # bars newest-first
    b=bars[:n+1]
    if len(b)<2: return None
    trs=[]
    for i in range(len(b)-1):
        h=float(b[i]["high"]);lo=float(b[i]["low"]);pc=float(b[i+1]["close"])
        trs.append(max(h-lo,abs(h-pc),abs(lo-pc)))
    return sum(trs)/len(trs)

tech={}
for sym,bars in BARS.items():
    cn=[float(b["close"]) for b in bars]  # newest-first
    n=len(cn); price=cn[0]
    def ret(k): return (price/cn[k]-1)*100 if n>k else None
    r21=ret(21); r63=ret(63) if n>63 else ret(n-1)
    s20=sma(cn,20); s50=sma(cn,50)
    co=cn[::-1]
    dr=[cn[i]/cn[i+1]-1 for i in range(min(20,n-1))]
    a=atr(bars,14)
    tech[sym]=dict(price=round(price,2),r21=round(r21,1) if r21 is not None else 0,
      r63=round(r63,1) if r63 is not None else 0,
      sma20=round(s20,2) if s20 else price, sma50=round(s50,2) if s50 else price,
      px20=round((price/s20-1)*100,1) if s20 else 0, px50=round((price/s50-1)*100,1) if s50 else 0,
      rsi=round(rsi(co,14),1) if rsi(co,14) is not None else 50,
      vol=round(stdev(dr)*(252**.5)*100,1), atr=round(a,3) if a else round(price*0.03,3),
      bars=n)

# ---- fundamentals / snapshot (all 24) ----
snap={
 "NVDA":dict(pe=28.10,ps=17.72,eps=7.91,yld=0.45,hi=236.00,lo=163.90,mcap=5356.7,sec="Semis",name="NVIDIA"),
 "AMD":dict(pe=143.6,ps=22.12,eps=3.90,yld=0.0,hi=584.73,lo=149.85,mcap=913.9,sec="Semis",name="Advanced Micro Devices"),
 "INTC":dict(pe=-51.2,ps=9.60,eps=-2.12,yld=0.0,hi=142.35,lo=24.22,mcap=574.0,sec="Semis",name="Intel"),
 "MU":dict(pe=23.0,ps=12.70,eps=44.17,yld=0.06,hi=1254.81,lo=154.40,mcap=1147.2,sec="Semis",name="Micron"),
 "TSM":dict(pe=31.68,ps=16.06,eps=13.72,yld=0.94,hi=463.97,lo=264.08,mcap=2254.4,sec="Semis",name="Taiwan Semi (TSMC)"),
 "AVGO":dict(pe=45.65,ps=19.16,eps=7.83,yld=0.73,hi=494.22,lo=289.50,mcap=1707.1,sec="Semis",name="Broadcom"),
 "META":dict(pe=25.07,ps=7.43,eps=26.56,yld=0.32,hi=788.22,lo=519.78,mcap=1696.0,sec="Mega Tech",name="Meta Platforms"),
 "GOOGL":dict(pe=17.56,ps=9.59,eps=19.90,yld=0.25,hi=408.10,lo=235.23,mcap=4274.9,sec="Mega Tech",name="Alphabet"),
 "AAPL":dict(pe=38.53,ps=10.52,eps=8.72,yld=0.32,hi=344.27,lo=234.16,mcap=4905.5,sec="Mega Tech",name="Apple"),
 "ORCL":dict(pe=23.14,ps=6.22,eps=6.38,yld=1.35,hi=325.79,lo=114.50,mcap=446.3,sec="Mega Tech",name="Oracle"),
 "PLTR":dict(pe=151.4,ps=69.34,eps=1.17,yld=0.0,hi=207.52,lo=106.37,mcap=426.9,sec="Mega Tech",name="Palantir"),
 "TSLA":dict(pe=338.4,ps=13.88,eps=1.08,yld=0.0,hi=498.83,lo=297.38,mcap=1438.7,sec="Mega Tech",name="Tesla"),
 "SMTC":dict(pe=109.4,ps=14.68,eps=1.69,yld=0.0,hi=185.46,lo=57.50,mcap=17.3,sec="Semis",name="Semtech"),
 "TWST":dict(pe=-75.1,ps=24.24,eps=-2.22,yld=0.0,hi=167.05,lo=23.30,mcap=11.0,sec="Biotech",name="Twist Bioscience"),
 "HAFN":dict(pe=7.76,ps=1.90,eps=1.30,yld=10.98,hi=10.12,lo=4.49,mcap=5.06,sec="Shipping",name="Hafnia"),
 "TRMD":dict(pe=6.30,ps=2.22,eps=6.07,yld=11.56,hi=38.73,lo=18.35,mcap=3.92,sec="Shipping",name="Torm"),
 # new mid-caps
 "CVI":dict(pe=78.2,ps=0.64,eps=0.69,yld=0.75,hi=54.64,lo=19.50,mcap=5.40,sec="Energia",name="CVR Energy"),
 "SDGR":dict(pe=-39.4,ps=8.38,eps=-0.74,yld=0.0,hi=30.41,lo=10.95,mcap=2.17,sec="Health/IA",name="Schrödinger"),
 "SMMT":dict(pe=-15.9,ps=None,eps=-1.12,yld=0.0,hi=29.23,lo=12.07,mcap=14.24,sec="Biotech",name="Summit Therapeutics"),
 "ODD":dict(pe=76.0,ps=1.54,eps=0.24,yld=0.0,hi=64.23,lo=9.25,mcap=0.835,sec="Consumo",name="Oddity Tech"),
 "FRNM":dict(pe=-248,ps=15.0,eps=-0.069,yld=0.0,hi=17.255,lo=9.95,mcap=1.84,sec="Diagnóstico",name="Freenome"),
 "SECZ":dict(pe=108.9,ps=None,eps=0.10,yld=0.0,hi=14.05,lo=5.14,mcap=1.77,sec="Fintech",name="Securitize"),
 "ASST":dict(pe=-1.71,ps=290,eps=-17.6,yld=0.0,hi=157.8,lo=7.02,mcap=2.86,sec="Gestão/Cripto",name="Strive"),
 "PURR":dict(pe=None,ps=None,eps=-1.0,yld=0.0,hi=14.47,lo=3.01,mcap=2.79,sec="Cripto",name="Hyperliquid Strat."),
 # wave 3: mid-caps + quality small-caps
 "HALO":dict(pe=33.6,ps=7.71,eps=3.35,yld=0.0,hi=112.66,lo=61.23,mcap=12.76,sec="Biopharma",name="Halozyme"),
 "DBX":dict(pe=16.33,ps=3.17,eps=2.23,yld=0.0,hi=38.17,lo=21.70,mcap=8.23,sec="Software",name="Dropbox"),
 "OSCR":dict(pe=23.46,ps=0.65,eps=1.37,yld=0.0,hi=34.48,lo=10.69,mcap=9.92,sec="Health Insur.",name="Oscar Health"),
 "TXG":dict(pe=-129.9,ps=16.18,eps=-0.59,yld=0.0,hi=79.94,lo=11.16,mcap=9.98,sec="Life Sciences",name="10x Genomics"),
 "IOVA":dict(pe=-14.2,ps=14.29,eps=-0.72,yld=0.0,hi=10.98,lo=1.76,mcap=4.64,sec="Biotech",name="Iovance"),
 "PBF":dict(pe=6.86,ps=0.27,eps=11.26,yld=1.43,hi=82.61,lo=25.16,mcap=9.15,sec="Energia",name="PBF Energy"),
 "MG":dict(pe=24.86,ps=0.89,eps=0.83,yld=0.0,hi=21.32,lo=9.35,mcap=0.66,sec="Industrial",name="Mistras Group"),
 "INFU":dict(pe=31.46,ps=1.79,eps=0.41,yld=0.0,hi=13.15,lo=7.29,mcap=0.256,sec="Saúde (micro)",name="InfuSystem"),
}
tgt={"NVDA":327.7,"AMD":616.5,"INTC":116.37,"MU":1513.1,"TSM":552.26,"AVGO":531.85,"META":755.28,
 "GOOGL":428.16,"AAPL":328.22,"ORCL":237.97,"PLTR":196.84,"TSLA":396.94,"SMTC":209.29,"TWST":109.58,"HAFN":10.25,"TRMD":36.5,
 "CVI":33.4,"SDGR":21.43,"SMMT":27.2,"ODD":14.93,"FRNM":18.0,"SECZ":11.8,"ASST":29.4,"PURR":22.3,
 "HALO":99.56,"DBX":32.6,"OSCR":35.4,"TXG":52.13,"IOVA":10.22,"PBF":72.54,"MG":23.0,"INFU":16.83}  # SMMT converted GBP->USD
rat={"NVDA":(48,11,2,1,0,62),"AMD":(39,5,11,0,0,55),"INTC":(14,1,32,1,1,49),"MU":(36,9,4,0,0,49),
 "TSM":(14,6,1,0,0,21),"AVGO":(40,7,3,0,0,50),"META":(47,9,6,0,0,62),"GOOGL":(43,13,5,0,0,61),
 "AAPL":(19,6,13,3,3,44),"ORCL":(27,8,7,1,0,43),"PLTR":(20,1,9,1,1,32),"TSLA":(15,4,20,2,2,43),
 "SMTC":(13,1,1,0,0,15),"TWST":(7,2,3,1,0,13),"HAFN":(1,0,1,0,0,2),"TRMD":(1,0,1,0,0,2),
 "CVI":(0,0,2,3,1,6),"SDGR":(5,0,2,0,0,7),"SMMT":(10,1,6,0,0,17),"ODD":(0,0,7,1,2,10),
 "FRNM":(5,0,0,0,0,5),"SECZ":(3,2,0,0,0,5),"ASST":(4,1,0,0,0,5),"PURR":(3,1,0,0,0,4),
 "HALO":(5,2,2,0,0,9),"DBX":(0,1,4,1,1,7),"OSCR":(0,3,7,0,1,11),"TXG":(5,1,12,0,0,18),
 "IOVA":(5,2,2,0,0,9),"PBF":(1,0,9,3,1,14),"MG":(1,0,0,0,0,1),"INFU":(3,0,0,0,0,3)}
cf={
 "NVDA":[(914.7,707.7,1419.2,1338.6),(733.1,722.5,1275.9,1201.8),(3972.6,1167.4,1436.6,1366.5)],
 "AMD":[(466.9,398.1,933.0,873.3),(1980.8,531.9,1215.6,1206.4),(1395.2,427.7,678.2,723.4)],
 "INTC":[(380.4,443.2,588.3,619.3),(2394.7,580.5,828.0,773.5),(976.4,290.4,540.7,532.4)],
 "MU":[(657.6,744.9,1046.8,1111.0),(2862.4,576.3,1132.3,1045.3),(2299.7,1557.3,1430.6,1353.6)],
 "TSM":[(323.9,71.3,80.6,115.8),(206.8,61.1,112.2,102.4),(120.7,71.2,71.8,72.3)],
 "AVGO":[(243.1,201.0,266.9,285.6),(139.2,177.4,276.5,310.1),(1139.8,346.8,326.5,291.5)],
 "META":[(509.5,246.4,419.4,338.2),(359.2,1909.7,337.1,393.1),(1453.2,646.4,489.9,434.2)],
 "GOOGL":[(1501.5,247.0,240.1,220.2),(131.8,114.9,193.1,244.7),(5486.2,460.8,431.9,411.4)],
 "AAPL":[(295.6,3090.4,336.0,505.4),(455.0,278.8,368.5,380.8),(13355.4,386.3,450.6,554.2)],
 "ORCL":[(139.1,104.0,96.0,91.2),(44.3,50.8,90.4,90.6),(58.8,101.7,65.6,74.6)],
 "PLTR":[(104.3,105.2,180.0,183.8),(541.3,83.1,171.9,169.4),(512.9,70.4,141.7,159.0)],
 "TSLA":[(317.9,275.6,533.8,514.4),(1456.4,437.7,586.5,593.1),(4037.1,426.9,705.3,764.2)],
 "SMTC":[(21.5,23.9,32.1,36.7),(32.3,20.1,28.0,27.4),(15.1,24.3,39.1,60.1)],
 "TWST":[(4.1,7.6,10.6,14.5),(9.0,10.6,22.6,21.5),(4.3,5.7,13.4,14.2)],
 "HAFN":[(0.1,0.097,0.338,0.126),(0.301,0.0,0.189,0.349),(0.0,0.099,0.260,0.191)],
 "TRMD":[(2.5,3.2,5.5,5.4),(0.57,1.1,1.3,2.2),(1.4,4.3,4.6,4.6)],
 "CVI":[(1.19,0.134,1.145,0.731),(0.551,0.130,0.384,0.867),(0.0,0.352,0.369,0.583)],
 "SDGR":[(1.856,0.795,2.392,1.807),(10.208,4.290,10.504,7.770),(2.532,3.209,4.671,5.388)],
 "SMMT":[(2.229,2.988,0.949,1.668),(2.056,2.811,2.700,3.633),(0.538,157.177,1.797,3.722)],
 "ODD":[(0.232,0.497,0.600,0.575),(0.876,0.551,1.211,0.518),(0.123,0.312,0.705,0.733)],
 "FRNM":[(0.034,0.0,0.066,0.121),(0.032,1.579,0.526,0.817),(0.622,0.770,1.116,0.296)],
 "SECZ":[(0.373,0.495,0.286,0.581),(0.950,0.904,1.146,1.307),(2.904,4.020,2.544,1.548)],
 "ASST":[(14.304,11.541,10.313,10.084),(17.916,15.421,11.326,13.170),(20.586,19.027,17.694,18.037)],
 "PURR":[(6.930,6.717,8.651,7.237),(31.627,14.104,17.533,13.627),(16.421,16.782,23.518,22.782)],
 "HALO":[(5.593,7.507,6.860,5.040),(2.823,3.116,7.317,6.567),(52.211,56.102,14.603,12.139)],
 "DBX":[(1.305,0.787,3.011,4.307),(5.857,0.757,3.576,2.532),(0.594,1.961,2.765,4.130)],
 "OSCR":[(2.339,5.023,2.579,2.397),(1.350,0.824,2.064,2.676),(0.868,1.714,2.584,2.309)],
 "TXG":[(4.186,5.763,6.429,11.145),(3.720,5.795,6.235,9.302),(0.333,1.102,4.358,6.606)],
 "IOVA":[(6.597,16.100,7.261,7.889),(9.825,6.297,7.126,7.752),(5.659,4.089,4.359,5.420)],
 "PBF":[(4.514,8.640,4.998,7.391),(1.528,5.045,4.061,3.762),(4.165,2.540,4.626,3.446)],
 "MG":[(0.0,0.0,0.030,0.073),(0.051,0.212,0.307,0.234),(0.175,1.380,0.665,1.007)],
 "INFU":[(0.016,0.107,0.022,0.024),(0.118,0.019,0.009,0.020),(0.0,0.014,0.068,0.056)],
}
gbp_flag={"SMMT"}  # target converted

syms=list(snap.keys())
rows={}
for s in syms:
    t=tech[s]; sp=snap[s]; price=t["price"]
    up=(tgt[s]/price-1)*100
    sb,b,h,sell,un,num=rat[s]
    bull=(sb+0.5*b-0.5*sell-un)/num
    net=sum((d[0]-d[1])+(d[2]-d[3]) for d in cf[s])
    netr=net/(sp["mcap"]*1000)
    dist_hi=(price/sp["hi"]-1)*100
    rows[s]=dict(price=price,r21=t["r21"],r63=t["r63"],px20=t["px20"],px50=t["px50"],rsi=t["rsi"],
      vol=t["vol"],atr=t["atr"],upside=up,bull=bull,net=net,netr=netr,disthi=dist_hi,
      pe=sp["pe"],ps=sp["ps"],eps=sp["eps"],yld=sp["yld"],mcap=sp["mcap"],sec=sp["sec"],name=sp["name"],
      sma20=t["sma20"],sma50=t["sma50"],bars=t["bars"])

def z(vals):
    m=sum(vals)/len(vals); sd=stdev(vals) or 1
    return [(v-m)/sd for v in vals]
def zmap(key):
    zz=z([rows[s][key] for s in syms]); return {s:zz[i] for i,s in enumerate(syms)}
zr21=zmap("r21");zr63=zmap("r63");zpx50=zmap("px50");zpx20=zmap("px20");zup=zmap("upside");zbull=zmap("bull");znf=zmap("netr")
def rsi_score(r):
    if r>=78: return -1.5-(r-78)*0.05
    if r>=50: return 1.0-abs(r-61)/15.0
    return (r-50)/12.0
zr=z([rsi_score(rows[s]["rsi"]) for s in syms]); zrsi={s:zr[i] for i,s in enumerate(syms)}
def valq(s):
    r=rows[s];sc=0
    if r["eps"] is None or r["eps"]<0: sc-=1.0
    else: sc+=0.3
    if r["ps"] is not None:
        if r["ps"]>30: sc-=1.2
        elif r["ps"]>15: sc-=0.5
    if r["pe"] is not None and 0<r["pe"]<30: sc+=0.5
    return sc
zv=z([valq(s) for s in syms]); zvq={s:zv[i] for i,s in enumerate(syms)}

W={"mom":0.35,"tech":0.25,"flow":0.15,"anal":0.20,"valq":0.05}
comp={};blocks={}
for s in syms:
    mom=0.45*zr21[s]+0.35*zr63[s]+0.20*zpx50[s]
    tb=0.55*zrsi[s]+0.45*zpx20[s]
    fl=znf[s]
    conf=min(1.0, rat[s][5]/10.0)   # analyst coverage confidence (10+ = full)
    an=conf*(0.6*zup[s]+0.4*zbull[s]); vq=zvq[s]
    c=W["mom"]*mom+W["tech"]*tb+W["flow"]*fl+W["anal"]*an+W["valq"]*vq
    r=rows[s];pen=0
    if r["upside"]<0 and r["rsi"]>72: pen-=0.45
    if r["rsi"]>82: pen-=0.25
    # parabolic / speculative penalty: huge 3M run + hot RSI + tiny cap
    if r["r63"]>70 and r["rsi"]>72: pen-=0.30
    if (r["eps"] is None or r["eps"]<0) and r["mcap"]<4 and (r["ps"] is None or r["ps"]>25): pen-=0.20
    c+=pen; comp[s]=c
    blocks[s]=dict(mom=round(mom,2),tech=round(tb,2),flow=round(fl,2),anal=round(an,2),valq=round(vq,2),pen=round(pen,2))
def to100(c): return round(max(0,min(100,50+c*22)),1)
score={s:to100(comp[s]) for s in syms}
def verdict(x): return "BUY" if x>=55 else ("HOLD" if x>=45 else "SELL")

# ============ MODEL B: QUALIDADE + RECUO (buy good companies on the dip) ============
def clamp(x,a,b): return max(a,min(b,x))
def quality_raw(s):
    r=rows[s]; q=0.0; conf=min(1.0,rat[s][5]/10.0)
    q += 1.2 if (r["eps"] is not None and r["eps"]>0) else -1.2      # profitability
    pe=r["pe"]
    if pe is None or pe<0: q-=0.6
    elif 8<=pe<=35: q+=0.8
    elif 0<pe<8: q+=0.3
    elif pe>80: q-=0.8
    ps=r["ps"]
    if ps is not None:
        if ps<6: q+=0.5
        elif ps>20: q-=0.8
        elif ps>10: q-=0.3
    if r["yld"]>0: q+=0.3                                           # dividend payer
    m=r["mcap"]
    q += 0.5 if m>=50 else (0.2 if m>=5 else (-0.5 if m<1 else 0))  # size/stability
    q += r["bull"]*conf*0.8                                         # analyst quality (coverage-weighted)
    return q
def pullback_raw(s):
    r=rows[s]; p=0.0; rsi=r["rsi"]
    if 40<=rsi<=58: p+= 1.0-abs(rsi-48)/18.0
    elif rsi<40: p-= (40-rsi)/15.0
    else: p-= (rsi-58)/12.0
    x=r["px20"]
    if -7<=x<=2: p+=0.8
    elif x>2: p-= clamp((x-2)/8.0,0,1.2)
    else: p-= clamp((-7-x)/8.0,0,1.0)
    d=r["disthi"]
    if -20<=d<=-3: p+=0.9
    elif d>-3: p-=0.8
    else: p-= clamp((-20-d)/20.0,0,1.2)
    mm=r["r21"]
    if -8<=mm<=10: p+=0.5
    elif mm>10: p-= clamp((mm-10)/20.0,0,1.0)
    else: p-= clamp((-8-mm)/15.0,0,0.8)
    return p
qraw={s:quality_raw(s) for s in syms}; praw={s:pullback_raw(s) for s in syms}
traw={s:clamp(rows[s]["px50"],-25,25) for s in syms}
uraw={s:rows[s]["upside"]*min(1.0,rat[s][5]/10.0) for s in syms}
zQ=z([qraw[s] for s in syms]); zP=z([praw[s] for s in syms]); zT=z([traw[s] for s in syms]); zU=z([uraw[s] for s in syms])
zQ={s:zQ[i] for i,s in enumerate(syms)};zP={s:zP[i] for i,s in enumerate(syms)}
zT={s:zT[i] for i,s in enumerate(syms)};zU={s:zU[i] for i,s in enumerate(syms)}
WQ={"qual":0.30,"pull":0.30,"trend":0.15,"ups":0.20,"flow":0.05}
compq={};blocksq={}
for s in syms:
    c=WQ["qual"]*zQ[s]+WQ["pull"]*zP[s]+WQ["trend"]*zT[s]+WQ["ups"]*zU[s]+WQ["flow"]*znf[s]
    compq[s]=c
    blocksq[s]=dict(qual=round(zQ[s],2),pull=round(zP[s],2),trend=round(zT[s],2),ups=round(zU[s],2),flow=round(znf[s],2))
scoreq={s:to100(compq[s]) for s in syms}
def verdictq(s):
    v="BUY" if scoreq[s]>=55 else ("HOLD" if scoreq[s]>=45 else "SELL")
    r=rows[s]
    isspec = r["sec"] in ("Cripto","Gestão/Cripto") or r["mcap"]<0.4
    # quality gate: never BUY junk / broken trend / parabolic in this lens
    if v=="BUY" and ((r["eps"] is None or r["eps"]<=0) or isspec or r["px50"]<-3 or r["disthi"]<-30 or r["rsi"]>68):
        v="HOLD"
    return v

# ---- trade plan: stop 2xATR, targets R-multiples, inverse-vol sizing ----
for s in syms:
    r=rows[s];a=r["atr"];price=r["price"]
    R=2*a
    r["stop"]=round(price-R,2); r["stopPct"]=round(R/price*100,1)
    r["t1"]=round(price+2*R,2); r["t2"]=round(price+3*R,2)
    r["t1pct"]=round(2*R/price*100,1); r["t2pct"]=round(3*R/price*100,1)
    r["atrPct"]=round(a/price*100,1)
    r["score"]=score[s]; r["verdict"]=verdict(score[s]); r["blocks"]=blocks[s]
    r["scoreq"]=scoreq[s]; r["verdictq"]=verdictq(s); r["blocksq"]=blocksq[s]
    r["gbp"]=s in gbp_flag
    ap=r["atrPct"]
    r["risk"]="Alto" if ap>=6 else ("Médio" if ap>=3.5 else "Baixo")
    r["cov"]=rat[s][5]
    _pe=r["pe"]; _un=(r["eps"] is None or r["eps"]<0)
    r["spec"]= (r["sec"] in ("Cripto","Gestão/Cripto")
                or r["mcap"]<0.4
                or (r["mcap"]<3 and _un)
                or (rat[s][5]<6 and (_un or _pe is None or _pe>60)))
# inverse-vol weights within BUY set
buys=[s for s in syms if rows[s]["verdict"]=="BUY"]
invsum=sum(1/rows[s]["atrPct"] for s in buys) if buys else 1
for s in syms:
    rows[s]["ivw"]=round((1/rows[s]["atrPct"])/invsum*100,1) if s in buys else 0
buysq=[s for s in syms if rows[s]["verdictq"]=="BUY"]
invsumq=sum(1/rows[s]["atrPct"] for s in buysq) if buysq else 1
for s in syms:
    rows[s]["ivwq"]=round((1/rows[s]["atrPct"])/invsumq*100,1) if s in buysq else 0

order=sorted(syms,key=lambda s:comp[s],reverse=True)
orderq=sorted(syms,key=lambda s:compq[s],reverse=True)
print("N=",len(syms))
print("BUY:",[s for s in order if rows[s]['verdict']=='BUY'])
print("HOLD:",[s for s in order if rows[s]['verdict']=='HOLD'])
print("SELL:",[s for s in order if rows[s]['verdict']=='SELL'])
print()
print(f"{'sym':<6}{'sec':<13}{'sc':>5}{'verd':>5}{'ATR%':>6}{'stop%':>7}{'T1%':>6}{'T2%':>6}{'ivw%':>6}{'r21':>6}{'r63':>7}{'RSI':>5}{'up%':>7}{'bars':>5}")
for s in order:
    r=rows[s]
    print(f"{s:<6}{r['sec']:<13}{r['score']:>5}{r['verdict']:>5}{r['atrPct']:>6}{r['stopPct']:>7}{r['t1pct']:>6}{r['t2pct']:>6}{r['ivw']:>6}{r['r21']:>6}{r['r63']:>7}{r['rsi']:>5}{r['upside']:>7.1f}{r['bars']:>5}")

print()
print("== MODELO B: QUALIDADE + RECUO ==")
print("BUY:",[s for s in orderq if rows[s]['verdictq']=='BUY'])
print("HOLD:",[s for s in orderq if rows[s]['verdictq']=='HOLD'][:20])
print(f"{'sym':<6}{'scB':>5}{'verd':>5}{'Qual':>6}{'Pull':>6}{'Trend':>6}{'Ups':>6}{'RSI':>5}{'vsSMA20':>8}{'vsSMA50':>8}{'distHi':>7}")
for s in orderq[:14]:
    r=rows[s];b=r["blocksq"]
    print(f"{s:<6}{r['scoreq']:>5}{r['verdictq']:>5}{b['qual']:>6}{b['pull']:>6}{b['trend']:>6}{b['ups']:>6}{r['rsi']:>5}{r['px20']:>8}{r['px50']:>8}{r['disthi']:>7}")
json.dump({"order":order,"orderq":orderq,"rows":{s:rows[s] for s in syms},"weights":W,"weightsq":WQ},open(BASE+"full24.json","w"))
