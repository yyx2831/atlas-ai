"""离线回归：工具范围、消息关联、loop/graph 等价与停止边界。"""

import asyncio
import json
from tools_lab import validate_call
from learn import (
    Simulator,
    initial_state,
    make_nodes,
    run_loop,
    run_graph,
    failure_experiments,
)


async def main():
    for name, raw in [
        ("unknown", "{}"),
        ("get_device", '{"device_id":2}'),
        ("get_device", '{"device_id":"1"}'),
        ("get_device", '{"device_id":1,"force":true}'),
    ]:
        try:
            validate_call(name, raw, 1)
        except ValueError:
            pass
        else:
            raise AssertionError(f"非法调用未拦截：{name}, {raw}")

    plan = [
        ("get_device", {"device_id": 1}),
        ("get_alarm", {"device_id": 1}),
        ("search_manual", {"query": "ERR-1007"}),
    ]
    names = [name for name, _ in plan]
    loop = await run_loop(
        initial_state("测试"), *make_nodes(Simulator(plan), names, verbose=False)
    )
    graph = await run_graph(
        initial_state("测试"), *make_nodes(Simulator(plan), names, verbose=False), 5
    )
    assert loop == graph
    assert loop["iterations"] == 4 and len(loop["steps"]) == 3
    assert loop["stop_reason"] == "answered"
    calls = [c for m in loop["messages"] for c in m.get("tool_calls", [])]
    results = [m for m in loop["messages"] if m["role"] == "tool"]
    assert [c["id"] for c in calls] == [m["tool_call_id"] for m in results]
    assert all(json.loads(m["content"])["ok"] for m in results)
    limited = await run_loop(
        initial_state("测试"),
        *make_nodes(Simulator(plan), names, max_iterations=3, verbose=False),
    )
    assert limited["iterations"] == 3 and len(limited["steps"]) == 3
    assert limited["stop_reason"] == "iteration_limit"
    await failure_experiments()
    print("PASS：参数边界、消息关联、loop/graph 一致、4 轮正常结束与 3 轮上限")


if __name__ == "__main__":
    asyncio.run(main())
