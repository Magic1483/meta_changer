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

# --- MCP server ---
mcp = MCPServer("MetaChangeTool")

@mcp.tool()
def SetMetadata(file_paths:List[str],phone_preset:str):
    """set metadata for target image"""
    try:
        set_metadata(file_paths,phone_preset)
        return f"Successfully updated metadata for: {', '.join(file_paths)}"
    except exiftool.exceptions.ExifToolExecuteError as err:
        return f"ExifTool Error: {err.stderr if hasattr(err, 'stderr') else err}"
    except Exception as err:
        return f'Error set metadata {err}'

@mcp.tool()
def AddPresets(presets: Dict[str, Phone]) -> str:
    """Register multiple camera metadata presets in bulk."""
    try:
        # Convert dictionary inputs to Phone dataclass instances if needed
        proc_presets = {
            name: (p if isinstance(p, Phone) else Phone(**p))
            for name, p in presets.items()
        }
        add_presets(proc_presets)
        return f"Successfully appended {len(presets)} new presets to registry."
    except Exception as err:
        return f"Error adding presets: {str(err)}"

@mcp.tool()
def GetPresets() -> str:
    """Return a plain text newline-delimited list of all available configuration presets."""
    return "\n".join(get_presets())

