import asyncio
from pathlib import Path
from typing import Dict, List
from mcp.server import MCPServer
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
    Make          :str
    Model         :str
    Software      :str
    LensModel     :str
    FNumber       :str
    FocalLength   :str
    FocalLength35 :str

CSV_PATH = CONFIG_DIR / "presets.csv"
PRESETS: Dict[str,Phone] = {}

if not CSV_PATH.exists():
    default_csv = str(resources.files(__package__) / "presets.csv")
    shutil.copyfile(default_csv,CSV_PATH)

def load_presets():
    global PRESETS
    with CSV_PATH.open('r',encoding="utf-8") as f:
        for d in  DictReader(f.readlines()):
            preset = d['Preset'] 
            del d['Preset']
            PRESETS[preset] = Phone(*d)

def get_presets():
    return list(PRESETS.keys())

def export_presets():
    return PRESETS

def set_presets(presets:Dict[str,Phone]):
    global PRESETS
    PRESETS = presets
    fieldnames = ["Preset",*get_presets()]
    rows = [[preset,*astuple(phone)] for preset,phone in presets.items()]
    
    with CSV_PATH.open('w',encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        writer.writerows(rows)

def add_preset(preset_name: str, phone: Phone):
    row_values = [preset_name, *astuple(phone)]
    print(row_values)
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row_values)

def set_metadata(file_paths:List[str],phone_preset:str):
    global PRESETS

    if phone_preset not in PRESETS:
        raise ValueError(f'Phone {phone_preset} not found in presets')
    p = PRESETS[phone_preset]

    with exiftool.ExifToolHelper() as et:
        et.set_tags(
            files=file_paths,
            tags=p.__dict__,
            params=["-P","-overwrite_original"]
            )



mcp = MCPServer("MetaChangeTool")
@mcp.tool()
def SetMetadata(file_paths:List[str],phone_preset:str):
    """set metadata for target image"""
    return set_metadata(file_paths,phone_preset)

@mcp.resource("presets")
def Presets() -> List[str]:
    """return list of available presets"""
    return get_presets()

load_presets()