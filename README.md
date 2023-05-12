# IdolShowdownFrameDataExtractor

## Usage
Extract assets with something like AssetRipper. Required folders are AnimationClip, Sprite, Texture2D. Place folders in the same folder as the .py files.

Generate GUID Maps with GenerateGUIDMap.py. Files are included from the base version but will need to be updated once the game is patched.

Extract Sprites with SpriteHandler.py using the base name of the file.

Examples:
```
python SpriteHandler.py Ayama_Crouch_0
python SpriteHandler.py all
```
Use AddFrameData.py to generate images with hitbox data using the fullpath to the animation. 
```
python AddFrameData.py AnimationClip/<desired animation>
```
