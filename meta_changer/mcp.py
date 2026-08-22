from mcp.server import MCPServer
from core import *

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