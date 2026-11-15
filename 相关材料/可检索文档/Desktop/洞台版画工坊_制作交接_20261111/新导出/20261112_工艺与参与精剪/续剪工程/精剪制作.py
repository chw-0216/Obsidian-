"""Recreate the Nov 12 edit from the portable project. Use --project to set its root."""
from pathlib import Path
import argparse, concurrent.futures, json, math, shutil, subprocess, sys
import cv2
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

parser=argparse.ArgumentParser()
parser.add_argument('--project',type=Path,required=True)
p=parser.parse_args().project.resolve()
eng=p/'剪辑工程'
out=p/'新导出/20261112_工艺与参与精剪'
work=Path.cwd()/'work/print_cut_nov12_cache'
work.mkdir(parents=True,exist_ok=True)
out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(eng))
from workshop_music import score
media={r['id']:p/'原始素材'/r['file'] for r in json.loads((p/'原始素材/素材索引.json').read_text('utf-8'))}
enc=['-c:v','libx264','-preset','veryfast','-crf','16','-threads','3','-pix_fmt','yuv420p','-color_primaries','bt709','-colorspace','bt709','-color_trc','bt709','-color_range','tv','-video_track_timescale','30000','-movflags','+faststart']
base=['ffmpeg','-hide_banner','-nostdin','-v','error','-y','-filter_threads','2','-filter_complex_threads','2']
def ff(args):
    subprocess.run(base+list(map(str,args)),cwd=work,check=True)
def probe(f):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(f)]))['streams']
def mp4(s):
    return work/(s+'.mp4')

# 30 fps. The two audition cuts share the same encoded clips.
counts=dict(entry=81,ink=75,head=66,pause=104,tail=290,shirt=114,talk1=62,talk2=70,
            child=96,wide=75,print=120,lift=105,look=50,moon=90,guide=135,door=131)
full=['entry','ink','head','tail','shirt','talk1','talk2','child','wide','print','lift','look','moon','guide','door']
av=['head','pause','tail','shirt']
bv=['head','tail','shirt']
result_names=['01_乡村美育工作站_版画丝网工作坊_精剪.mp4','02_A_保留完整往返.mp4','03_B_缩短中间段.mp4']
reused={'entry':('M01_01',0),'talk1':('M01_06',0),'talk2':('M01_07',0),'child':('M01_08',0),'wide':('M02_01',0),'print':('M02_02',26),'lift':('M02_03',14),'look':('M02_04',38)}
raw0={'head':9,'pause':75,'tail':179}
photos={'ink':('P15',(.49,.415,.99),(.49,.440,.89),12),'shirt':('P09',(.536,.493,.62),(.502,.420,.99),38),
        'moon':('P18',(.51,.49,.99),(.543,.483,.92),10),'guide':('P13',(.50,.297,.994),(.493,.737,.92),36),
        'door':('P14',(.49,.473,.965),(.507,.464,.94),52)}
def label(name,txt,end):
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: T,Microsoft YaHei,42,&H00F8F6F1,&H00FFFFFF,&H600F1817,&H89090F0F,-1,0,0,0,100,100,1,0,1,1.2,2,1,84,84,62,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
    f=work/(name+'.ass')
    f.write_text(header+f'Dialogue: 0,0:00:00.19,0:00:{end:05.2f},T,,0,0,0,,'+r'{\fad(200,220)}'+txt+'\n',encoding='utf-8-sig')
    return 'ass='+f.name
def still(k):
    sid,start,end,hold=photos[k]
    a=cv2.imdecode(np.fromfile(media[sid],np.uint8),cv2.IMREAD_COLOR)
    h,w=a.shape[:2]
    # Soften the brightest cotton and paper tones without changing logo outlines.
    x=np.arange(256,dtype='float32')/255
    shoulder={'shirt':.049,'ink':.019,'guide':.025,'moon':.012,'door':.025}[k]
    lut=np.rint(255*(x-shoulder*np.maximum(0,(x-.66)/.34)**2)).clip(0,255).astype('uint8')
    a=cv2.LUT(a,lut)
    filters=['scale=out_color_matrix=bt709:out_range=tv','format=yuv420p','setsar=1']
    if k=='shirt': filters.append(label(k,'工作坊印品',3.65))
    if k=='moon': filters.append(label(k,'数智教育工作坊  ·  月相印制',2.92))
    if k=='door': filters.extend([label(k,'洞台村  ·  版画丝网工作坊',4.30),'fade=t=out:s=107:n=23'])
    proc=subprocess.Popen(base+['-f','rawvideo','-pix_fmt','bgr24','-s','1920x1080','-r','30','-i','pipe:0','-an','-vf',','.join(filters),*enc,str(mp4(k))],cwd=work,stdin=subprocess.PIPE)
    try:
        for t in range(counts[k]):
            z=min(t/max(1,counts[k]-hold-1),1)
            z=z*z*(3-2*z)
            cx,cy,fw=np.array(start)*(1-z)+np.array(end)*z
            cw=w*fw;ch=cw*9/16
            tx=np.clip(cx*w-cw/2,0,w-cw);ty=np.clip(cy*h-ch/2,0,h-ch)
            frame=cv2.warpAffine(a,np.float32([[cw/1920,0,tx],[0,ch/1080,ty]]),(1920,1080),flags=cv2.WARP_INVERSE_MAP|cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
            proc.stdin.write(frame.tobytes())
    finally:
        proc.stdin.close()
        if proc.wait(): raise RuntimeError(k)
def render(k):
    if k in photos: return still(k)
    n=counts[k]
    if k in reused:
        idx,first=reused[k];src=eng/'现版已调色镜头'/(idx+'.mp4')
        if first==0 and int(probe(src)[0]['nb_frames'])==n:
            shutil.copyfile(src,mp4(k));return
        vf=f'trim=start_frame={first}:end_frame={first+n},setpts=PTS-STARTPTS'
    else:
        src=media['V05'];first=raw0[k]
        vf=f'trim=start_frame={first}:end_frame={first+n},setpts=PTS-STARTPTS,scale=1920:1080:flags=lanczos,setsar=1'
    ff(['-i',src,'-an','-vf',vf,'-frames:v',n,*enc,mp4(k)])
def pcm(file):
    raw=subprocess.check_output(base+['-i',str(file),'-vn','-ac','2','-ar','48000','-f','f32le','pipe:1'])
    return np.frombuffer(raw,'<f4').reshape(-1,2).copy()
def ramp(t,a,b):
    z=np.clip((t-a)/(b-a),0,1);return z*z*(3-2*z)
def window(t,a,b,c,d):
    return ramp(t,a,b)*(1-ramp(t,c,d))
def moment(seq,k): return sum(counts[a] for a in seq[:seq.index(k)])/30
def writepcm(name,arr):
    path=work/(name+'.wav');wavfile.write(path,48000,arr.astype('<f4'));return path
def analyze(file):
    cmd=['ffmpeg','-nostats','-hide_banner','-i',str(file),'-vn','-af','loudnorm=I=-17:TP=-2:LRA=6:print_format=json','-f','null','-']
    log=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stderr.decode('utf-8','replace')
    return json.loads(log[log.rfind('{'):log.rfind('}')+1])
def mix():
    source={}
    for sid in ['V05','V041','V042']:
        sound=pcm(media[sid])
        sound=sosfilt(butter(2,75,'highpass',fs=48000,output='sos'),sound,axis=0)
        source[sid]=sound.astype('float32')
    windows={k:('V05',v/30) for k,v in raw0.items()}
    windows.update({'wide':('V042',4.2+2/30),'print':('V041',35.4+36/30),'lift':('V042',57.6+14/30),'look':('V041',54+43/30)})
    def field(seq):
        chunks=[]
        for k in seq:
            length=counts[k]*1600
            a=np.zeros((length,2),np.float32)
            if k in windows:
                sid,s=windows[k];i=round(s*48000);a=source[sid][i:i+length].copy()
                a*= .9 if sid=='V05' else .31
            chunks.append(a)
        return np.concatenate(chunks)
    def audition(seq,key):
        arr=field(seq);t=np.arange(len(arr))/48000;end=moment(seq,'shirt')
        arr*=(ramp(t,0,.08)*(1-ramp(t,end-.12,end)))[:,None]*1.20
        return writepcm(key,arr)
    A=audition(av,'audition_a');B=audition(bv,'audition_b')
    length=sum(counts[k] for k in full)/30
    path=work/'music.wav';score(path,length,90,seed=61111)
    music=pcm(path);onset=moment(full,'head');release=moment(full,'shirt');classlift=moment(full,'lift');classend=moment(full,'moon')
    t=np.arange(round(length*48000))/48000
    duck=-3.5*window(t,onset-.36,onset+.12,release,release+.72)-4.5*window(t,release-5.8,release-5.2,release,release+.65)
    duck-=7.5*window(t,classlift-.4,classlift+.12,classend-.3,classend+.25)
    # The last bite of the classroom scene and the held sign give the music room to resolve.
    duck-=4.2*ramp(t,moment(full,'door')-.25,moment(full,'door')+1.45)
    bg=music[:len(t)]*10**(duck[:,None]/20)
    src=field(full)
    env=window(t,onset,onset+.20,release-.15,release)+window(t,moment(full,'wide'),moment(full,'wide')+.35,classend-.38,classend)
    # Smooth the discontinuity removed by the audition's single edit.
    cut=moment(full,'tail');env*=1-.8*window(t,cut-.02,cut-.001,cut+.001,cut+.022)
    prem=writepcm('premix',bg+src*env[:,None])
    measures=analyze(prem)
    gain=10**((-17-float(measures['input_i']))/20)
    # A sample-wise soft knee preserves levels below -3.7 dBFS and protects AAC headroom.
    signal=(bg+src*env[:,None])*gain
    mag=np.abs(signal);knee=.65;cap=.76
    signal=np.sign(signal)*np.where(mag<=knee,mag,knee+(cap-knee)*np.tanh((mag-knee)/(cap-knee)))
    return [writepcm('master',signal),A,B]
def mux(seq,sound,name):
    lst=work/(name[:2]+'.ffconcat')
    lst.write_text('ffconcat version 1.0\n'+''.join(f"file '{k}.mp4'\nduration {counts[k]/30:.9f}\n" for k in seq),'utf-8')
    target=out/name
    ff(['-f','concat','-safe','0','-i',lst,'-i',sound,'-map','0:v','-map','1:a','-c:v','copy','-bsf:v','setts=pts=round(PTS/1000)*1000:dts=round(DTS/1000)*1000:duration=1000','-video_track_timescale','30000','-c:a','aac','-b:a','256k','-t',f'{sum(counts[k] for k in seq)/30:.9f}','-movflags','+faststart',target])
    ff(['-xerror','-i',target,'-map','0:v','-map','0:a','-f','null','-'])
    v,a=probe(target);assert int(v['nb_frames'])==sum(counts[k] for k in seq) and abs(float(v['duration'])-float(a['duration']))<.002,(v['duration'],a['duration'])
    return dict(file=name,frames=int(v['nb_frames']),seconds=float(v['duration']),audio=float(a['duration']),integrated=analyze(target))
if __name__=='__main__':
    cv2.setNumThreads(2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as jobs:
        sound=jobs.submit(mix)
        list(jobs.map(render,counts))
        waves=sound.result()
    results=[mux(seq,aud,name) for seq,aud,name in zip([full,av,bv],waves,result_names)]
    proof={'versions':results,'timeline':[{ 'shot':k,'start':moment(full,k),'end':moment(full,k)+counts[k]/30} for k in full],'source_V05_frames_inclusive_exclusive':{'A':[[9,469]],'B':[[9,75],[179,469]]},'frames_per_second':30,'photo_sources':{k:v[0] for k,v in photos.items()}}
    (work/'cut.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(results,ensure_ascii=False),flush=True)
