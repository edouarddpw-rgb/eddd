import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import butter, sosfilt, resample_poly
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from dsp import SR, comp_gain, release_smooth
x,_=sf.read('mix_premaster.wav'); x=x.astype(np.float64)
x=sosfilt(butter(2,28,'high',fs=SR,output='sos'),x,axis=0)
from mix import peq, shelf
x=peq(x,550,-3.0,0.8); x=peq(x,250,-1.0,1.0); x=peq(x,75,1.5,1.0); x=shelf(x,3500,3.5,True)
# glue compressor (stereo-linked, RMS-ish detector)
det=np.sqrt(sosfilt(butter(1,30,'low',fs=SR,output='sos'),(x**2).max(1)))
g=comp_gain(det,-16.0,2.0,0.012,0.15); x*=g[:,None]
print('glue GR max dB',-20*np.log10(g.min()),'avg in drop',-20*np.log10(np.median(g[int(125*SR):int(180*SR)])))
def limit(y,ceil_db,look=0.004,rel=0.06):
    c=10**(ceil_db/20); L=int(look*SR); pk=np.abs(y).max(1)
    gt=np.minimum(1,c/np.maximum(pk,1e-9))
    g1=minimum_filter1d(gt,size=L,origin=-(L//2))
    g1=release_smooth(g1,rel); gs=uniform_filter1d(g1,size=L,origin=(L-1)//2-(L-1)) 
    gs=np.minimum(gs,g1)  # safety
    return y*gs[:,None], gs
meter=pyln.Meter(SR)
def tp(y): return 20*np.log10(np.abs(resample_poly(y,4,1,axis=0)).max())
def soft(y,th=0.7):
    a=np.abs(y); o=np.where(a>th, th+(1-th)*np.tanh((a-th)/(1-th)), a); return np.sign(y)*o
def run(gain_db,ceil):
    y=soft(x*10**(gain_db/20),0.75)
    u=resample_poly(y,4,1,axis=0); SRo=SR
    c=10**(ceil/20); L=int(0.004*SR*4); pk=np.abs(u).max(1)
    gt=np.minimum(1,c/np.maximum(pk,1e-9)); g1=minimum_filter1d(gt,size=L,origin=-(L//2))
    from dsp import release_smooth as rs
    g1=rs(g1,0.06*4); gs=np.minimum(uniform_filter1d(g1,size=L,origin=(L-1)//2-(L-1)),g1)
    u*=gs[:,None]; y=resample_poly(u,1,4,axis=0); return y,gs
lo,hi=0.0,14.0
for _ in range(7):
    mid=(lo+hi)/2; y,gs=run(mid,-1.2); l=meter.integrated_loudness(y)
    if l<-9.0: lo=mid
    else: hi=mid
y,gs=run(lo,-1.2); l=meter.integrated_loudness(y); t=tp(y)
print('gain',lo,'LUFS',l,'TP',t,'max limiter GR dB',-20*np.log10(gs.min()))
y=y[:int((192*1.92+4.5)*SR)]; f=int(0.5*SR); y[-f:]*=np.linspace(1,0,f)[:,None]
y*=10**(-0.15/20); sf.write('Calanques_master.wav',y,SR,subtype='PCM_24')
