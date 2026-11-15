"""Master the three approved workshop sequences as one continuous film."""
import concurrent.futures
import io
import json
import math
import subprocess
import wave
from pathlib import Path
from urllib.parse import quote

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import butter, sosfilt
from workshop_music import score

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / '剪辑工程/上版运镜素材'
ORIGINAL = ROOT / '原始素材'
WORK = ROOT / '新导出/复现工作区'
OUT = ROOT / '新导出/基准复现'
WORK.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)
MASTER = OUT / '乡村美育工作站_版画工坊宣传片_横屏完整版.mp4'
previous_timeline = json.loads((PREVIOUS / '04_重构素材与来源/运镜时间线.json').read_text('utf-8'))
shots = {s['id']: s for m in previous_timeline['modules'] for s in m['shots']}
originals = {s['id']: s for s in json.loads((ORIGINAL / '素材索引.json').read_text('utf-8'))}

# Source in, retained frames and optional tail hold at 30 fps. The two adjacent
# shots from P13 are rendered as one camera move with a shared colour balance.
edits = [
    ('M01_01', 0, 81, 0), ('M01_02', 3, 90, 0), ('M01_03', 4, 70, 0),
    ('M01_04', 0, 447, 0), ('M01_06', 9, 62, 0), ('M01_07', 9, 70, 0),
    ('M02_01', 2, 80, 0), ('M02_02', 10, 180, 0), ('M02_03', 0, 265, 0),
    ('M02_04', 5, 135, 0), ('M03_01', 4, 80, 0), ('M03_02', 0, 162, 0),
    ('M03_03', 0, 84, 0), ('M01_05', 0, 114, 0), ('M01_08', 0, 96, 0),
    ('M01_09', 0, 72, 36)]
assert {e[0] for e in edits} == set(shots) and len(edits) == len(shots)
timeline = []
frames = 0
for shot_id, first, count, hold in edits:
    shot = shots[shot_id]
    assert first + count <= round(shot['duration'] * 30)
    assert shot['sid'] not in {'P04', 'P06', 'P07'}
    timeline.append(dict(id=shot_id, source=shot['sid'], start=frames/30, first=first,
                         count=count, hold=hold, role=shot['name']))
    frames += count + hold
    timeline[-1]['end'] = frames/30
duration = frames/30

# Measured on neutral surfaces, then tuned by shot. Luma moves do not alter
# white cloth into grey or force dark graphite/teal materials to match skin.
# Values are RGB white-balance gains, saturation, shadow lift and midtone lift.
looks = {
    'M01_01': ((1.003, .998, 1.000), .98, .002, .004),
    'M01_02': ((1.000, 1.000, 1.020), .91, .006, .012),
    'M01_03': ((1.010, .996, 1.004), .96, .000, -.009),
    'M01_04': ((1.004, .998, 1.020), .98, .003, .003),
    'M01_05': ((.997, 1.003, 1.002), .98, .000, -.008),
    'M01_06': ((1.012, 1.000, 1.016), .965, .018, .030),
    'M01_07': ((1.001, .999, 1.012), .97, .005, -.003),
    'M01_08': ((.989, 1.003, 1.012), .98, .000, -.006),
    'M01_09': ((1.005, .999, 1.008), .97, .003, .006),
    'M02_01': ((1.002, .998, 1.002), .99, .002, .005),
    'M02_02': ((1.000, 1.000, 1.006), .99, .004, .008),
    'M02_03': ((1.028, 1.000, .977), .985, .005, .014),
    'M02_04': ((1.004, .999, 1.002), .985, .004, .008),
    'M03_01': ((.995, 1.002, 1.007), .95, -.001, -.002),
    'M03_02': ((1.003, 1.001, .998), .96, .009, .019),
}
def write_look(shot_id):
    gain, saturation, shadow, mid = looks[shot_id]
    levels = np.linspace(0., 1., 33)
    blue, green, red = np.meshgrid(levels, levels, levels, indexing='ij')
    rgb = np.stack((red, green, blue), axis=-1).reshape(-1, 3) * gain
    grey = (rgb @ np.array([.2126, .7152, .0722]))[:, None]
    color = grey + (rgb - grey)*saturation
    y = np.clip(grey, 0, 1)
    color += shadow * (1-y)**2 + mid * (4*y*(1-y))
    # Shared soft shoulder and very light paper warmth, strongest in lit areas.
    color += np.array([.002, .0007, -.0015])*y
    color -= .014*np.clip((color-.75)/.25, 0, 1)**2
    file = WORK / (shot_id + '.cube')
    with file.open('w', encoding='ascii') as f:
        f.write('LUT_3D_SIZE 33\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        np.savetxt(f, np.clip(color, 0, 1), fmt='%.6f')
    return file.name

def ff(args, tag):
    result = subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',
                             '-filter_threads','2','-filter_complex_threads','2', *map(str,args)],
                            cwd=WORK, capture_output=True)
    if result.returncode:
        raise RuntimeError(tag + ' ' + result.stderr.decode('utf-8','replace')[-2000:])

encode = ['-c:v','libx264','-preset','fast','-crf','16','-threads','3','-pix_fmt','yuv420p',
          '-color_primaries','bt709','-colorspace','bt709','-color_trc','bt709','-color_range','tv',
          '-video_track_timescale','30000','-movflags','+faststart']

def make_label(shot_id, label):
    # A location appears on the real establishing frame, with no intertitle.
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Place,Microsoft YaHei,43,&H00F8F6F1,&H00F8F6F1,&H48352C24,&H630D1712,-1,0,0,0,100,100,1,0,1,1.6,2.0,1,78,60,62,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
    name = 'place_' + shot_id + '.ass'
    (WORK / name).write_text(header + 'Dialogue: 0,0:00:00.07,0:00:02.51,Place,,0,0,0,,{\\fad(170,200)}'+label+'\n',encoding='utf-8-sig')
    return name

def campus_camera():
    """Render one unbroken camera arc from faces to hands, then travel sideways."""
    p = ORIGINAL / originals['P13']['file']
    image = cv2.imdecode(np.fromfile(p,np.uint8),cv2.IMREAD_COLOR)
    ih, iw = image.shape[:2]
    dest = WORK / 'campus_clean.mkv'
    args = ['ffmpeg','-hide_banner','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24',
            '-s','1920x1080','-r','30','-i','-','-an','-c:v','ffv1','-level','3',
            '-threads','3','-pix_fmt','gbrp',str(dest)]
    # Cubic Hermite interpolation keeps the pan velocity continuous at the join.
    keys = np.array([0., .55, 4.90, 6.00, 8.16666667])
    poses = np.array([[.5,.29,.99],[.499,.31,.989],[.49,.719,.934],
                      [.505,.745,.896],[.57,.760,.76]])
    from scipy.interpolate import PchipInterpolator
    values = PchipInterpolator(keys, poses, axis=0)(np.arange(246)/30)
    log = (WORK/'campus_camera.log').open('wb')
    proc = subprocess.Popen(args,stdin=subprocess.PIPE,stderr=log)
    try:
        for cx, cy, fw in values:
            cw=iw*fw; ch=cw*9/16
            cx=np.clip(cx*iw,cw/2,iw-cw/2); cy=np.clip(cy*ih,ch/2,ih-ch/2)
            transform=np.float32([[cw/1920,0,cx-cw/2],[0,ch/1080,cy-ch/2]])
            view=cv2.warpAffine(image,transform,(1920,1080),flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
            proc.stdin.write(view.tobytes())
    finally:
        proc.stdin.close(); code=proc.wait(); log.close()
    if code: raise RuntimeError('Campus camera failed. See '+str(WORK/'campus_camera.log'))
    return dest

locations = {'M01_01':'洞台村  ·  乡村美育工作站','M02_01':'澜沧课堂','M03_01':'校内工作坊'}

def render_shot(item):
    sid=item['id']
    if sid=='M03_03': return None
    input_path=PREVIOUS/shots[sid]['file']
    count=item['count']
    if sid=='M03_02':
        input_path=campus_camera(); count+=84
    cube=write_look(sid)
    filters=[f'trim=start_frame={item["first"]}:end_frame={item["first"]+count}',
             'setpts=PTS-STARTPTS','format=gbrp16le',f'lut3d=file={cube}:interp=tetrahedral',
             'scale=out_color_matrix=bt709:out_range=tv','format=yuv420p','setsar=1']
    if sid in locations: filters.append('ass=filename='+make_label(sid,locations[sid]))
    if item['hold']: filters.append(f'tpad=stop_mode=clone:stop={item["hold"]}')
    if sid=='M01_01': filters.append('fade=t=in:s=0:n=5')
    if sid=='M01_09': filters.append('fade=t=out:s=85:n=22')
    output=WORK/(sid+'.mp4')
    ff(['-i',input_path,'-vf',','.join(filters),'-an','-frames:v',count+item['hold'],*encode,output],sid)
    return output

def prepare_sound():
    sr=48000
    full_score=WORK/'continuous_score.wav'
    score(full_score,duration,90,seed=61111)
    n=round(duration*sr)
    def pcm(path, start=0, length=None):
        cmd=['ffmpeg','-v','error','-ss',str(start),'-i',str(path),'-vn']
        if length is not None: cmd+=['-t',str(length)]
        cmd+=['-ar',str(sr),'-ac','2','-f','f32le','-']
        return np.frombuffer(subprocess.check_output(cmd),'<f4').reshape(-1,2).copy()
    bg=pcm(full_score)[:n]
    assert len(bg)==n
    env=np.ones(n,np.float32)
    field=np.zeros((n,2),np.float32)
    by_id={s['id']:s for s in timeline}
    # Local times within the approved shots. Only the matching original's sound
    # is used under its own continuous image, at integer-frame accurate offsets.
    for sid,local_in,seconds in [('M01_04',10.6,4.1),('M02_03',.35,4.8)]:
        shot=shots[sid]; item=by_id[sid]
        t_src=shot['source_in']+item['first']/30+local_in
        audio=pcm(ORIGINAL/originals[shot['sid']]['file'],t_src,seconds)
        if len(audio)<sr: continue
        audio=sosfilt(butter(2,[100,8000],btype='bandpass',fs=sr,output='sos'),audio,axis=0)
        rms=np.sqrt(np.mean(audio**2)); peak=np.max(np.abs(audio))
        if rms<.0001: continue
        audio*=min(10**(-27/20)/rms, .27/max(peak,.001), 5)
        x=np.arange(len(audio))/sr
        shape=np.sin(np.pi/2*np.clip(x/.42,0,1))**2 * np.sin(np.pi/2*np.clip((seconds-x)/.65,0,1))**2
        start=round((item['start']+local_in)*sr);stop=start+len(audio)
        field[start:stop]+=audio*shape[:,None]
        env[start:stop]=1-.34*shape
    mix=bg*env[:,None]+field
    premix=WORK/'premix.wav'
    with wave.open(str(premix),'wb') as f:
        f.setnchannels(2);f.setframerate(sr);f.setsampwidth(2)
        f.writeframes((np.clip(mix,-.999,.999)*32767).astype('<i2').tobytes())
    master=WORK/'final_mix.wav'
    # Constant gain preserves the slow release of the musical ending.
    ff(['-i',premix,'-af','loudnorm=I=-18:TP=-1.5:LRA=9','-ar','48000','-c:a','pcm_s24le',master],'sound')
    return master

def read_frame(p,t,size=480):
    raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(p),'-frames:v','1','-vf',f'scale={size}:-2','-f','image2pipe','-c:v','mjpeg','-'])
    return Image.open(io.BytesIO(raw)).convert('RGB')

def comparison():
    pairs=[('M01_02','油墨与木纹'),('M03_02','指导现场'),('M01_05','白棉布与印迹'),('M01_08','纸张与肤色')]
    sheet=Image.new('RGB',(1090,147+4*335),'#eeeae2')
    draw=ImageDraw.Draw(sheet);large=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',31);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
    draw.text((23,18),'版画工坊  /  照片色调对照',font=large,fill='#20352e')
    draw.text((24,91),'上一版取景',font=small,fill='#52625c');draw.text((554,91),'完整片中的画面',font=small,fill='#52625c')
    for i,(sid,label) in enumerate(pairs):
        item=next(a for a in timeline if a['id']==sid)
        local={'M03_02':.13,'M01_08':3.0}.get(sid,1.0)
        t=item['start']+local
        left=read_frame(PREVIOUS/shots[sid]['file'],item['first']/30+local,512)
        right=read_frame(MASTER,t,512); y=128+i*335
        sheet.paste(left,(24,y));sheet.paste(right,(554,y));draw.text((25,y+292),label,font=small,fill='#263b33')
    file=OUT/'照片色调对照.jpg';sheet.save(file,quality=94)

def finish(segments,audio):
    paths=WORK/'master_concat.txt'
    paths.write_text(''.join("file '"+p.name+"'\n" for p in segments),encoding='utf-8')
    temp=WORK/'integrated_candidate.mp4'
    ff(['-f','concat','-safe','0','-i',paths,'-i',audio,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-t',str(duration),'-metadata','title=乡村美育工作站 · 版画工坊','-movflags','+faststart',temp],'master')
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(temp)]))
    v,a=info['streams'];assert v['width']==1920 and v['height']==1080 and v['r_frame_rate']=='30/1'
    assert int(v['nb_frames'])==frames and abs(float(v['duration'])-float(a['duration']))<.025
    ff(['-i',temp,'-f','null','-'],'full decode')
    temp.replace(MASTER)
    comparison()
    (WORK/'edit_decisions.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(file=str(MASTER),frames=frames,duration=duration,bytes=MASTER.stat().st_size),ensure_ascii=False),flush=True)

def deliver():
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        sound_job=pool.submit(prepare_sound)
        jobs=[pool.submit(render_shot,s) for s in timeline]
        segments=[p for p in (j.result() for j in jobs) if p]
        audio=sound_job.result()
    finish(segments,audio)

if __name__=='__main__':
    deliver()
