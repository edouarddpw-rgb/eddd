import numpy as np, json
from scipy.signal import butter, sosfilt, oaconvolve
from dsp import *
rng=np.random.default_rng(7)
BPM=125.0; BEAT=60/BPM; BAR=4*BEAT; STEP=BEAT/4; NBARS=192
N=int((NBARS*BAR+6)*SR)
def T(bar,step=0.0): return (bar-1)*BAR+step*STEP
def mf(m): return 440.0*2**((m-69)/12)
def bp(x,lo,hi,o=2): return sosfilt(butter(o,[lo,hi],'band',fs=SR,output='sos'),x)
def hp(x,f,o=2): return sosfilt(butter(o,f,'high',fs=SR,output='sos'),x,axis=0)
def lp(x,f,o=2): return sosfilt(butter(o,f,'low',fs=SR,output='sos'),x,axis=0)
def pan(x,p):
    a=(p+1)*np.pi/4; return np.stack([x*np.cos(a)*np.sqrt(2),x*np.sin(a)*np.sqrt(2)],1)
def tarr(d): return np.arange(int(d*SR))/SR
def place(buf,sig,t,g=1.0):
    i=max(0,int(round(t*SR)));
    if i>=len(buf): return
    if sig.ndim==1: sig=pan(sig,0)
    m=min(len(sig),len(buf)-i); buf[i:i+m]+=g*sig[:m]
def new(): return np.zeros((N,2),np.float32)
MIDI={}
def ev(part,t,d,note,vel=100): MIDI.setdefault(part,[]).append((t,d,int(note),int(vel)))
def inr(bar,ranges): return any(a<=bar<=b for a,b in ranges)
SW=0.07*STEP
def hum(step): return (SW if step%2==1 else 0)+rng.normal(0,0.0025)

# ---------------- one-shots ----------------
def kick():
    t=tarr(0.5); f=43.65+(150-43.65)*np.exp(-t/0.03)+40*np.exp(-t/0.004)
    body=np.sin(2*np.pi*np.cumsum(f)/SR)*(1-np.exp(-t/0.0008))*np.exp(-t/0.26)
    click=lp(rng.normal(0,1,len(t)),2500)*np.exp(-t/0.0015)*0.12
    x=np.tanh(1.8*(body+click))/np.tanh(1.8); x[-500:]*=np.linspace(1,0,500); return x
def clap(seed):
    r=np.random.default_rng(seed); t=tarr(0.4); env=np.zeros_like(t)
    for k in (0,0.011,0.023): env+=(t>=k)*np.exp(-np.clip(t-k,0,None)/0.005)
    env+=(t>=0.03)*np.exp(-np.clip(t-0.03,0,None)/0.11)*0.7
    L=bp(r.normal(0,1,len(t)),850,2600)*env; R=bp(r.normal(0,1,len(t)),850,2600)*env
    s=np.stack([L,R],1); return s/np.abs(s).max()
METAL=[205.3,304.4,369.6,522.7,540,800]
def hat(dec,seed):
    r=np.random.default_rng(seed); t=tarr(max(0.15,dec*6))
    m=sum(np.sign(np.sin(2*np.pi*f*t+r.uniform(0,6))) for f in METAL)
    x=hp(r.normal(0,1,len(t)),7000,4)*np.exp(-t/dec)+0.5*hp(m,7000,4)*np.exp(-t/(dec*0.8))
    return x/np.abs(x).max()
def shaker(seed):
    r=np.random.default_rng(seed); t=tarr(0.15)
    env=np.minimum(t/0.012,1)*np.exp(-np.clip(t-0.012,0,None)/0.035)
    x=bp(r.normal(0,1,len(t)),4000,10000)*env; return x/np.abs(x).max()
def conga(f,seed):
    r=np.random.default_rng(seed); t=tarr(0.35); ff=f*(1+0.12*np.exp(-t/0.008))
    x=np.sin(2*np.pi*np.cumsum(ff)/SR)*np.exp(-t/0.15)+bp(r.normal(0,1,len(t)),1500,4000)*np.exp(-t/0.004)*0.35
    return x/np.abs(x).max()
def tom(f):
    t=tarr(0.5); ff=f*(1+0.45*np.exp(-t/0.015))
    x=np.tanh(1.4*np.sin(2*np.pi*np.cumsum(ff)/SR)*np.exp(-t/0.2)); return x/np.abs(x).max()
def cowbell():
    t=tarr(0.4); x=np.sign(np.sin(2*np.pi*523.25*t))+np.sign(np.sin(2*np.pi*783.99*t))
    x=bp(x,600,3500)*(0.7*np.exp(-t/0.012)+0.3*np.exp(-t/0.12)); return x/np.abs(x).max()
def clave():
    t=tarr(0.1); x=np.sin(2*np.pi*1864.7*t)*np.exp(-t/0.022); return x
def crash(seed,dec=0.8):
    r=np.random.default_rng(seed); t=tarr(3.0); out=[]
    for c in range(2):
        m=sum(np.sign(np.sin(2*np.pi*f*1.7*t+r.uniform(0,6))) for f in METAL)
        out.append((hp(r.normal(0,1,len(t)),4500,4)+0.4*hp(m,5000,4))*np.exp(-t/dec))
    s=np.stack(out,1); return s/np.abs(s).max()
def riser(bars,seed):
    r=np.random.default_rng(seed); d=bars*BAR; t=tarr(d); x=t/d
    fc=300*(8000/300)**x; out=[]
    for c in range(2): out.append(svf(r.normal(0,1,len(t)),fc,2.0,1)*x**2.2)
    sw=saw(150*(6)**x,0.0)*0.15*x**3; s=np.stack(out,1)+pan(sw,0)
    return s/np.abs(s).max()
def downlifter(seed):
    r=np.random.default_rng(seed); d=2*BAR; t=tarr(d); x=t/d
    fc=7000*(250/7000)**x; out=[svf(r.normal(0,1,len(t)),fc,1.5,1)*(1-x)**1.5 for c in range(2)]
    s=np.stack(out,1); return s/np.abs(s).max()
def impact():
    t=tarr(2.0); f=60*(30/60)**np.minimum(t/1.2,1)
    x=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.6); return x
KICK=kick(); CLAPS=[clap(i) for i in range(4)]
CH=[hat(0.03,i) for i in range(4)]; OH_S=[hat(0.11,10+i) for i in range(3)]; OH_L=[hat(0.3,20+i) for i in range(3)]
SHK=[shaker(30+i) for i in range(4)]
CG_H=[conga(mf(60),40+i) for i in range(3)]; CG_L=[conga(mf(53),50+i) for i in range(3)]
TOMS={m:tom(mf(m)) for m in (51,53,55,56,58,60,63,65)}
COW=cowbell(); CLV=clave()

# ---------------- arrangement tables ----------------
PROG=[(29,[53,56,60,65]),(37,[53,56,61,65]),(34,[53,58,61,65]),(39,[55,58,63,67])]  # Fm Db Bbm Eb : bass low root, seq voicing
PADV=[[53,56,60,63,67],[49,53,56,60,65],[46,49,53,56,60],[51,55,58,60,65]]
HARM=[(65,96),(105,128),(129,160)]
def chord(bar): return (bar-1)%4

st={k:new() for k in ['kick','clap','hats','perc','bass','acid','lead','seq','pads','fx']}
kicks=[]
# KICK
for bar in range(1,NBARS+1):
    for s in (0,4,8,12):
        ok=inr(bar,[(1,63),(65,95),(129,192)]) or (bar in (64,96) and s<8)
        if ok:
            t=T(bar,s); place(st['kick'],KICK,t); kicks.append(t); ev('kick',t,STEP,60,110)
# CLAP
for bar in range(1,NBARS+1):
    if inr(bar,[(9,63),(65,95),(129,188)]):
        for s in (4,12):
            t=T(bar,s)+rng.normal(0,0.002); c=CLAPS[rng.integers(4)]
            place(st['clap'],c,t,1.0); place(st['clap'],CLAPS[rng.integers(4)],t+0.009,0.45); ev('clap',t,STEP,60,105)
    roll=None
    if bar==64 or bar==96: roll=[(s,0.4+0.6*s/16) for s in range(8,16)]
    if 121<=bar<=124: roll=[(s,0.35+0.1*(bar-121)) for s in (0,4,8,12)]
    if bar in (125,126): roll=[(s,0.55+0.05*(bar-125)) for s in range(0,16,2)]
    if bar==127: roll=[(s,0.7+0.2*s/16) for s in range(16)]
    if bar==128: roll=[(s,0.9+0.1*s/8) for s in range(8)]
    if roll:
        for s,v in roll:
            t=T(bar,s); place(st['clap'],CLAPS[rng.integers(4)],t,v); ev('clap',t,STEP*0.5,60,int(127*min(v,1)))
# HATS
for bar in range(1,NBARS+1):
    for s in range(16):
        t=T(bar,s)+hum(s)
        if inr(bar,[(1,96),(113,127),(129,184)]) or (bar==128 and s<8) or (bar>184 and s%2==0):
            acc=1.0 if s%4==2 else (0.55 if s%2==0 else 0.38)
            if bar<=8: acc*=0.8
            v=acc*rng.uniform(0.85,1.0); place(st['hats'],pan(CH[rng.integers(4)],0.15),t,v*0.8); ev('closed_hat',t,STEP*0.5,60,int(127*v))
        if s%4==2:
            if inr(bar,[(33,48),(65,96),(161,176)]): place(st['hats'],pan(OH_S[rng.integers(3)],-0.1),t,0.7); ev('open_hat',t,STEP,60,90)
            if inr(bar,[(129,160)]): place(st['hats'],pan(OH_L[rng.integers(3)],-0.1),t,0.75); ev('open_hat',t,STEP*2,60,100)
        if inr(bar,[(17,96),(105,128),(129,184)]) and not (bar==128 and s>=8):
            v=(1.0 if s%2==1 else 0.6)*rng.uniform(0.8,1); place(st['hats'],pan(SHK[rng.integers(4)],-0.35),t+0.004,v*0.6); ev('shaker',t,STEP*0.5,60,int(110*v))
# PERC
CONGA_A=[(3,'H'),(6,'H'),(7,'L'),(10,'H'),(11,'L'),(14,'L'),(15,'L')]
CONGA_B=[(2,'H'),(3,'H'),(6,'H'),(7,'L'),(10,'H'),(11,'L'),(13,'H'),(14,'L')]
CLAVE=[[0,6,12],[4,8]]
for bar in range(1,NBARS+1):
    full=inr(bar,[(25,95),(129,176)]); sparse=inr(bar,[(109,127)])
    pat=CONGA_A if bar%2 else CONGA_B
    for s,w in pat:
        if full or (sparse and w=='H' and s in (3,10)):
            t=T(bar,s)+hum(s); v=rng.uniform(0.7,1.0)*(0.75 if sparse else 1)
            if w=='H': place(st['perc'],pan(CG_H[rng.integers(3)],-0.35),t,v*0.8); ev('conga_high',t,STEP,60,int(120*v))
            else: place(st['perc'],pan(CG_L[rng.integers(3)],0.35),t,v*0.8); ev('conga_low',t,STEP,53,int(120*v))
    if inr(bar,[(33,95),(129,176)]):
        tp=[(7,53),(13,60),(15,53)] if (bar-1)%4<3 else [(7,53),(9,60),(13,60),(15,65)]
        for s,m in tp:
            t=T(bar,s)+hum(s); place(st['perc'],TOMS[m],t,0.85); ev('tom_808',t,STEP*1.5,m,105)
    if bar==96:
        for s,m in zip(range(8,16),[65,63,60,58,56,55,53,51]):
            t=T(bar,s); place(st['perc'],TOMS[m],t,0.6+0.4*(s-8)/8); ev('tom_808',t,STEP,m,110)
    if inr(bar,[(41,48),(81,96),(145,160)]):
        for s in ([3,11] if bar%2 else [3,9,11]):
            t=T(bar,s)+hum(s); place(st['perc'],pan(COW,0.25),t,0.5); ev('cowbell',t,STEP,60,80)
    if inr(bar,[(81,96),(137,160)]):
        for s in CLAVE[(bar-1)%2]:
            t=T(bar,s)+hum(s); place(st['perc'],pan(CLV,-0.3),t,0.45); ev('clave',t,STEP,60,80)
# BASS
PED_A=[(2,0),(3,1),(6,0),(10,0),(11,1),(14,0)]
def bass_note(f,d,v):
    t=tarr(d+0.06); fr=np.full(len(t),f)
    x=saw(fr,rng.uniform())*0.7+np.sin(2*np.pi*f*t)*0.8
    fc=170+1500*np.exp(-t/0.07); x=svf(x,fc,1.3,0)
    env=np.minimum(t/0.002,1)*(0.6+0.4*np.exp(-t/0.12))*np.clip((d+0.04-t)/0.04,0,1)
    return np.tanh(2.0*x*env)*v
for bar in range(1,NBARS+1):
    ped=inr(bar,[(33,63),(161,176)]) or (bar==64)
    harm=inr(bar,[(65,95),(129,160)])
    if not(ped or harm): continue
    root=29 if ped else PROG[chord(bar)][0]
    pat=[(s,root+12*o) for s,o in PED_A]
    if (bar-1)%4==3: pat=[(2,root),(3,root+12),(6,root),(10,root+12),(11,root+15),(14,root+10)]
    for s,m in pat:
        if bar==64 and s>=8: continue
        t=T(bar,s); d=STEP*0.85; v=0.85 if m>root else 1.0
        place(st['bass'],bass_note(mf(m),d,v),t); ev('bass',t,d,m,int(115*v))
# helper: continuous mono synth from note list
def cont_synth(notes,glide,att,rel):
    f=np.full(N,mf(53)); gate=np.zeros(N); onset=np.full(N,1e3)
    for t,d,m in notes:
        i=int(t*SR); j=min(int((t+d)*SR),N); f[i:]=mf(m); gate[i:j]=1.0
        k=np.arange(i,min(i+int(2*SR),N)); onset[k]=np.minimum(onset[k],(k-i)/SR)
    f=slew_log(f,glide); env=ar_env(gate,att,rel); return f,env,onset
def autolog(points,t):
    b=[T(p[0]) for p in points]; v=[np.log(p[1]) for p in points]; return np.exp(np.interp(t,b,v))
def autolin(points,t):
    return np.interp(t,[T(p[0]) for p in points],[p[1] for p in points])
tt=np.arange(N)/SR
# ACID
ACID=[(0,53,10),(9,56,7),(16,55,6),(22,60,10),(32,53,8),(39,51,9),(48,56,6),(54,58,6),(60,60,5)]
notes=[]
for bar in range(57,169,4):
    if not inr(bar,[(57,96),(129,168)]): continue
    for s,m,l in ACID:
        t=T(bar,s); notes.append((t,l*STEP,m)); ev('acid',t,l*STEP,m,100)
f,env,onset=cont_synth(notes,0.06,0.003,0.05)
cut=autolog([(57,180),(65,260),(96.9,1500),(129,900),(144,2600),(160,3600),(168,600)],tt)
acc=1+1.3*np.exp(-onset/0.12)
x=acid_filter(saw(f,0.0)*env,cut*acc,7.0,2.2)
x=np.tanh(1.6*x)*autolin([(57,0.5),(65,1),(160,1),(168,0)],tt)
st['acid']+=pan(x.astype(np.float32),0)
# LEAD
HOOK=[[(0,72,3),(3,68,2),(6,72,2),(8,75,3),(11,72,2),(14,70,2)],
      [(0,68,4),(6,65,2),(8,67,2),(10,68,4),(14,67,2)],
      [(0,72,3),(3,68,2),(6,72,2),(8,75,3),(11,72,2),(14,70,2)],
      [(0,67,4),(6,70,2),(8,75,3),(11,70,2),(14,67,2)]]
def lead_layer(oct_shift,bars_ranges,vibpts,cutpts,gainpts,name,detc=6):
    notes=[]
    for bar in range(1,NBARS+1):
        if not inr(bar,bars_ranges): continue
        if bar==128: continue
        for s,m,l in HOOK[chord(bar)]:
            t=T(bar,s); d=l*STEP*0.97; notes.append((t,d,m+oct_shift)); ev(name,t,d,m+oct_shift,100)
    f,env,onset=cont_synth(notes,0.025,0.004,0.07)
    depth=autolin(vibpts,tt)*np.clip((onset-0.12)/0.15,0,1)
    fv=f*2**(depth*np.sin(2*np.pi*5.6*tt)/1200)
    x=saw(fv*2**(detc/1200),0.1)+saw(fv*2**(-detc/1200),0.6)+0.45*saw(2*fv,0.3)
    x=svf(np.tanh(1.4*x),autolog(cutpts,tt),0.9,0)*env*autolin(gainpts,tt)
    return x
lead=lead_layer(0,[(73,96),(105,127)],[(73,8),(96,25),(105,12),(128,30)],[(73,2600),(96.9,5000),(105,900),(127,4500)],[(73,1),(96.9,1),(105,0.55),(127,1)],'lead')
lead+=lead_layer(12,[(129,160)],[(129,30),(160,40)],[(129,5000),(160,6000)],[(129,0.85),(160,0.85)],'lead_octave_up',8)
lead+=lead_layer(0,[(145,160)],[(145,25),(160,35)],[(145,3500),(160,3500)],[(145,0.5),(160,0.5)],'lead',8)
st['lead']+=pan(lead.astype(np.float32),0)
# SEQ (16th phasing saw)
SEQ_IDX=[0,3,2,3,1,3,2,3,0,3,2,3,1,3,2,1]
seqcut=lambda t: autolog([(49,250),(64.9,2400),(65,1600),(96.9,2200),(113,300),(127.9,4000),(129,2000),(160,2600)],np.array([t]))[0]
for bar in range(1,NBARS+1):
    if not inr(bar,[(49,96),(113,127),(129,160)]) and not(bar==128): continue
    voic=PROG[0][1] if bar<65 else PROG[chord(bar)][1]
    for s in range(16):
        if bar==128 and s>=8: break
        m=voic[SEQ_IDX[s]]; t=T(bar,s); d=STEP*0.6; td=tarr(d+0.15)
        cc=seqcut(t)*(1+2*np.exp(-td/0.03))
        L=saw(np.full(len(td),mf(m)*2**(8/1200)),rng.uniform())+0.5*saw(np.full(len(td),mf(m+12)*2**(-5/1200)),rng.uniform())
        R=saw(np.full(len(td),mf(m)*2**(-8/1200)),rng.uniform())+0.5*saw(np.full(len(td),mf(m+12)*2**(5/1200)),rng.uniform())
        env=np.minimum(td/0.002,1)*np.exp(-td/0.09)*np.clip((d+0.03-td)/0.03,0,1)
        v=0.75 if s%2 else 1.0
        place(st['seq'],np.stack([svf(L,cc,1.4,0)*env,svf(R,cc,1.4,0)*env],1)*v,t); ev('saw_sequence',t,d,m,int(110*v))
for c,ph in ((0,0.0),(1,1.6)):
    st['seq'][:,c]=phaser(st['seq'][:,c].astype(np.float64),0.18,250,3500,0.55,ph)
# PADS + SUB + DRONE (breakdown)
for bar in range(97,128):
    ci=chord(bar); t=T(bar); d=BAR*(0.5 if bar==128 else 1.0)+0.02; td=tarr(d+1.0)
    env=np.minimum(td/0.35,1)*np.clip((d-td)/1.0+1,0,1)*np.where(td<d,1,np.exp(-(td-d)/0.35))
    padL=np.zeros(len(td)); padR=np.zeros(len(td))
    for j,m in enumerate(PADV[ci]):
        for k,dc in enumerate((-14,-6,0,6,14)):
            o=saw(np.full(len(td),mf(m)*2**(dc/1200)),rng.uniform())
            if (j+k)%2: padL+=o
            else: padR+=o
        ev('pads',t,d,m,85)
    cutp=1400+900*np.sin(2*np.pi*0.25*(t+td))
    s=np.stack([svf(padL,cutp,0.7,0),svf(padR,cutp,0.7,0)],1)*env[:,None]*0.12
    place(st['pads'],s,t)
    if bar>=105:
        r=PROG[ci][0]; place(st['pads'],np.sin(2*np.pi*mf(r)*td)*env*0.5,t); ev('sub_breakdown',t,d,r,90)
gd=np.zeros(N); 
for a,b in [(1,48),(97,127)]: gd[int(T(a)*SR):int(T(b+1)*SR)]=1
denv=ar_env(gd,1.5,1.5); fdr=mf(41)*2**(14*np.sin(2*np.pi*4.8*tt)/1200)
dr=(np.sin(2*np.pi*np.cumsum(fdr)/SR)+0.3*svf(saw(fdr*2,0.0),np.full(N,600.0),0.7,0))*denv*0.12
st['pads']+=pan(dr.astype(np.float32),0)
# FX
place(st['fx'],riser(4,1),T(61),0.6); place(st['fx'],riser(8,2),T(121),0.7)
st['fx'][int(T(128,8)*SR):int(T(129)*SR)]=0
place(st['fx'],downlifter(3),T(97),0.5)
for b,g in [(65,0.6),(81,0.3),(97,0.6),(129,0.7),(145,0.3),(161,0.45),(177,0.3)]: place(st['fx'],crash(b),T(b),g)
for b in (65,129): place(st['fx'],impact(),T(b),0.55)
vin=np.zeros(N); idx=rng.integers(0,N,int(N/SR*25)); vin[idx]=rng.normal(0,1,len(idx))
vin=bp(vin,800,5000)*1.5+rng.normal(0,0.004,N); vg=np.zeros(N)
for a,b in [(1,32),(97,120)]: vg[int(T(a)*SR):int(T(b+1)*SR)]=1
st['fx']+=pan((vin*ar_env(vg,2,2)*0.25).astype(np.float32),0)
# pause before drop 2 (dry signals)
i0,i1=int(T(128,8)*SR),int(T(129)*SR)
for k in st:
    if k!='fx': st[k][i0-200:i1]*=np.concatenate([np.linspace(1,0,200),np.zeros(i1-i0)])[:,None]
np.save('kicks.npy',np.array(kicks))
for k,v in st.items(): np.save(f'dry_{k}.npy',v)
json.dump(MIDI,open('midi_events.json','w'))
print('rendered',{k:float(np.abs(v).max()) for k,v in st.items()})
