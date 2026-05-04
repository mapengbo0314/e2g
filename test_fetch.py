import asyncio
from harness.mcp_server import _handle_fetch_context

def main():
    args = {
        "paths": ["src/pages/Landing.jsx"],
    }
    tool_index_dir = "/Users/pengbolicious/pengbo-apps/e-2-g/local_outputs/span_landing_index_v2"
    workspace_root = "/Users/pengbolicious/pengbo-apps/e-2-g"
    
    result = _handle_fetch_context(args, tool_index_dir, workspace_root)
    print(result)

if __name__ == '__main__':
    main()
