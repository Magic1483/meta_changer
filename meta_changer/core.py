import asyncio
from pathlib import Path
from typing import Dict, List

import exiftool
from dataclasses import  astuple, dataclass
from csv import DictReader
from importlib import resources
import csv,os,shutil


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

def set_metadata(file_paths:List[str],phone_preset:str) -> None:
    global PRESETS

    if phone_preset not in PRESETS:
        raise ValueError(f'Phone {phone_preset} not found in presets')
    
    resolved_paths = []
    for fp in file_paths:
        p = Path(fp).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Target image file does not exist: {p}")
        resolved_paths.append(str(p))
        
    phone = PRESETS[phone_preset]
    
    with exiftool.ExifToolHelper() as et:
        et.set_tags(
            files=file_paths,
            tags=phone.__dict__,
            params=["-P","-overwrite_original"]
            )

load_presets()



