import numpy as np, soundfile as sf, pyloudnorm as pyln, sys
from scipy.signal import butter, sosfilt, oaconvolve, resample_poly
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from dsp import SR, comp_gain, release_smooth, svf
BPM=125.0; BAR=4*60/BPM
def T(bar,step=0): return (bar-1)*BAR+step*BAR/16
def hp(x,f,o=2): return sosfilt(butter(o,f,'high',fs=SR,output='sos'),x,axis=0)
def lp(x,f,o=2): return sosfilt(butter(o,f,'low',fs=SR,output='sos'),x,axis=0)
def peq(x,f0,gdb,Q):
    A=10**(gdb/40); w=2*np.pi*f0/SR; al=np.sin(w)/(2*Q)
    b=[1+al*A,-2*np.cos(w),1-al*A]; a=[1+al/A,-2*np.cos(w),1-al/A]
    return sosfilt(np.array([b+a])/a[0],x,axis=0)
def shelf(x,f0,gdb,hi=True):
    A=10**(gdb/40); w=2*np.pi*f0/SR; al=np.sin(w)/2*np.sqrt(2); c=np.cos(w); s=2*np.sqrt(A)*al
    if hi: b=[A*((A+1)+(A-1)*c+s),-2*A*((A-1)+(A+1)*c),A*((A+1)+(A-1)*c-s)]; a=[(A+1)-(A-1)*c+s,2*((A-1)-(A+1)*c),(A+1)-(A-1)*c-s]
    else: b=[A*((A+1)-(A-1)*c+s),2*A*((A-1)-(A+1)*c),A*((A+1)-(A-1)*c-s)]; a=[(A+1)+(A-1)*c+s,-2*((A-1)+(A+1)*c),(A+1)+(A-1)*c-s]
    return sosfilt(np.array([b+a])/a[0],x,axis=0)
rng=np.random.default_rng(3)
def ir(T60,length,damp,pre):
    n=int(length*SR); t=np.arange(n)/SR; out=[]
    for c in range(2):
        x=rng.normal(0,1,n)*np.exp(-6.91*t/T60); x=lp(x,damp); x=hp(x,180)
        x=np.concatenate([np.zeros(int(pre*SR)),x]); out.append(x/np.sqrt((x**2).sum()))
    return out
HALL=ir(2.8,3.5,5500,0.025); ROOM=ir(0.7,1.0,7000,0.008)
def verb(x,IR): return np.stack([oaconvolve(x[:,c],IR[c])[:len(x)] for c in range(2)],1)
def pingpong(x,d,fb,n=7):
    m=x.mean(1); out=np.zeros_like(x); k=int(d*SR)
    for i in range(1,n+1):
        sh=np.zeros(len(m)); sh[i*k:]=m[:-i*k]*fb**(i-1); out[:,i%2]+=sh
    return lp(hp(out,300),3500)
if __name__=='__main__':
    st={k:np.load(f'dry_{k}.npy').astype(np.float64) for k in ['kick','clap','hats','perc','bass','acid','lead','seq','pads','fx']}
    N=len(st['kick']); kicks=np.load('kicks.npy')
    # sidechain envelope
    duck=np.zeros(N); L=int(0.4*SR); tt=np.arange(-int(0.003*SR),L)/SR
    shape=np.where(tt<0,(tt+0.003)/0.003,np.exp(-tt/0.065))
    for t in kicks:
        i=int(t*SR)-int(0.003*SR); o=max(0,-i); i=max(0,i); j=min(i+len(shape)-o,N); duck[i:j]=np.maximum(duck[i:j],shape[o:o+j-i])
    def sc(x,depth): return x*(1-depth*duck)[:,None]
    # channel EQ / processing
    st['kick']=peq(st['kick'],3500,1.5,1.0)
    st['clap']=peq(hp(st['clap'],220),1800,1.5,1.0)
    st['hats']=hp(st['hats'],450)
    st['perc']=hp(st['perc'],110)
    st['bass']=lp(hp(st['bass'],32),3500)
    st['acid']=peq(hp(st['acid'],120),300,-2,1.0)
    st['lead']=peq(hp(st['lead'],220),3200,-1.5,1.2)
    st['seq']=hp(st['seq'],260)
    st['pads']=hp(st['pads'],35)
    # sends (reverb/delay) added into each stem
    st['clap']+=verb(st['clap'],ROOM)*0.22+verb(st['clap'],HALL)*0.08
    st['perc']+=verb(st['perc'],ROOM)*0.25
    st['hats']+=verb(st['hats'],ROOM)*0.12
    lead_wet=verb(st['lead'],HALL)*0.28+pingpong(st['lead'],3*BAR/16,0.45)*0.35
    st['lead']+=sc(lead_wet,0.5)
    st['seq']+=sc(verb(st['seq'],HALL)*0.22,0.5)
    st['acid']+=sc(verb(st['acid'],HALL)*0.10+pingpong(st['acid'],3*BAR/16,0.35)*0.12,0.4)
    st['pads']+=verb(hp(st['pads'],200),HALL)*0.35
    # sidechain dry/wet
    st['bass']=sc(st['bass'],0.92); st['acid']=sc(st['acid'],0.45); st['lead']=sc(st['lead'],0.3); st['seq']=sc(st['seq'],0.5); st['pads']=sc(st['pads'],0.5)
    # gain staging (RMS in drop 1, relative to kick)
    def rms(x,a,b): s=x[int(T(a)*SR):int(T(b)*SR)]; return 20*np.log10(np.sqrt((s**2).mean())+1e-12)
    target={'kick':0,'bass':-3,'clap':-8,'hats':-14,'perc':-10,'acid':-9,'lead':-7.5,'seq':-12.5}
    ref=rms(st['kick'],65,97)
    for k,v in target.items():
        w=(73,97) if k=='lead' else (65,97)
        st[k]*=10**((ref+v-rms(st[k],*w))/20)
    st['pads']*=10**((ref-6-rms(st['pads'],105,121))/20)
    st['fx']*=10**((ref-11-rms(st['fx'],121,128))/20)
    for k in st: print(f"{k:6s} drop1 {rms(st[k],65,97)-ref:6.1f}  break {rms(st[k],105,121)-ref:6.1f}  drop2 {rms(st[k],129,161)-ref:6.1f}")
    np.save('kick_ref.npy',np.array([ref]))
    for k,v in st.items(): sf.write(f'stem_{k}.wav',(v*10**(-14/20)).astype(np.float32),SR,subtype='FLOAT')
    mix=sum(st.values())*10**(-14/20)
    sf.write('mix_premaster.wav',mix.astype(np.float32),SR,subtype='FLOAT')
    print('premaster peak dB',20*np.log10(np.abs(mix).max()))
