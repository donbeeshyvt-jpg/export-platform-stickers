"""Build transparent platform images and validate local LINE submission archives."""
import argparse
import hashlib
from sticker_index import ALPHABETS, OUTPUT, create_index, load_plan, write_table
import bisect
import io
import itertools
import json
import math
import re
import tempfile
import zipfile
from pathlib import Path
from PIL import Image

TARGETS = ("yt", "dc_emoji", "dc_sticker", "line_static", "line_animated",
           "line_emoji", "line_emoji_animated", "line_custom", "line_message",
           "line_big", "line_popup", "line_effect")
A = Image.Resampling.NEAREST
RGB_LIMIT = 1_000_000
SPECIAL = {"line_popup": "popup", "line_effect": "effect"}
EMOJI = {"line_emoji", "line_emoji_animated"}

def need(ok, why):
    if not ok:
        raise ValueError(why)

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def read_frames(path):
    if path.suffix.lower() == ".json":
        data = read_json(path)
        if "image" not in data:
            frames, times = [], []
            for row in data["frames"]:
                with Image.open(path.parent/row["file"]) as image:
                    frames.append(image.convert("RGBA"))
                times.append(row["duration_ms"])
            need(frames and len({f.size for f in frames})==1 and all(math.isfinite(t) and t>0 for t in times),
                 "PNG 序列的尺寸需一致，格時間需為正數")
            return frames,times
        with Image.open(path.parent / data["image"]) as sheet:
            sheet = sheet.convert("RGBA")
        frames, times = [], []
        for f in data["frames"]:
            x, y, w, h = [f[k] for k in ("x", "y", "w", "h")]
            need(0 <= x < x+w <= sheet.width and 0 <= y < y+h <= sheet.height,
                 f"圖集超出格框 {f}")
            frames.append(sheet.crop((x, y, x+w, y+h)))
            times.append(f["duration_ms"])
    else:
        frames, times = [], []
        with Image.open(path) as src:
            first = int(bool(src.info.get("default_image", False)))
            for i in range(first, src.n_frames):
                src.seek(i)
                frames.append(src.convert("RGBA"))
                times.append(src.info.get("duration", 100))
    need(frames and len({f.size for f in frames}) == 1, "同一動畫需使用相同來源畫布")
    need(all(math.isfinite(t) and t > 0 for t in times), "請先修正來源的零長度或無效畫格")
    return frames, times

def atlas(source, out):
    frames, times = read_frames(source)
    w, h = frames[0].size
    cols = min(8, len(frames))
    image = Image.new("RGBA", (w*cols, h*math.ceil(len(frames)/cols)))
    entries = []
    for i, (frame, duration) in enumerate(zip(frames, times)):
        x, y = i%cols*w, i//cols*h
        image.paste(frame, (x,y))
        entries.append(dict(x=x, y=y, w=w, h=h, duration_ms=duration))
    image.save(out / "sheet.png")
    data = dict(image="sheet.png", frames=entries)
    save_json(out / "sheet.json", data)
    back, delays = read_frames(out / "sheet.json")
    need(times == delays and all(a.tobytes() == b.tobytes() for a,b in zip(frames,back)),
         "精靈圖往返驗證失敗")

def master(source, out, sampling, size=600):
    need(size>0,"母稿邊長必須是正整數")
    # Fit the complete source canvas once so that every frame retains its anchor.
    frames,times = read_frames(source)
    w,h = frames[0].size
    scale = min(1,size/w,size/h)
    sw,sh = max(1,round(w*scale)),max(1,round(h*scale))
    xy = ((size-sw)//2,(size-sh)//2)
    entries = []
    for i,frame in enumerate(frames):
        canvas=Image.new("RGBA",(size,size))
        canvas.alpha_composite(frame.resize((sw,sh), sampling),xy)
        name=f"frame-{i:04}.png"
        canvas.save(out/name,dpi=(96,96))
        entries.append(dict(file=name,duration_ms=times[i]))
    save_json(out/"timeline.json",dict(source_size=[w,h],canvas=[size,size],
              placed_at=xy,frames=entries))

def envelope(frames):
    boxes = [f.getchannel("A").getbbox() for f in frames]
    boxes = [b for b in boxes if b]
    need(boxes, "畫面完全透明")
    return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)

def render(frames, bound, size, pad, method, tight=False):
    w,h = bound[2]-bound[0], bound[3]-bound[1]
    scale = min((size[0]-2*pad)/w, (size[1]-2*pad)/h)
    sw,sh = max(1,round(w*scale)),max(1,round(h*scale))
    if tight:
        size = tuple(min(cap, (n+2*pad+1)//2*2) for n,cap in zip((sw,sh),size))
    outputs = []
    for frame in frames:
        resized = frame.crop(bound).resize((sw,sh), method)
        canvas = Image.new("RGBA", size)
        canvas.alpha_composite(resized, ((size[0]-sw)//2,(size[1]-sh)//2))
        outputs.append(canvas)
    return outputs

def profile_frames(frames, times, cfg, seconds, maxloops):
    loops = cfg.get("plays", 1)
    need(type(seconds) is int and 1 <= seconds <= maxloops and type(loops) is int
         and 1 <= loops and seconds*loops <= maxloops, "請調整整秒週期及播放次數")
    indexes = cfg.get("indices")
    if indexes is None:
        n = min(12,len(frames))
        end = list(itertools.accumulate(times))
        indexes = [bisect.bisect_right(end, j*end[-1]/n) for j in range(n)]
    need(5 <= len(indexes) <= 20 and all(type(i) is int and 0 <= i < len(frames) for i in indexes),
         "LINE 動作需 5～20 個有效來源格，索引從 0 開始")
    stops = [round(i*seconds*1000/len(indexes)) for i in range(len(indexes)+1)]
    durations = cfg.get("duration_ms", [b-a for a,b in zip(stops,stops[1:])])
    need(len(durations)==len(indexes) and all(type(d) is int and d>0 for d in durations)
         and sum(durations)==seconds*1000, "duration_ms 應逐格對應，合計等於 seconds")
    return [frames[i] for i in indexes], durations, loops

def gif_frames(frames):
    # One shared RGB palette, one reserved transparency index for every frame.
    w,h = frames[0].size
    sheet = Image.new("RGB",(w,h*len(frames)))
    for i,f in enumerate(frames):
        sheet.paste(f.convert("RGB"),(0,h*i))
    palette = sheet.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    lut = palette.getpalette()[:765]
    lut = (lut+[0]*765)[:765]+[0,0,0]
    palref = Image.new("P",(1,1))
    palref.putpalette(lut[:765]+lut[:3])
    result=[]
    for f in frames:
        p = f.convert("RGB").quantize(palette=palref,dither=Image.Dither.NONE)
        p=p.point([*range(255),0])
        p.putpalette(lut)
        p.paste(255,mask=f.getchannel("A").point(lambda a:255 if a<128 else 0))
        result.append(p)
    return result

def encode(path, frames, times, plays, limit, line=False, gif=False):
    need(any(f.getchannel("A").getbbox() for f in frames),f"{path.name} 裁切或縮放後完全透明，請檢查來源與裁切框")
    result=io.BytesIO()
    if gif:
        seq=gif_frames(frames)
        # GIF stores centiseconds. Quantize cumulative times to avoid timing drift.
        stops = [0]+[round(t/10) for t in itertools.accumulate(times)]
        delays = [10*(b-a) for a,b in zip(stops,stops[1:])]
        need(min(delays)>0, "GIF 畫格太短；請降低取樣頻率")
        seq[0].save(result,"GIF",save_all=True,append_images=seq[1:],duration=delays,
                    loop=0,transparency=255,background=255,disposal=2,optimize=False)
        gif_ends=list(itertools.accumulate(delays))
    else:
        kw = dict(save_all=True,append_images=frames[1:],duration=times,loop=plays,
                  default_image=False,disposal=0,blend=0) if len(frames)>1 else {}
        frames[0].save(result,"PNG",dpi=(96,96),compress_level=9,**kw)
    data=result.getvalue()
    need(len(data)<limit,f"{path.name} 有 {len(data):,} bytes，請減少移動區域、畫格數或調整色彩後重試（工程門檻 <{limit:,}）")
    with Image.open(io.BytesIO(data)) as check:
        n=check.n_frames
        need(check.size==frames[0].size,"解碼尺寸錯誤")
        if len(frames)>1:
            need(n>=2 and (not line or 5<=n<=20),"編碼後有效畫格不足，請增加不同動作")
            if not gif:
                need(n==len(frames) and check.info.get("loop")==plays,"APNG 格數或播放次數不符；請合併重複姿勢並調整停留時間")
        total=0
        for i in range(n):
            check.seek(i)
            actual=check.convert("RGBA")
            if gif:
                intended=seq[bisect.bisect_right(gif_ends,total)].copy()
                intended.info["transparency"]=255
                reference=intended.convert("RGBA")
                for bg in ("#ffffff","#141414"):
                    matte=Image.new("RGBA",actual.size,bg)
                    need(Image.alpha_composite(matte,actual).tobytes()==Image.alpha_composite(matte,reference).tobytes(),
                         "GIF 解碼後出現殘影或透明差異")
            total+=check.info.get("duration",0)
            if not gif:
                need(actual.tobytes()==frames[i].tobytes(),"APNG 回讀像素與來源不符")
        if len(frames)>1:
            expected=sum(delays if gif else times)
            need(abs(total-expected)<=1, "回讀播放時間不符")
    path.write_bytes(data)
    return dict(file=path.name,wh=frames[0].size,frames=n,bytes=len(data),
                cycle_ms=total,plays=("infinite" if gif or (n>1 and plays==0) else plays if n>1 else None),
                sha256=hashlib.sha256(data).hexdigest())

def check_count(target, count, alphabet):
    if target in EMOJI:
        base={"regular":0,"kana":161,"latin":104,"both":265,
              "kana_extra":161,"latin_extra":104,"both_extra":265}
        need(alphabet in base,"未知的表情貼組合")
        n=base[alphabet]
        ok=(8<=count-n<=40) if alphabet=="regular" or alphabet.endswith("_extra") else count==n
    elif target in ("line_static","line_big","line_custom"):
        ok=count in (8,16,24,32,40)
    else:
        ok=count in (8,16,24)
    need(ok,f"{target} 套組張數 {count} 不符")

def export_plan(plan, cfgfile, root, chosen):
    rows=plan["items"]
    need(rows,"未指定素材")
    need(chosen,"請指定 --targets 或填寫索引內的目標平台")
    need(len(set(chosen))==len(chosen) and all(t in TARGETS for t in chosen),"目標重複或無效")
    keys=[i["key"] for i in rows]
    need(len(set(k.lower() for k in keys))==len(keys) and all(re.fullmatch(r"[A-Za-z0-9_]+",k) for k in keys),
         "key 使用不重複的英數字與底線")
    sources=cfgfile.parent
    notices=[]
    output_rows=[]
    for t in chosen:
        folder=root/t
        folder.mkdir()
        selected=[i for i in rows if t in i.get("targets", chosen)]
        need(selected,f"{t} 沒有勾選素材")
        line=t.startswith("line_")
        if line:
            check_count(t,len(selected),plan.get("alphabet","regular"))
        reports=[]
        def write(name, pictures, durations=None, loops=1, limit=RGB_LIMIT, gif=False, role="content"):
            report=encode(folder/name,pictures,durations or [],loops,limit,line,gif)
            reports.append(report)
            fmt="GIF" if gif else "APNG" if report["frames"]>1 else "PNG"
            width,height=report["wh"]
            output_rows.append(dict(key=key, target=t, position=num, role=role,
                                    output_path=f"{t}/{name}", archive_path=f"{t}.zip" if line else "",
                                    archive_member=name if line else "", format=fmt, width=width,
                                    height=height, frames=report["frames"], cycle_ms=report["cycle_ms"],
                                    plays=report["plays"], bytes=report["bytes"], sha256=report["sha256"]))
        for num,it in enumerate(selected,1):
            key=it["key"]
            opt=it.get("options",{}).get(t,{})
            stills,_=read_frames(sources/opt.get("source",it["source"]))
            need(len(stills)==1,"source 請指定一張代表靜圖，動畫使用 motion 或 effect")
            still=stills[0]
            need(still.getchannel("A").getextrema()[0]==0, f"{key} 靜圖缺透明背景")
            method=A if it.get("sampling","nearest")=="nearest" else Image.Resampling.LANCZOS
            need(it.get("sampling","nearest") in ("nearest","lanczos"),"sampling 限 nearest 或 lanczos")
            def bounds(seq, moving=False):
                manual=opt.get("motion_crop" if moving else "crop")
                if manual is None: return envelope(seq)
                x,y,r,b=manual
                need(0<=x<r<=seq[0].width and 0<=y<b<=seq[0].height,"crop 超出原圖")
                return tuple(manual)
            def static(size,pad,tight=False):
                return render([still],bounds([still]),size,pad,method,tight)
            base=str(num).zfill(3 if t in EMOJI else 2)
            motionkey="effect" if t in SPECIAL else "motion"
            animated=t in SPECIAL or t in ("line_animated","line_emoji_animated") or (
                t.startswith("dc_") and it.get(motionkey) and opt.get("animate",True))
            if animated:
                need(it.get(motionkey), f"{key} 缺 {motionkey}")
                seq,times=read_frames(sources/it[motionkey])
                need(any(f.getchannel("A").getextrema()[0]==0 for f in seq),f"{key} 動圖缺透明背景")
                need(len(seq)>=2,"動畫至少需要兩個畫格")
                bound=bounds(seq, moving=True)
                if line or opt.get("retime"):
                    seq,times,loops=profile_frames(seq,times,opt,opt.get("seconds",2),3 if t in SPECIAL else 4)
                else:
                    loops=0
                if t=="dc_sticker":
                    need(all(d>=1000/60-0.01 for d in times), "Discord 貼圖超過 60 FPS，請調整格時間")
                if t in SPECIAL:
                    write(base+".png",static((370,320),0,True))
                    size=tuple(opt.get("size",[480,480]))
                    w,h=size
                    need((w==480 and 320<=h<=480) or (h==480 and 200<=w<=480),"特效畫布不符")
                    suffix=SPECIAL[t]
                    write(base+"_"+suffix+".png",render(seq,bound,size,0,method),times,loops,role="overlay")
                elif t=="line_animated":
                    pictures=render(seq,bound,(320,270),0,method,True)
                    need(max(pictures[0].size)>=270,"動態貼圖至少一邊 270px")
                    write(base+".png",pictures,times,loops)
                elif t=="line_emoji_animated":
                    write(base+".png",render(seq,bound,(180,180),0,method),times,loops,300_000)
                elif t=="dc_emoji":
                    write(key+".gif",render(seq,bound,(128,128),0,method),times,0,256_000,True)
                else:
                    write(key+".png",render(seq,bound,(320,320),0,method),times,loops,512_000)
            elif t=="yt":
                need(re.fullmatch(r"[a-zA-Z0-9]{3,10}",key),"YT 名稱需 3～10 個英數字")
                size=opt.get("size",48)
                need(type(size) is int and 48<=size<=480,"YT 方形邊長需 48～480")
                write(key+".png",static((size,size),0))
            elif t=="dc_emoji":
                write(key+".png",static((128,128),0),limit=256_000)
            elif t=="dc_sticker":
                write(key+".png",static((320,320),0),limit=512_000)
            elif t=="line_big":
                box=bounds([still])
                cap=(min(396,(box[2]-box[0]+1)//2*2),min(660,(box[3]-box[1]+1)//2*2))
                pic=static(cap,0,True)
                need(pic[0].width>=80 and pic[0].height>=524,f"{key} 大貼圖內容未達最低寬／高；請提供直式構圖")
                write(base+".png",pic)
            elif t=="line_emoji":
                write(base+".png",static((180,180),0))
            else:
                write(base+".png",static((370,320),0 if t=="line_message" else 10,True))
            if t=="dc_emoji": need(len(key)>=2,"DC 表情名稱需至少兩碼")
            if t=="dc_sticker": notices.append(dict(target=t,file=key+".png",name=it.get("name",key),emoji=it.get("unicode"),description=it.get("description","")))
            if line and num==1:
                # The first item in upload order supplies main and tab images.
                write("tab.png",static((96,74),0),limit=300_000 if t=="line_emoji_animated" else RGB_LIMIT,role="tab")
                if t in SPECIAL:
                    write("main_"+SPECIAL[t]+".png",render(seq,bound,(480,480),0,method),times,loops,role="main_overlay")
                if t=="line_animated":
                    write("main.png",render(seq,bound,(240,240),0,method),times,loops,role="main")
                elif t not in EMOJI:
                    write("main.png",static((240,240),0),role="main")
        if line:
            archive=root/(t+".zip")
            with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
                for entry in sorted(folder.iterdir()): z.write(entry,entry.name)
            with zipfile.ZipFile(archive) as z:
                need(z.testzip() is None and sorted(z.namelist())==sorted(r["file"] for r in reports),"ZIP 核對失敗")
                need(all(z.read(n)==(folder/n).read_bytes() for n in z.namelist()),"ZIP 內容驗證失敗")
            need(archive.stat().st_size<(20_000_000 if t in EMOJI else 60_000_000),"ZIP 超過整包容量")
        save_json(root/(t+"-report.json"),reports)
    write_table(root/"output-index.csv",OUTPUT,output_rows)
    if notices: save_json(root/"discord-sticker-metadata.json",notices)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="cmd",required=True)
    m=sub.add_parser("master"); m.add_argument("source",type=Path); m.add_argument("out",type=Path)
    m.add_argument("--size",type=int,default=600)
    m.add_argument("--smooth",action="store_true",help="一般插畫用 Lanczos，像素圖預設最近鄰")
    a=sub.add_parser("atlas"); a.add_argument("source",type=Path); a.add_argument("out",type=Path)
    b=sub.add_parser("build"); b.add_argument("plan",type=Path); b.add_argument("out",type=Path)
    b.add_argument("--targets",nargs="+",choices=TARGETS)
    b.add_argument("--alphabet",choices=ALPHABETS)
    ix=sub.add_parser("index",help="建立空白素材索引或收錄資料夾內的單格 PNG")
    ix.add_argument("out",type=Path)
    ix.add_argument("--sources",type=Path)
    args=p.parse_args()
    if args.cmd=="index":
        count=create_index(args.out,args.sources)
        print(f"{count} 筆素材")
        return
    out=args.out.resolve()
    need(not out.exists(),"輸出目錄已存在，請換新名稱")
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        stage=Path(tmp)/"output";stage.mkdir()
        if args.cmd=="master": master(args.source,stage,Image.Resampling.LANCZOS if args.smooth else A,args.size)
        elif args.cmd=="atlas": atlas(args.source,stage)
        else:
            if args.plan.suffix.lower()==".csv":
                plan=load_plan(args.plan,TARGETS,args.alphabet or "regular")
            else:
                plan=read_json(args.plan)
                if args.alphabet:
                    plan["alphabet"]=args.alphabet
            export_plan(plan,args.plan.resolve(),stage,args.targets or plan["targets"])
        stage.rename(out)
    print(out)

if __name__=="__main__":
    main()
