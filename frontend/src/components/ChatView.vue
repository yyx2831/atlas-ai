<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from "vue";
import { api, downloadDocument, errorText, streamChat } from "../api";
import type { Citation, Conversation, Message } from "../types";
const conversations = ref<Conversation[]>([]);
const messages = ref<Message[]>([]);
const current = ref<string | null>(null);
const question = ref("");
const busy = ref(false);
const error = ref("");
const knowledge = ref(true);
const product = ref("");
const version = ref("");
const topK = ref(5);
const transcript = ref<HTMLElement | null>(null);
const source = ref<Citation | null>(null);
let controller: AbortController | null = null;
function stop() {
  controller?.abort();
}
async function refresh() {
  conversations.value = await api<Conversation[]>("/conversations");
}
async function open(id: string) {
  if (busy.value) return;
  try {
    messages.value = await api<Message[]>(`/conversations/${id}`);
    current.value = id;
  } catch (e) {
    error.value = errorText(e);
  }
}
function reset() {
  if (!busy.value) {
    current.value = null;
    messages.value = [];
    error.value = "";
  }
}
async function remove(id: string) {
  if (!confirm("删除这段会话及其消息？")) return;
  try {
    await api(`/conversations/${id}`, { method: "DELETE" });
    if (current.value === id) reset();
    await refresh();
  } catch (e) {
    error.value = errorText(e);
  }
}
async function send() {
  if (!question.value.trim() || busy.value) return;
  const prompt = question.value.trim();
  question.value = "";
  error.value = "";
  busy.value = true;
  messages.value.push({
    role: "user",
    content: prompt,
    status: "completed",
    citations: [],
  });
  const index = messages.value.length;
  messages.value.push({
    role: "assistant",
    content: "",
    status: "pending",
    citations: [],
  });
  controller = new AbortController();
  try {
    await streamChat(
      {
        question: prompt,
        conversation_id: current.value,
        use_knowledge: knowledge.value,
        product: product.value,
        version: version.value,
        top_k: topK.value,
      },
      controller.signal,
      (event) => {
        if (event.event === "meta")
          current.value = String(event.data.conversation_id);
        if (event.event === "delta")
          messages.value[index]!.content += String(event.data.text);
        if (event.event === "done") {
          messages.value[index]!.content = String(event.data.answer);
          messages.value[index]!.citations = event.data.citations as Citation[];
          messages.value[index]!.metrics = event.data.metrics as Record<
            string,
            unknown
          >;
          messages.value[index]!.status = "completed";
        }
        void nextTick(() => {
          transcript.value?.scrollTo({ top: transcript.value.scrollHeight });
        });
      },
    );
  } catch (e) {
    const cancelled = controller.signal.aborted;
    messages.value[index]!.status = cancelled ? "cancelled" : "failed";
    error.value = cancelled
      ? "已停止生成，部分回答保留在历史中。"
      : errorText(e);
  } finally {
    busy.value = false;
    controller = null;
    await refresh().catch(() => {});
  }
}
async function download(c: Citation) {
  try {
    await downloadDocument(c.document_id, c.filename);
  } catch (e) {
    error.value = errorText(e);
  }
}
onMounted(() =>
  refresh().catch((e) => {
    error.value = errorText(e);
  }),
);
onUnmounted(() => controller?.abort());
</script>
<template>
  <section class="chat-layout">
    <aside class="history">
      <button class="outline full" :disabled="busy" @click="reset">
        ＋ 新建会话
      </button>
      <h3 class="nav-label">最近会话</h3>
      <div
        v-for="c in conversations"
        :key="c.id"
        class="history-item"
        :class="{ selected: current === c.id }"
      >
        <button :disabled="busy" @click="open(c.id)">{{ c.title }}</button
        ><button
          :disabled="busy"
          aria-label="删除会话"
          class="delete-small"
          @click="remove(c.id)"
        >
          ×
        </button>
      </div>
      <p v-if="!conversations.length" class="hint">
        你的问答记录会保存在这里。
      </p>
    </aside>
    <div class="chat-main">
      <div ref="transcript" class="transcript" aria-live="polite">
        <div v-if="!messages.length" class="welcome">
          <span class="orbit">◈</span
          ><span class="eyebrow">YOUR KNOWLEDGE, CONNECTED</span>
          <h1>让设备问题，<br /><em>有据可查。</em></h1>
          <p class="muted">从维修手册中找到线索，每个回答都能回到来源。</p>
          <div class="prompt-grid">
            <button @click="question = '设备频繁断连应该检查哪些地方？'">
              设备频繁断连<br /><small>寻找排查步骤 ↗</small></button
            ><button @click="question = 'ERR-1007 是什么意思？'">
              错误代码 ERR-1007<br /><small>查找手册依据 ↗</small>
            </button>
          </div>
        </div>
        <article
          v-for="(m, index) in messages"
          :key="m.id ?? index"
          class="message"
          :class="m.role"
        >
          <div class="message-label">
            {{ m.role === "user" ? "你" : "◈ ATLAS"
            }}<small v-if="m.status !== 'completed'">
              ·
              {{
                { pending: "生成中", failed: "未完成", cancelled: "已停止" }[
                  m.status
                ] || m.status
              }}</small
            >
          </div>
          <div class="message-text">{{ m.content || "正在查找依据…" }}</div>
          <div v-if="m.citations.length" class="citations">
            <button v-for="c in m.citations" :key="c.id" @click="source = c">
              <span>{{ c.label }}</span
              >{{ c.filename }} · 第 {{ c.page }} 页 ↗
            </button>
          </div>
        </article>
      </div>
      <form class="composer" @submit.prevent="send">
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <textarea
          v-model="question"
          aria-label="输入问题"
          placeholder="描述你的问题，例如：设备频繁断连应该先检查什么？"
          :disabled="busy"
          rows="2"
          @keydown.ctrl.enter.prevent="send"
        ></textarea>
        <div class="composer-options">
          <label class="inline"
            ><input v-model="knowledge" type="checkbox" />使用知识库</label
          ><input
            v-model="product"
            aria-label="产品筛选"
            placeholder="产品（可选）"
          /><input
            v-model="version"
            aria-label="版本筛选"
            placeholder="版本"
          /><label class="inline"
            >Top K
            <select v-model="topK">
              <option :value="3">3</option>
              <option :value="5">5</option>
              <option :value="10">10</option>
            </select></label
          >
          <button v-if="busy" type="button" class="outline" @click="stop">
            停止</button
          ><button v-else class="primary" :disabled="!question.trim()">
            发送 ↑
          </button>
        </div>
      </form>
      <p class="composer-note">
        回答可能不完整。请核对引用，设备操作仍需遵循现场安全流程。
      </p>
    </div>
    <div v-if="source" class="modal-backdrop" @click.self="source = null">
      <section
        class="modal"
        role="dialog"
        aria-modal="true"
        aria-label="引用来源"
      >
        <button class="modal-close" @click="source = null">关闭 ×</button
        ><span class="eyebrow">SOURCE / {{ source.label }}</span>
        <h2>{{ source.filename }}</h2>
        <p class="muted">第 {{ source.page }} 页 · 本次检索原文片段</p>
        <p class="source-text">{{ source.content }}</p>
        <button class="outline" @click="download(source)">下载原文</button>
      </section>
    </div>
  </section>
</template>
