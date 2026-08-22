from pathlib import Path
from typing import Dict, List

import exiftool
from dataclasses import  asdict, astuple, dataclass
from csv import DictReader
from importlib import resources
import csv,os,shutil
import glob
from PIL import Image
import random

if os.name == "nt":
    CONFIG_DIR = Path(os.getenv("APPDATA")) / "meta_changer"
else:
    CONFIG_DIR = Path.home() / ".config" / "meta_changer"
CONFIG_DIR.mkdir(parents=True,exist_ok=True)

@dataclass
class Phone:
    Make                    :str
    Model                   :str
    Software                :str
    LensModel               :str
    FNumber                 :str
    FocalLength             :float
    FocalLengthIn35mmFormat :str

    def __post_init__(self):
        self.FocalLength = float(self.FocalLength)

CSV_PATH = CONFIG_DIR / "presets.csv"
PRESETS: Dict[str,Phone] = {}

if not CSV_PATH.exists():
    default_csv = str(resources.files(__package__) / "presets.csv")
    shutil.copyfile(default_csv,CSV_PATH)


# PRESETS
def load_presets():
    global PRESETS
    with CSV_PATH.open('r',encoding="utf-8") as f:
        for d in  DictReader(f.readlines()):
            preset = d.pop("Preset")
            PRESETS[preset] = Phone(**d)
            

def get_presets():
    return list(PRESETS.keys())

def export_presets():
    return PRESETS

def add_presets(presets: Dict[str,Phone]):
    """Append new preset, rewrite if exists"""
    global PRESETS

    rows = []
    for name,p in presets.items():
        PRESETS[name] = p
        rows.append([name, *astuple(p)])

    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
def set_presets(presets:Dict[str,Phone]):
    """ Rewrite all presets """

    global PRESETS
    PRESETS = presets
    fieldnames = ["Preset", "Make", "Model", "Software", 
                  "LensModel", "FNumber", "FocalLength", "FocalLengthIn35mmFormat"]
    
    with CSV_PATH.open('w',encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
    add_presets(presets)

def png_to_jpg(file_paths:List[str]) -> int:
    processed = 0
    for fp in file_paths:
        path = Path(fp)
        if not (path.exists() and path.suffix.lower() == '.png'):
            continue
        
        try:
            with Image.open(path,'r',formats=None) as img:
                img.convert('RGB').save(path.with_suffix('.jpg'))
                processed += 1
        except Exception: 
            continue

    return processed

def generate_random_shot_data() -> dict:
    return {
        "ISO": random.choice([50, 64, 80, 100, 125, 160, 200]),
        "ExposureTime": random.choice(["1/60", "1/120", "1/250", "1/500", "1/1000"]),
        "ExposureBiasValue": random.choice([0, 0, 0, -0.33, 0.33]),
        "SubSecTimeOriginal": f"{random.randint(0, 999):03d}",
        "SubSecTimeDigitized": f"{random.randint(0, 999):03d}",
        # "DateTimeOriginal": base_time.strftime("%Y:%m:%d %H:%M:%S"),
        "BrightnessValue": round(random.uniform(2.0, 6.5), 2),
    }

def set_metadata(patterns:List[str],phone_preset:str) -> int:
    """Return count of processed files"""
    global PRESETS

    if phone_preset not in PRESETS:
        raise ValueError(f'Phone {phone_preset} not found in presets')
    
    file_paths: set[Path] = set()
    for pattern in patterns:
        for m in  glob.glob(pattern,recursive=True):
            p = Path(m)
            if p.is_file():
                file_paths.add(p.resolve())
    
    if not file_paths:
        return 0
    
    phone = PRESETS[phone_preset]
    params = asdict(phone)
    params.update(generate_random_shot_data())
    with exiftool.ExifToolHelper() as et:
        et.set_tags(
            files=[str(p) for p in file_paths],
            tags=params,
            params=["-P","-overwrite_original"]
            )
    return len(file_paths)

load_presets()



