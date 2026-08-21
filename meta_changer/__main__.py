import asyncio
from .core import mcp

def main():
    asyncio.run(mcp.run_stdio_async())