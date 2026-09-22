import { describe, expect, it } from "vitest";
import { takeFrames } from "./api";
describe("SSE frame assembly", () => {
  it("preserves fragmented JSON and supports CRLF and multiple frames", () => {
    const first = takeFrames('event: delta\r\ndata: {"text":"中');
    expect(first.events).toEqual([]);
    const second = takeFrames(
      first.rest + '文"}\r\n\r\nevent: done\ndata: {}\n\n',
    );
    expect(second.events).toEqual([
      { event: "delta", data: { text: "中文" } },
      { event: "done", data: {} },
    ]);
    expect(second.rest).toBe("");
  });
  it("ignores comments and joins multi-line data", () => {
    expect(
      takeFrames(': heartbeat\n\nevent: delta\ndata: {\ndata: "text":"ok"}\n\n')
        .events,
    ).toEqual([{ event: "delta", data: { text: "ok" } }]);
  });
});
