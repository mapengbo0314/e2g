import asyncio
import json
import sys
from harness.mcp_server import run_mcp_server

class MockReader:
    def __init__(self, items):
        self.items = items
    
    async def readline(self):
        if not self.items:
            raise asyncio.exceptions.IncompleteReadError(b"", None)
        return self.items.pop(0)

async def main():
    import harness.mcp_server
    
    reqs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"rootUri": "file:///Users/pengbolicious/pengbo-apps/e-2-g"}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "trigger_harness_task", "arguments": {"index_dir": "/Users/pengbolicious/pengbo-apps/e-2-g/local_outputs/span_landing_index_v2", "prompt": "Analyze...", "thread_id": "test_mcp_2"}}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_harness_status", "arguments": {"index_dir": "/Users/pengbolicious/pengbo-apps/e-2-g/local_outputs/span_landing_index_v2", "thread_id": "test_mcp_2"}}}
    ]
    
    lines = [json.dumps(r).encode('utf-8') + b"\n" for r in reqs]
    reader = MockReader(lines)
    
    # monkey patch the loop
    loop = asyncio.get_running_loop()
    async def mock_connect(*args, **kwargs):
        pass
    loop.connect_read_pipe = mock_connect
    
    # monkey patch readline
    harness.mcp_server.asyncio.StreamReader = lambda: reader
    
    # run
    await run_mcp_server()

if __name__ == '__main__':
    asyncio.run(main())
