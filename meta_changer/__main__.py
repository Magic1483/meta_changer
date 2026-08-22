import asyncio
from .mcp import mcp

def main():
    asyncio.run(mcp.run_stdio_async())