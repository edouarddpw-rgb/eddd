import numpy as np
from numba import njit
SR=44100

@njit(cache=True)
def saw(freq, phase0):
    n=len(freq); out=np.empty(n); ph=phase0
    for i in range(n):
        dt=freq[i]/SR
        ph+=dt
        if ph>=1.0: ph-=1.0
        v=2.0*ph-1.0
        if ph<dt:
            t=ph/dt; v-=t+t-t*t-1.0
        elif ph>1.0-dt:
            t=(ph-1.0)/dt; v-=t*t+t+t+1.0
        out[i]=v
    return out

@njit(cache=True)
def svf(x, fc, q, mode):
    n=len(x); out=np.empty(n); ic1=0.0; ic2=0.0; k=1.0/q
    for i in range(n):
        f=fc[i]
        if f>0.45*SR: f=0.45*SR
        if f<10.0: f=10.0
        g=np.tan(np.pi*f/SR); a1=1.0/(1.0+g*(g+k)); a2=g*a1; a3=g*a2
        v3=x[i]-ic2; v1=a1*ic1+a2*v3; v2=ic2+a2*ic1+a3*v3
        ic1=2.0*v1-ic1; ic2=2.0*v2-ic2
        if mode==0: out[i]=v2
        elif mode==1: out[i]=v1
        else: out[i]=x[i]-k*v1-v2
    return out

@njit(cache=True)
def acid_filter(x, fc, q, drive):
    # resonant LP with saturation inside the loop (303-ish)
    n=len(x); out=np.empty(n); ic1=0.0; ic2=0.0; k=1.0/q
    for i in range(n):
        f=fc[i]
        if f>0.42*SR: f=0.42*SR
        if f<20.0: f=20.0
        g=np.tan(np.pi*f/SR); a1=1.0/(1.0+g*(g+k)); a2=g*a1; a3=g*a2
        xin=np.tanh(drive*x[i])
        v3=xin-ic2; v1=a1*ic1+a2*v3; v2=ic2+a2*ic1+a3*v3
        ic1=np.tanh(2.0*v1-ic1); ic2=2.0*v2-ic2
        out[i]=v2
    return out

@njit(cache=True)
def slew_log(f, tau):
    n=len(f); out=np.empty(n); a=np.exp(-1.0/(tau*SR)); y=np.log(f[0])
    for i in range(n):
        y=a*y+(1-a)*np.log(f[i]); out[i]=np.exp(y)
    return out

@njit(cache=True)
def ar_env(gate, att, rel):
    n=len(gate); out=np.empty(n); y=0.0
    aa=np.exp(-1.0/(att*SR)); ar=np.exp(-1.0/(rel*SR))
    for i in range(n):
        if gate[i]>y: y=aa*y+(1-aa)*gate[i]
        else: y=ar*y+(1-ar)*gate[i]
        out[i]=y
    return out

@njit(cache=True)
def phaser(x, rate, fmin, fmax, fb, phase):
    n=len(x); out=np.empty(n); xp=np.zeros(4); yp=np.zeros(4); last=0.0
    for i in range(n):
        lfo=0.5*(1.0+np.sin(2*np.pi*rate*i/SR+phase))
        f=fmin*(fmax/fmin)**lfo; t=np.tan(np.pi*f/SR); a=(t-1.0)/(t+1.0)
        y=x[i]+fb*last
        for s in range(4):
            o=a*y+xp[s]-a*yp[s]; xp[s]=y; yp[s]=o; y=o
        last=y; out[i]=0.5*(x[i]+y)
    return out

@njit(cache=True)
def comp_gain(det, thr_db, ratio, att, rel):
    n=len(det); g=np.empty(n); y=0.0
    aa=np.exp(-1.0/(att*SR)); ar=np.exp(-1.0/(rel*SR))
    for i in range(n):
        lvl=20*np.log10(det[i]+1e-9); over=lvl-thr_db
        gr=over*(1-1/ratio) if over>0 else 0.0
        if gr>y: y=aa*y+(1-aa)*gr
        else: y=ar*y+(1-ar)*gr
        g[i]=10**(-y/20)
    return g

@njit(cache=True)
def release_smooth(g, rel):
    n=len(g); out=np.empty(n); y=1.0; a=np.exp(-1.0/(rel*SR))
    for i in range(n):
        if g[i]<y: y=g[i]
        else: y=a*y+(1-a)*g[i]
        out[i]=y
    return out
