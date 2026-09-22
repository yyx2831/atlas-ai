"""测量 Atlas SSE；token 数必须来自模型服务，不能用字符数代替。"""

import argparse
import getpass
import json
from time import perf_counter

import httpx


def measure(client, headers, question):
    start = perf_counter()
    first = None
    final = None
    with client.stream(
        "POST",
        "/chat/stream",
        headers=headers,
        json={"question": question, "use_knowledge": False},
    ) as response:
        response.raise_for_status()
        event = ""
        for line in response.iter_lines():
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                payload = json.loads(line[5:])
                if event == "delta" and payload.get("text") and first is None:
                    first = perf_counter()
                elif event == "error":
                    raise RuntimeError(payload.get("detail", "stream failed"))
                elif event == "done":
                    final = payload
    end = perf_counter()
    if final is None:
        raise RuntimeError("流中断，没有 done 事件")
    metrics = final.get("metrics", {})
    usage = metrics.get("usage") or {}
    count = usage.get("completion_tokens", usage.get("output_tokens"))
    decode_seconds = end - first if first is not None else None
    return {
        "mode": metrics.get("mode"),
        "ttft_ms": round((first - start) * 1000, 2) if first is not None else None,
        "total_ms": round((end - start) * 1000, 2),
        "output_tokens": count,
        # Approximation: subtract the first token; final event/network overhead is included.
        "decode_tokens_per_second": round(max(count - 1, 0) / decode_seconds, 2)
        if count is not None and decode_seconds and metrics.get("mode") != "demo"
        else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--email", required=True)
    parser.add_argument("--runs", type=int, choices=range(1, 21), default=3)
    parser.add_argument("--question", default="请用五句话解释设备断连时如何收集证据。")
    args = parser.parse_args()
    with httpx.Client(
        base_url=args.url.rstrip("/"), timeout=330, trust_env=False
    ) as client:
        response = client.post(
            "/auth/login",
            json={"email": args.email, "password": getpass.getpass("密码：")},
        )
        response.raise_for_status()
        headers = {"Authorization": "Bearer " + response.json()["access_token"]}
        for run in range(1, args.runs + 1):
            print(
                json.dumps(
                    {"run": run, **measure(client, headers, args.question)},
                    ensure_ascii=False,
                )
            )


if __name__ == "__main__":
    main()
