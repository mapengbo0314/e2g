import asyncio
from harness.task_registry import TaskRegistry
from harness.mcp_server import _handle_trigger_task, _handle_get_status

async def main():
    registry = TaskRegistry()
    args = {
        "index_dir": "/Users/pengbolicious/pengbo-apps/e-2-g/local_outputs/span_landing_index_v2",
        "prompt": "Analyze the span-landing codebase...",
        "thread_id": "test_thread_1"
    }
    tool_index_dir = args["index_dir"]
    result = _handle_trigger_task(registry, args, tool_index_dir)
    print("Trigger result:", result)
    
    status = _handle_get_status(registry, {"thread_id": "test_thread_1"}, tool_index_dir)
    print("Status immediately:", status)
    
    # wait for thread to finish
    await asyncio.sleep(5)
    
    status_later = _handle_get_status(registry, {"thread_id": "test_thread_1"}, tool_index_dir)
    print("Status after 5s:", status_later)

if __name__ == '__main__':
    asyncio.run(main())
