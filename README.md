
## Installation

### Install all options
```bash 
pip install "meta_changer[mcp,tg_bot] @ git+https://github.com/Magic1483/meta_changer" --upgrade
```

### Install as library
```bash 
pip install "meta_changer @ git+https://github.com/Magic1483/meta_changer"
```

### Install as MCP tool
```bash
pip install "meta_changer[tg_bot] @ git+https://github.com/Magic1483/meta_changer"
```

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


### Install as tg bot
```bash
pip install "meta_changer[tg_bot] @ git+https://github.com/Magic1483/meta_changer"
```


