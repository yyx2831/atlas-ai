/** 唯一 HTTP 入口。组件只处理业务数据，不重复拼认证头和错误信息。 */
export function authHeaders(): Record<string, string> {
  const token = sessionStorage.getItem("atlas-token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function checked(response: Response): Promise<Response> {
  if (!response.ok) {
    if (response.status === 401)
      window.dispatchEvent(new Event("atlas:unauthorized"));
    const error = await response.json().catch(() => ({}));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : `请求失败（${response.status}），请检查输入`,
    );
  }
  return response;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await checked(
    await fetch(`/api${path}`, {
      ...init,
      headers: {
        ...authHeaders(),
        ...(init.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" }),
        ...init.headers,
      },
    }),
  );
  return response.status === 204 ? (undefined as T) : response.json();
}

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

/** 网络 chunk 不等于 SSE 帧：保留尾部半帧，下一个 chunk 到来后继续拼接。 */
export function takeFrames(buffer: string): {
  events: SSEEvent[];
  rest: string;
} {
  const events: SSEEvent[] = [];
  let match: RegExpExecArray | null;
  while ((match = /\r?\n\r?\n/.exec(buffer))) {
    const frame = buffer.slice(0, match.index);
    buffer = buffer.slice(match.index + match[0].length);
    let event = "message";
    const data: string[] = [];
    for (const line of frame.split(/\r?\n/)) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    if (data.length) events.push({ event, data: JSON.parse(data.join("\n")) });
  }
  return { events, rest: buffer };
}

export async function streamChat(
  body: unknown,
  signal: AbortSignal,
  onEvent: (event: SSEEvent) => void,
) {
  const response = await checked(
    await fetch("/api/chat/stream", {
      method: "POST",
      signal,
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  );
  if (!response.body) throw new Error("浏览器不支持流式响应");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const result = takeFrames(buffer);
      buffer = result.rest;
      if (buffer.length > 200_000) throw new Error("流式消息过大");
      for (const event of result.events) {
        onEvent(event);
        if (event.event === "done") completed = true;
        if (event.event === "error") throw new Error(String(event.data.detail));
      }
    }
    if (!completed) throw new Error("连接中断，回答未完成，可稍后查看历史状态");
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

export async function downloadDocument(id: string, filename: string) {
  const response = await checked(
    await fetch(`/api/knowledge/documents/${id}/file`, {
      headers: authHeaders(),
    }),
  );
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const errorText = (error: unknown) =>
  error instanceof Error ? error.message : "操作失败，请重试";
