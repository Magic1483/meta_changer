import asyncio
from pathlib import Path
from typing import Dict, List
from mcp.server import MCPServer
import exiftool
from dataclasses import  astuple, dataclass
from csv import DictReader
import csv


@dataclass
class Phone:
    Make          :str
    Model         :str
    Software      :str
    LensModel     :str
    FNumber       :str
    FocalLength   :str
    FocalLength35 :str

CSV_PATH = Path(__file__).parent / "presets.csv"
PRESETS: Dict[str,Phone] = {}

def load_presets():
    global PRESETS
    with CSV_PATH.open('r',encoding="utf-8") as f:
        for d in  DictReader(f.readlines()):
            preset = d['Preset'] 
            del d['Preset']
            PRESETS[preset] = Phone(*d)

def get_presets():
    return list(PRESETS.keys())

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