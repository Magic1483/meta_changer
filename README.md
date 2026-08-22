
## Install 
1. as library  `uv add git+[https://github.com/Magic1483/meta_changer]`
2. as MCP tool `uv add git+[https://github.com/Magic1483/meta_changer][mcp]`

Use in mcp_config.json 

```json
{
  "mcpServers": {
    "MetaChangeTool": {
      "command": "meta-changer",
      "args": []
    }
  }
}
```