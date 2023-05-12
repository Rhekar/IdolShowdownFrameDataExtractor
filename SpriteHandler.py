import os
import yaml
import json
from PIL import Image

with open("SpriteGUID.json", 'r') as f:
    spriteGuids = json.load(f)
with open("TextureGUID.json", 'r') as f:
    texGuids = json.load(f)

def ripAllSprites():
    for sprite in spriteGuids.values():
        spriteName = sprite["file"]
        ripSprite(spriteName)
        
def ripSprite(name):
    if os.path.isfile(os.path.join("SpriteRip", name + ".png")):
        return
    assetname = os.path.join("Sprite", name + ".asset")
    with open(assetname, 'r') as f:
        spritedata = yaml.load(f, Loader=yaml.BaseLoader)
        bb = spritedata["Sprite"]["m_RD"]["textureRect"]
        tex = spritedata["Sprite"]["m_RD"]["texture"]
    im = Image.open(os.path.join("Texture2D", texGuids[tex['guid']]+".png"))
    left = round(float(bb['x']))
    bottom = im.height - round(float(bb['y']))
    top = bottom - round(float(bb['height']))
    right = left + round(float(bb['width']))
    cropped = im.crop((left, top, right, bottom))
    cropped.save(os.path.join("SpriteRip", name + ".png"))

if __name__ == "__main__":
    if not os.path.exists("SpriteRip"):
        os.makedirs("SpriteRip")
    ripSprite("Ayama_Crouch_0") 
    #ripAllSprites()