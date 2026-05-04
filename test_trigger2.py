import asyncio
from harness.task_registry import TaskRegistry
from harness.mcp_server import _handle_trigger_task, _handle_get_status
import uuid

async def main():
    registry = TaskRegistry()
    tid = str(uuid.uuid4())
    args = {
        "index_dir": "/Users/pengbolicious/pengbo-apps/e-2-g/local_outputs/span_landing_index_v2",
        "prompt": "Analyze the span-landing codebase...",
        "thread_id": tid
    }
    tool_index_dir = args["index_dir"]
    result = _handle_trigger_task(registry, args, tool_index_dir)
    print("Trigger result:", result)
    
    # Let's wait 15 seconds to see if it finishes
    for i in range(15):
        await asyncio.sleep(1)
        status = _handle_get_status(registry, {"thread_id": tid}, tool_index_dir)
        print(f"Status at {i}s: {status.get('status')} - step: {status.get('current_step')}")

if __name__ == '__main__':
    asyncio.run(main())
