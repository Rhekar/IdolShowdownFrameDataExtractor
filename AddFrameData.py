# importing image object from PIL
import math
from PIL import Image, ImageDraw
import os
import sys
import json
import yaml
from dataclasses import dataclass
from collections import defaultdict
import re

@dataclass
class Vec3:
    x: float
    y: float
    z: float
    init: bool = True
    
@dataclass
class Box:
    pos: Vec3 = None
    scale: Vec3 = None
    set: bool = False
    def __repr__(self):
        return f"Pos:{self.pos}\n scale: {self.scale}\n"
ppu = 100
imgscale = 2
hitboxRe = re.compile(r"Hitboxes/Hitbox(?P<index>\d*)")
hurtboxRe = re.compile(r"Hurtboxes/Hurtbox(?P<index>\d*)")

with open("SpriteGUID.json", 'r') as f:
    spriteGuids = json.load(f)
with open("TextureGUID.json", 'r') as f:
    texGuids = json.load(f)
    
    
class Frame:
    def __init__(self):
        self.subframecount = 0
        self.spriteGuid = None
        self.spriteOffset = (0,0)
        self.hitboxes = [Box(),Box(),Box(),Box(),Box()]
        self.hurtboxes = [Box(),Box(),Box(),Box(),Box()]
        self.colisionbox = []
        self.changed = False
        return
        
    def __repr__(self):
        return f"{spriteGuids[self.spriteGuid]['file']}\nHB:{self.hitboxes}\nHU:{self.hurtboxes}\n"
class Sequence:
    def __init__(self):
        self.frames = defaultdict(Frame)
        # on Frame X hitbox Y is active if true
        self.activeHitboxes = defaultdict(lambda: defaultdict(float))
        self.activeHurtboxes = defaultdict(lambda: defaultdict(float))
        self.fps = 60.0
        return
        

    
def loadSpriteData(data, seq):
    #import pdb; pdb.set_trace()
    spriteData = data["AnimationClip"]["m_PPtrCurves"][0]["curve"]
    for sprite in spriteData:
        frame = round(float(sprite["time"])*seq.fps)
        seq.frames[frame].spriteGuid = sprite["value"]["guid"]
        offset = spriteGuids[sprite["value"]["guid"]]["offset"]
        seq.frames[frame].spriteOffset = (float(offset["x"]), float(offset["y"]))
        seq.frames[frame].changed = True
    
def loadBoxData(data, seq):
    boxPosData = data["AnimationClip"]["m_PositionCurves"]
    for pos in boxPosData:
        isHitbox = hitboxRe.match(pos["path"])
        isHurtbox = hurtboxRe.match(pos["path"])
        for entry in pos["curve"]["m_Curve"]:
            frame = round(float(entry["time"])*seq.fps)
            value = entry["value"]
            pdata = Vec3(float(value['x']), float(value['y']), float(value['z']))
            if isHitbox:
                index = 0
                if isHitbox.group('index'):
                   index = int(isHitbox.group('index')) - 1
                seq.frames[frame].hitboxes[index].pos = pdata
                seq.frames[frame].hitboxes[index].set = True
            elif isHurtbox:
                index = 0
                if isHurtbox.group('index'):
                   index = int(isHurtbox.group('index')) - 1
                seq.frames[frame].hurtboxes[index].pos = pdata
                seq.frames[frame].hurtboxes[index].set = True
            if not seq.frames[frame].spriteGuid:
                k = sorted(seq.frames.keys())
                for i in range(frame-1, -1, -1):
                    if i not in k:
                        continue
                    seq.frames[frame].spriteGuid = seq.frames[i].spriteGuid
                    seq.frames[frame].spriteOffset = seq.frames[i].spriteOffset
                    break
    boxScaleData = data["AnimationClip"]["m_ScaleCurves"] 
    for scale in boxScaleData:
        isHitbox = hitboxRe.match(scale["path"])
        isHurtbox = hurtboxRe.match(scale["path"])
        for entry in scale["curve"]["m_Curve"]:
            frame = round(float(entry["time"])*seq.fps)
            value = entry["value"]
            pdata = Vec3(float(value['x']), float(value['y']), float(value['z']))
            if isHitbox:
                index = 0
                if isHitbox.group('index'):
                   index = int(isHitbox.group('index')) - 1
                seq.frames[frame].hitboxes[index].scale = pdata
                seq.frames[frame].hitboxes[index].set = True
            elif isHurtbox:
                index = 0
                if isHurtbox.group('index'):
                   index = int(isHurtbox.group('index')) - 1
                seq.frames[frame].hurtboxes[index].scale = pdata
                seq.frames[frame].hurtboxes[index].set = True
            else:
                continue
            if not seq.frames[frame].spriteGuid:
                k = sorted(seq.frames.keys())
                for i in range(frame, -1, -1):
                    if i not in k:
                        continue
                    seq.frames[frame].spriteGuid = seq.frames[i].spriteGuid
                    seq.frames[frame].spriteOffset = seq.frames[i].spriteOffset
                    break
def loadActiveData(data, seq):
    activeData = data["AnimationClip"]["m_FloatCurves"]
    for active in activeData:
        if active["attribute"] != "m_IsActive":
            continue
        isHitbox = hitboxRe.match(active["path"])
        isHurtbox = hurtboxRe.match(active["path"])
        for entry in active["curve"]["m_Curve"]:
            frame = round(float(entry["time"])*seq.fps)
            active = entry["value"]
            if isHitbox:
                index = 0
                if isHitbox.group('index'):
                   index = int(isHitbox.group('index')) - 1
                seq.activeHitboxes[frame][index] = float(active)
            elif isHurtbox:
                index = 0
                if isHurtbox.group('index'):
                   index = int(isHurtbox.group('index')) - 1
                seq.activeHurtboxes[frame][index] = float(active)
def genBox(pos, scale, offset, imgsize):
    width = ppu * scale.x * imgscale 
    height = ppu * scale.y * imgscale 
    left = (imgsize[0] / 2) - (width / 2) + (offset[0] * imgscale) + ppu * pos.x * imgscale
    top = (imgsize[1] / 2) - (height / 2) - (offset[1] * imgscale) - ppu * pos.y * imgscale
    bottom = top + height
    right = left + width
    return [(left, top), (right, bottom)]
    
def add_margin(pil_img, left, top, right, bottom, color):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result

def loadFrame(seq, f, currentHitboxes, currentHurtboxes, renderHitboxes, renderHurtboxes, activeHitboxes, activeHurtboxes):
    frameObj = seq.frames[f]
    for i, box in enumerate(frameObj.hitboxes):
        if box.set:
            if box.scale:
                currentHitboxes[i].scale = box.scale
            if box.pos:
                currentHitboxes[i].pos = box.pos     
    for i, box in enumerate(frameObj.hurtboxes):
        if box.set:
            if box.scale:
                currentHurtboxes[i].scale = box.scale
            if box.pos:
                currentHurtboxes[i].pos = box.pos   
    if f in seq.activeHitboxes:
        for i in seq.activeHitboxes[f]:
            activeHitboxes[i] = seq.activeHitboxes[f][i]    
    if f in seq.activeHurtboxes:
        for i in seq.activeHurtboxes[f]:
            activeHurtboxes[i] = seq.activeHurtboxes[f][i]            
def genBoxes(seq, f, currentHitboxes, currentHurtboxes, renderHitboxes, renderHurtboxes, activeHitboxes, activeHurtboxes, imgsize):
    frameObj = seq.frames[f]
    for i, active in enumerate(activeHitboxes):
        if active:
            renderHitboxes[i] = genBox(currentHitboxes[i].pos, currentHitboxes[i].scale, frameObj.spriteOffset, imgsize)
    for i, active in enumerate(activeHurtboxes):
        if active:
            renderHurtboxes[i] = genBox(currentHurtboxes[i].pos, currentHurtboxes[i].scale, frameObj.spriteOffset, imgsize)
def renderFrame(seq, f, currentHitboxes, currentHurtboxes, renderHitboxes, renderHurtboxes, activeHitboxes, activeHurtboxes, baseimg):
    # Todo: gen in place later
    for i in range(len(activeHitboxes)):
        if activeHitboxes[i]:
            hitimg = Image.new("RGBA", (baseimg.width, baseimg.height))
            hitimg1 = ImageDraw.Draw(hitimg)
            hitimg1.rectangle(renderHitboxes[i], fill ="#ff4c4c4c", outline ="#ff4c4cff")
            baseimg = Image.alpha_composite(baseimg,hitimg)
        if activeHurtboxes[i]:
            hurtimg = Image.new("RGBA", (baseimg.width, baseimg.height))
            hurtimg1 = ImageDraw.Draw(hurtimg)
            hurtimg1.rectangle(renderHurtboxes[i], fill ="#4cff4c4c", outline ="#4cff4cff")
            baseimg = Image.alpha_composite(baseimg,hurtimg)
    baseimg.save(os.path.join("SpriteRipHitboxes", f"{spriteGuids[seq.frames[f].spriteGuid]['file']}_f{f}.png"))

def padImg(seq, f, baseimg, currentHitboxes, currentHurtboxes, activeHitboxes, activeHurtboxes, imgsize):
    frameObj = seq.frames[f]
    r = imgsize[0]
    t = 0
    b = imgsize[1]
    l = 0
    for i, active in enumerate(activeHitboxes):
        if active:
            [(left, top), (right, bottom)] = genBox(currentHitboxes[i].pos, currentHitboxes[i].scale, frameObj.spriteOffset, imgsize)
            l = min(l, left)
            r = max(r, right)
            t = min(t, top)
            b = max(b, bottom)
    for i, active in enumerate(activeHurtboxes):
        if active:
            [(left, top), (right, bottom)] = genBox(currentHurtboxes[i].pos, currentHurtboxes[i].scale, frameObj.spriteOffset, imgsize)
            l = min(l, left)
            r = max(r, right)
            t = min(t, top)
            b = max(b, bottom)
    l = l if l == 0 else abs(math.ceil(l-16.5))
    t = t if t == 0 else abs(math.ceil(t-16.5))
    r = 0 if r == imgsize[0] else math.floor(r-imgsize[0]+16.5)
    b = 0 if b == imgsize[1] else math.floor(b-imgsize[1]+16.5)
    #print(l,t,r-imgsize[0],b-imgsize[1])
    print(l,t,r,b)
    return add_margin(baseimg, t, r, b, l, (0, 19, 19, 0))
def renderBoxes(seq):
    frames = sorted(seq.frames)
    numFrames = frames[-1]
    renderHitboxes = [0,0,0,0,0]
    renderHurtboxes = [0,0,0,0,0]
    currentHitboxes = [Box(),Box(),Box(),Box(),Box()]
    currentHurtboxes = [Box(),Box(),Box(),Box(),Box()]
    activeHitboxes = [0,0,0,0,0]
    activeHurtboxes = [1,0,0,0,0]
    for f in frames:
        print(f)
        baseimg = Image.open(os.path.join("SpriteRip", spriteGuids[seq.frames[f].spriteGuid]["file"] + ".png"))
        baseimg = baseimg.resize((baseimg.width*imgscale, baseimg.height*imgscale), resample=0)
        loadFrame(seq, f, currentHitboxes, currentHurtboxes, renderHitboxes, renderHurtboxes, activeHitboxes, activeHurtboxes)
        #baseimg = padImg(seq, f, baseimg, currentHitboxes, currentHurtboxes, activeHitboxes, activeHurtboxes, (baseimg.width, baseimg.height))
        baseimg = add_margin(baseimg, (512-baseimg.width)//2, (512-baseimg.height)//2,(512-baseimg.width)//2, (512-baseimg.height)//2, (0, 19, 19, 0))
        genBoxes(seq, f, currentHitboxes, currentHurtboxes, renderHitboxes, renderHurtboxes, activeHitboxes, activeHurtboxes, (baseimg.width, baseimg.height))
        #print (seq, f, currentHitboxes, currentHurtboxes, renderHitboxes, renderHurtboxes, activeHitboxes, activeHurtboxes, (baseimg.width, baseimg.height))
        renderFrame(seq, f, currentHitboxes, currentHurtboxes, renderHitboxes, renderHurtboxes, activeHitboxes, activeHurtboxes, baseimg)
def addFrameData(aniClip):
    s = Sequence()
    with open(aniClip, 'r') as f:
        anidata = yaml.load(f, Loader=yaml.BaseLoader)
        s.fps = float(anidata["AnimationClip"]["m_SampleRate"])
        loadSpriteData(anidata, s)
        loadBoxData(anidata, s)
        loadActiveData(anidata, s)
    renderBoxes(s)

def dumpAll():
    return
if __name__ == "__main__":
    if not os.path.exists("SpriteRipHitboxes"):
        os.makedirs("SpriteRipHitboxes")
    addFrameData(sys.argv[1])