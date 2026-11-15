import math,wave,subprocess
from pathlib import Path
import numpy as np
from scipy.signal import butter,sosfilt

def score(destination,duration,bpm=87,seed=61110):
    sr=48000;n=round(sr*duration);mix=np.zeros((n,2));rng=np.random.default_rng(seed);beat=60/bpm
    def add(sound,start,gain,pan=0):
        start=round(start*sr)
        if start>=n:return
        count=min(len(sound),n-start);ang=(pan+1)*np.pi/4
        mix[start:start+count,0]+=sound[:count]*gain*np.cos(ang)
        mix[start:start+count,1]+=sound[:count]*gain*np.sin(ang)
    def key(note,length=2.5):
        t=np.arange(round(sr*length))/sr;f=440*2**((note-69)/12)
        a=np.sin(2*np.pi*f*t+.22*np.exp(-t*6)*np.sin(4*np.pi*f*t))
        a+=.22*np.sin(2*np.pi*f*2.002*t)*np.exp(-t*1.8)+.06*np.sin(6*np.pi*f*t)*np.exp(-t*3)
        return a*(1-np.exp(-t*180))*np.exp(-t/.78)
    def pad(notes,length):
        t=np.arange(round(sr*length))/sr;env=np.minimum(t/.3,1)*np.minimum((length-t)/.85,1)
        a=np.zeros(len(t))
        for note in notes:
            f=440*2**((note-69)/12);a+=np.sin(2*np.pi*f*t)+.25*np.sin(2*np.pi*f*.998*t)+.11*np.sin(4*np.pi*f*t)
        return a/len(notes)*env
    def bass(note):
        t=np.arange(round(sr*.95))/sr;f=440*2**((note-69)/12)
        return (np.sin(2*np.pi*f*t)+.17*np.sin(4*np.pi*f*t))*(1-np.exp(-t*90))*np.exp(-t/.45)
    filt=butter(2,[4500,11000],btype='bandpass',fs=sr,output='sos')
    def shaker():
        t=np.arange(round(sr*.11))/sr
        return sosfilt(filt,rng.normal(0,1,len(t)))*(1-np.exp(-t*500))*np.exp(-t*48)
    def kick():
        t=np.arange(round(sr*.2))/sr
        return np.sin(2*np.pi*(48*t+3*(1-np.exp(-30*t))))*(1-np.exp(-280*t))*np.exp(-23*t)
    cycle=[[60,64,67,71],[57,60,64,67],[53,57,60,64],[55,60,62,67],[60,64,67,74],[57,60,64,67],[50,57,60,65],[55,59,62,67]]
    bars=math.ceil(duration/(4*beat));cadence=max(0,bars-2)
    for bar in range(bars):
        start=4*bar*beat;chord=cycle[bar%8] if bar<cadence else [60,64,67,69]
        add(pad(chord,4*beat+.65),start,.047,(-1 if bar%2 else 1)*.22)
        for j,index in enumerate([0,2,1,3,2,1]):
            if bar==bars-1 and j>2:continue
            add(key(chord[index]+12),start+[0,.75,1.5,2,2.75,3.5][j]*beat,.060 if j in [0,3] else .044,[-.28,.24,-.1,.3,-.2,.14][j])
        for off in ([0,2] if bar<bars-1 else [0]):add(bass(chord[0]-12),start+off*beat,.073)
        if bar<bars-1:
            for off in [0,2]:add(kick(),start+off*beat,.040)
            for j in range(8):add(shaker(),start+(j*.5+.035*(j%2))*beat,.017 if j%2 else .010,(-1 if j%2 else 1)*.45)
        if bar%4 in [1,3] and bar<cadence:
            for off,note in zip([.5,1.75,3],[chord[2]+12,chord[3]+12,chord[1]+12]):add(key(note,2.7),start+off*beat,.038,.12)
    filtered=np.column_stack([sosfilt(butter(2,3300,fs=sr,output='sos'),mix[:,i]) for i in range(2)])
    for delay,gain in [(.173,.12),(.281,.10),(.413,.07),(.557,.045)]:
        shift=round(delay*sr);mix[shift:,0]+=filtered[:-shift,1]*gain;mix[shift:,1]+=filtered[:-shift,0]*gain
    t=np.arange(n)/sr;mix*=((np.clip(t/.4,0,1)*np.clip((duration-t)/1.7,0,1))**.85)[:,None]
    mix*=.76/max(np.max(np.abs(mix)),1e-8)
    raw=Path(destination).with_suffix('.temp.wav')
    with wave.open(str(raw),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((mix*32767).astype('<i2').tobytes())
    r=subprocess.run(['ffmpeg','-hide_banner','-v','error','-y','-i',str(raw),'-af','loudnorm=I=-19:TP=-2:LRA=7','-ar','48000','-c:a','pcm_s24le',str(destination)],capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf-8','replace'))
    return raw
