import os
import yaml
import json
def genTexGuids():
    tex = os.listdir("Texture2D")
    txmap = {}
    for texture_file in tex:
        if "meta" in texture_file:
            with open("Texture2D/" + texture_file, 'r') as f:
                meta = yaml.load(f)
                # why developers why
                if "aki_3m_projectile" in texture_file:
                    txmap[meta['guid']] = "aki_3m_projectile."
                txmap[meta['guid']] = texture_file.split('.')[0]
    with open("TextureGUID.json", 'w') as f2:
        json.dump(txmap, f2)
def genSpriteGuids():
    sprite = os.listdir("Sprite")
    spritemap = {}
    i = 0
    for sprite_file in sprite:
        if "meta" in sprite_file:
            with open("Sprite/" + sprite_file, 'r') as f:
                with open("Sprite/" + sprite_file[:-5], 'r') as f2:
                    meta = yaml.load(f)
                    spriteraw = yaml.load(f2, Loader=yaml.BaseLoader)
                    # why developers why        
                    if "aki_3m_projectile" in sprite_file:
                        spritemap[meta['guid']] = ".".join(sprite_file.split('.')[0:2])
                    else:
                        spritemap[meta['guid']] = {"file": sprite_file.split('.')[0], "offset": spriteraw["Sprite"]['m_Offset']}
        i += 1
        if i % 100 == 0:
            print(i)
    with open("SpriteGUID.json", 'w') as f2:
        json.dump(spritemap, f2)

if __name__ == "_main__":        
    genTexGuids()
    genSpriteGuids()
