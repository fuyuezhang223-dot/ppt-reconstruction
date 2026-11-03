"""Optional: regenerate ONLY photo and decorative-illustration assets from bundled references.
Standard icons must come from assets/icon_library SVG, NEVER from slide screenshots.
Usage: python examples/real_cases/eam_6pages/prepare_photo_assets.py
"""
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'references'
ASSETS=ROOT/'assets'; ASSETS.mkdir(exist_ok=True)
PHOTO_BOXES={205:(1068,294,1604,798),206:(1097,293,1603,797),207:(1097,293,1603,797),
208:(1171,292,1604,713),209:(1097,293,1603,797),210:(1092,300,1607,758)}
for page,box in PHOTO_BOXES.items():
    with Image.open(SRC/f'slide_{page}.png') as im:
        crop=im.convert('RGBA').crop(box)
    mask=Image.new('L',crop.size,0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,crop.width-1,crop.height-1),radius=17,fill=255)
    crop.putalpha(mask);crop.save(ASSETS/f'worker_{page}.png')
with Image.open(SRC/'slide_205.png') as im:
    im.convert('RGB').crop((868,74,1672,281)).save(ASSETS/'industrial_skyline.png')
print('只输出人物照片、工业线稿背景。标准SVG图标由图标库调用，不裁剪。')
