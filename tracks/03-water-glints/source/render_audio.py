from pathlib import Path
import numpy as np, wave, struct,csv,json
out=Path(__file__).parent;stems=out/'Stems';stems.mkdir(exist_ok=True)
sr=44100;bpm=88;sec=60/bpm;Q=480
meters=[(4, 4), (4, 4), (4, 4), (4, 4), (4, 4), (4, 4), (5, 4), (4, 4), (5, 4), (4, 4), (4, 4), (6, 8), (6, 8), (4, 4), (5, 4), (4, 4), (4, 4), (4, 4), (6, 8), (6, 8), (5, 4), (6, 8), (4, 4), (4, 4), (4, 4), (4, 4), (4, 4), (4, 4), (4, 4), (4, 4), (4, 4), (4, 4), (6, 8), (6, 8), (4, 4), (4, 4), (5, 4), (4, 4), (5, 4), (4, 4), (4, 4), (4, 4), (6, 8), (5, 4), (4, 4), (5, 4), (4, 4), (4, 4), (5, 4), (6, 8), (4, 4), (5, 4), (6, 8), (4, 4), (5, 4), (4, 4), (4, 4), (6, 8), (4, 4), (5, 4), (4, 4), (4, 4), (4, 4), (4, 4)]
seq=['Dm', 'Dm', 'Bb', 'A7', 'Dm', 'Gm', 'A7', 'Dm', 'Dm', 'Gm', 'A7', 'Dm', 'Bb', 'Gm', 'A7', 'Dm', 'Dm', 'Dm', 'Gm', 'A7', 'Dm', 'Bb', 'A7', 'Dm', 'Dm', 'Gm', 'A7', 'Dm', 'Dm', 'Bb', 'A7', 'Dm', 'Dm', 'Dm', 'Bb', 'Gm', 'Dm', 'Gm', 'A7', 'Dm', 'Dm', 'Dm', 'Bb', 'Gm', 'Dm', 'Gm', 'A7', 'Dm', 'Dm', 'Bb', 'Dm', 'Gm', 'Dm', 'Bb', 'A7', 'Dm', 'Dm', 'Bb', 'Gm', 'Dm', 'A7', 'Dm', 'Dm', 'Dm']
bpms=[66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 66.0, 68.0, 50, 50, 71.75, 73.0, 74.25, 75.5, 76.75, 78.0, 79.25, 68, 62, 66, 58, 64, 60, 56, 60, 66, 66, 66, 66, 66, 66, 66, 66]
beats=[n*4/d for n,d in meters];starts=np.cumsum([0]+beats[:-1]).tolist();total=sum(beats)
barsecs=np.array(beats)*60/np.array(bpms);times=np.r_[0,np.cumsum(barsecs)];duration=times[-1]+5;N=int(duration*sr)
def when(beat):
 i=min(len(starts)-1,max(0,int(np.searchsorted(starts,beat,side='right')-1)));return times[i]+(beat-starts[i])*60/bpms[i]
chords={'Dm':[62,65,69],'Bb':[62,65,70],'A7':[61,64,67,69],'Gm':[62,67,70],'F':[60,65,69],'C7':[60,64,67,70]};roots={'Dm':38,'Bb':34,'A7':33,'Gm':31,'F':41,'C7':36}
names=['01 Vinyl Arrows','02 Glass Melody','03 Velvet Percussion','04 Harp - foreground','05 Warm Foundation','06 Air and Harmonics','07 Breath Flute','08 Broken Vinyl','09 Finger Bass','10 Quiet Sub','11 Dull Kick','12 Udu and Clicks']
bufs=[np.zeros((N,2),np.float32) for _ in names];events=[];rng=np.random.default_rng(27)
def add(k,beat,p,d,v,kind,pan=0):
 start=int(when(beat)*sr);count=min(int((when(beat+d)-when(beat))*sr),N-start)
 if count<=0:return
 t=np.arange(count,dtype=np.float32)/sr;f=440*2**((p-69)/12);ph=2*np.pi*f*t;attack=1-np.exp(-t*180)
 if kind=='finger':
  # Plucked string spectrum with a brief finger transient and natural decay.
  det=ph+.018*np.exp(-t*18)*np.sin(ph*.5)
  x=sum(np.sin(det*h+.12*h)*np.exp(-t*(1.5+h*.45))/(h**1.35) for h in range(1,10))*attack
  x+=rng.normal(0,.055,count)*np.exp(-t*90)
  x*=np.minimum((count/sr-t)/.06,1)
 elif kind=='sub':x=np.sin(ph)*(1-np.exp(-t*35))*np.exp(-t*1.8)*np.minimum((count/sr-t)/.12,1)
 elif kind=='udu':x=(np.sin(2*np.pi*(95*t+1.5*(1-np.exp(-t*22))))+.4*np.sin(2*np.pi*173*t))*np.exp(-t*12)*attack+rng.normal(0,.05,count)*np.exp(-t*65)
 elif kind=='click':x=(rng.normal(0,.17,count)+np.sin(2*np.pi*1100*t)*.13)*np.exp(-t*210)
 elif kind=='flute':
  vib=ph+.025*np.sin(2*np.pi*5*t);x=(np.sin(vib)+.12*np.sin(vib*2)+rng.normal(0,.012,count))*(1-np.exp(-t*22))*np.minimum((count/sr-t)/.14,1)*.75
 elif kind=='harp':
  x=sum(np.sin(ph*h)*np.exp(-t*(1.8+h*.85))/(h**1.55) for h in range(1,9))*attack
 elif kind=='bell':x=np.sin(ph+1.2*np.exp(-t*6)*np.sin(ph*2.002))*np.exp(-t*4)*attack
 elif kind=='bass':x=(np.sin(ph)+.17*np.sin(ph*2))*np.exp(-t*3)*attack
 elif kind=='pad':x=(np.sin(ph)+.22*np.sin(ph*2.001))*np.minimum(t/.3,1)*np.minimum((count/sr-t)/.5,1)*.65
 elif kind=='kick':x=np.sin(2*np.pi*(49*t+55*.035*(1-np.exp(-t/.035))))*np.exp(-t*14)*attack
 elif kind=='snare':x=(rng.normal(0,.38,count)+.35*np.sin(2*np.pi*180*t))*np.exp(-t*25)*attack
 elif kind=='hat':
  noise=rng.normal(0,.25,count).astype(np.float32);x=np.diff(noise,prepend=0)*np.exp(-t*70)
 else:x=np.sin(ph)*np.exp(-t*15)*attack
 x=(x*v).astype(np.float32);g=np.array([np.sqrt((1-pan)/2),np.sqrt((1+pan)/2)],np.float32);bufs[k][start:start+count]+=x[:,None]*g
 if kind in ['harp','bell','pad','bass']:events.append([k,beat,p,d,round(v*127)])
# Vinyl arrows: two evolving noise swells, then air opens out.
for b in range(2):
 start=int(times[b]*sr);count=int(barsecs[b]*sr);t=np.arange(count)/sr;u=t/barsecs[b]
 noise=rng.normal(0,1,count);filtered=np.convolve(noise,np.ones(9)/9,mode='same')
 sweep=np.sin(2*np.pi*(120*t+420*t*t/(2*barsecs[b])))
 env=np.sin(np.pi*np.minimum(u*1.25,1))**1.7
 signal=(filtered*.13+sweep*.035)*env
 signal+=rng.normal(0,.007,count)*(1-u)
 for ch in range(2):bufs[0][start:start+count,ch]+=signal*(.85 if ch else 1)
for b,h in enumerate(seq):
 base=starts[b];L=beats[b];c=chords[h];foreground=b>=7
 if b>=2:
  # Glass announces the theme; later leaves room for harp.
  motif=[c[2]+12,c[1]+12,c[0]+12,c[1]+12]
  for j,p in enumerate(motif[:2] if foreground else motif):
   beat=.5+j*.5
   if beat<L:add(1,base+beat,p,min(.9,L-beat),.085 if foreground else .16,'bell',-.3)
 if b>=3 and b not in [39,40] and b<56:
  # Dull velvet kick, brushed backbeat; adapt naturally to each bar length.
  for beat in ([0,.75,2.75] if b%3==0 else [.25,1.75,3.25] if b%3==1 else [0,1.5,2.25]):
   if False:pass
  back=2 if L>=4 else 1.5 if meters[b][1]==8 else 1
  if back<L:add(2,base+back,38,.2,.09,'snare',.12)
  step=.5 if meters[b][1]==4 else 1
  for j,beat in enumerate([.5,1.25,1.5,2.375,2.5,3.25,3.75]):
   if beat<L:add(2,base+beat,42,.12,.028 if j%2 else .042,'hat',(-1)**j*.28)
 if b>=4 and b not in [39,40]:
  for beat in []:pass
 # Broad open pad, no thick low chords.
 if b>=2:
  for p in [c[0],c[2]]:add(5,base,p,max(.5,L-.1),.026 if foreground else .035,'pad',.35)
 if foreground and b not in range(32,39):
  # Recognisable contour, strong-note neighbours and dominant leading tone C#.
  theme={'Dm':[74,76,77,76,74,73,74,81],'Gm':[74,76,77,79,77,76,74,70],'A7':[73,74,76,79,76,74,73,69],'Bb':[74,76,77,81,77,76,74,70],'F':[77,79,81,79,77,76,77,84],'C7':[76,77,79,82,79,77,76,72]}[h]
  step=1/3 if meters[b][1]==8 else .5
  n=int(L/step)
  level=.14+min(b-7,13)*.005 if b<22 else max(.10,.205-(b-22)*.01)
  if b in [11,15,23,27]:level*=.85
  for j in range(n):
   if 16<=b<39 and j%3:continue
   if b>=48 and j%4:continue
   pitch=theme[j%8];beat=j*step
   add(3,base+beat,pitch,min(.85,L-beat),level*(1 if j%3 else 1.15),'harp',-.12)
  # Ending gestures articulate tonic/dominant triads; A7 resolves to Dm next bar.
  if b in [10,14,22,26,30]:
   for j,p in enumerate(c):
    beat=max(0,L-1)+j*.12
    if beat<L:add(3,base+beat,p+12,min(1.2,L-beat+.3),.12,'harp',.2)

# Shared two-note seed A-F, breaths, and selective F-G trills.
for b in range(12,64):
 base=starts[b];L=beats[b];late=b>=48
 level=.115 if b<42 else .15
 if late:level*=max(.22,1-(b-48)/19)
 if b in [16,18,20,23,28,30,31,32,34,36,39,40,42,44,47,48,50,52,54,55,57,60,63]:
  if b in [20,31,39,40]:add(6,base,77,L-.25,level,'flute',.22)
  else:
   add(6,base+.25,81,min(1.1,L/3),level,'flute',.18)
   add(6,base+L*.48,77,L*.45,level,'flute',.18)
  if b in [20,31,40,47]:
   for j in range(6):add(6,base+L-.85+j*.11,77 if j%2==0 else 79,.12,level*.55,'flute',.18)
 # Recorder-like harmonic register in the answering phrases.
 if b in [28,32,33,35,43,45]:
  add(1,base+.5,81,.5,.07,'flute',-.25);add(1,base+1.25,77,1.2,.08,'flute',-.25)
 if 48<=b<=55:
  # Motif dissolves between different players with generous silence.
  bufs[3][int(times[b]*sr):int(times[b+1]*sr)]*=.35
  add(3,base+L*.65,77 if b%2==0 else 81,1.8,.11*(56-b)/8,'harp',-.3)
 if b in [39,40]:
  for j,pitch in enumerate([74,77,81,86]):add(3,base+j*.7,pitch,1.8,.075,'harp',(-1)**j*.5)
# Deliberate errors, cuts, and delayed chromatic resolutions.
for b in [5,9,14,26,30,36,44,46]:
 base=starts[b];L=beats[b]
 a=int(when(base+L-.75)*sr);z=int(when(base+L-.5)*sr)
 for k in [2,4,5]:bufs[k][a:z]*=.02
 for j in range(5):add(7,base+L-.5+j*.0625,75,.07,.055,'bell',(-1)**j*.7)
 add(3,base+L-.125,75,.12,.085,'harp');add(3,base+L,74,.8,.12,'harp')
 for j in range(4):add(7,base+.75+j*.1875,86,.08,.028,'hat',(-1)**j*.75)
# The final soft tonic and F retain the water-glint aftertaste.
for pitch in [62,65,69]:add(3,starts[-1],pitch,4,.045,'harp')
# New low ensemble: mono-centred bass and sub, dry kick, roomy udu.
for b in range(3,64):
 if b in [39,40]:continue
 base=starts[b];L=beats[b];root=roots[seq[b]]
 growth=1 if b<41 else min(1,.28+(b-41)*.19)
 decline=1 if b<48 else max(0,(61-b)/13)**1.3
 level=growth*decline
 # Root, small anticipations, and a fifth leave room for the melodies.
 pattern=[(0,root,1.1,.25),(1.5,root,.55,.17),(2.75,root+7,.6,.18),(L-.375,root,.28,.12)]
 if meters[b][1]==8:pattern=[(0,root,1.1,.24),(1.75,root+7,.6,.16)]
 for off,pitch,d,v in pattern:
  if 0<=off<L:
   d=min(d,L-off-.03)
   if d>0:add(8,base+off,pitch,d,v*level,'finger')
 if b>=4:
  add(9,base,root-12,min(1.7,L-.1),.075*level,'sub')
 # Kick is deliberately sparse; it stops before the final breathing bars.
 if b<56:
  for off in ([0,2.5] if b%2==0 else [.25,1.75]):
   if off<L:add(10,base+off,36,.6,.29*level,'kick')
  for off in [.875, min(L-.4,2.125)]:
   if off<L:add(11,base+off,48,.4,.105*level,'udu',-.22 if off<1 else .27)
  if b%3==1:add(11,base+L-.625,80,.08,.06*level,'click',.4)
# Guarantee no new low tails intrude into the two-bar ringing void.
cut=int(times[39]*sr);resume=int(times[41]*sr)
for k in [8,9,10,11]:
 ramp=int(.04*sr);bufs[k][cut-ramp:cut]*=np.linspace(1,0,ramp)[:,None];bufs[k][cut:resume]=0
for k in [8,10,11]:bufs[k]=np.tanh(bufs[k]*1.6)/1.6
for k in [0,2,4,7]:bufs[k]=np.tanh(bufs[k]*1.8)/1.8
for k in [0,1,3,5,6,7]:
 source=bufs[k].copy()
 for delay,gain in [(.27,.12),(.63,.15),(1.11,.10),(1.79,.065),(2.37,.035)]:
  shift=int(delay*sr);bufs[k][shift:]+=source[:-shift,::-1]*gain
mix=sum(bufs);peak=float(np.max(np.abs(mix)));gain=min(1,.82/max(peak,1e-6))
fade=int(4*sr)
def write(path,a):
 a=a*gain;a[-fade:]*=np.linspace(1,0,fade)[:,None]
 with wave.open(str(path),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(a,-1,1)*32767).astype('<i2').tobytes())
for name,a in zip(names,bufs):write(stems/(name+'.wav'),a)
write(out/'Water Glints - Dense Bass - 64 bars.wav',mix)
rows=['Такт | Размер | BPM (четверть) | Гармония | Начало, сек','--- | --- | --- | --- | ---']
for i in range(64):rows.append(f'{i+1} | {meters[i][0]}/{meters[i][1]} | {bpms[i]:g} | {seq[i]} | {times[i]:.2f}')
(out/'Карта 64 тактов.md').write_text('# Блик на воде — 64 такта\n\n'+ '\n'.join(rows))
(out/'form64.json').write_text(json.dumps({'meters':meters,'bpm':bpms,'harmonies':seq,'seconds':times.tolist(),'duration':duration,'peak':peak*gain},indent=2))
print('64 bars',round(duration,2),'seconds; peak',round(peak*gain,3))
