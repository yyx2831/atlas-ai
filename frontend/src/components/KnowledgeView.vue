<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, downloadDocument, errorText } from "../api";
import type { Document } from "../types";
const documents = ref<Document[]>([]);
const file = ref<File | null>(null);
const product = ref("router");
const version = ref("v1");
const error = ref("");
const notice = ref("");
const busy = ref(false);
const input = ref<HTMLInputElement | null>(null);
const preview = ref<{
  filename: string;
  chunks: { id: string; page: number; content: string }[];
} | null>(null);
const labels: Record<string, string> = {
  ready: "可检索",
  indexing: "索引中",
  failed: "失败",
  deleting: "删除待重试",
};
async function refresh() {
  documents.value = await api<Document[]>("/knowledge/documents");
}
async function upload() {
  if (!file.value) return;
  busy.value = true;
  error.value = "";
  notice.value = "";
  const data = new FormData();
  data.append("file", file.value);
  data.append("product", product.value);
  data.append("version", version.value);
  try {
    const doc = await api<Document>("/knowledge/documents", {
      method: "POST",
      body: data,
    });
    notice.value = `${doc.filename} 已处理，可在知识问答中使用。`;
    file.value = null;
    if (input.value) input.value.value = "";
    await refresh();
  } catch (e) {
    error.value = errorText(e);
    await refresh().catch(() => {});
  } finally {
    busy.value = false;
  }
}
async function action(
  doc: Document,
  mode: "delete" | "reindex" | "preview" | "download",
) {
  if (mode === "delete" && !confirm(`删除 ${doc.filename} 及其索引？`)) return;
  busy.value = true;
  error.value = "";
  try {
    if (mode === "preview")
      preview.value = await api(`/knowledge/documents/${doc.id}`);
    else if (mode === "download") await downloadDocument(doc.id, doc.filename);
    else {
      await api(
        `/knowledge/documents/${doc.id}${mode === "reindex" ? "/reindex" : ""}`,
        { method: mode === "delete" ? "DELETE" : "POST" },
      );
      await refresh();
    }
  } catch (e) {
    error.value = errorText(e);
  } finally {
    busy.value = false;
  }
}
onMounted(() =>
  refresh().catch((e) => {
    error.value = errorText(e);
  }),
);
</script>
<template>
  <section class="page">
    <div class="page-heading">
      <div>
        <span class="eyebrow">KNOWLEDGE BASE</span>
        <h1>把经验，变成依据。</h1>
        <p class="muted">上传维修手册与故障记录。仅你自己的文档参与检索。</p>
      </div>
      <span class="counter">{{ documents.length }} <small>份文档</small></span>
    </div>
    <form class="upload-card" @submit.prevent="upload">
      <div>
        <span class="upload-icon">↑</span>
        <h3>添加一份知识</h3>
        <p class="muted">
          PDF、TXT、Markdown · 最多 5 MB<br />扫描 PDF 请先完成 OCR。
        </p>
      </div>
      <div class="upload-fields">
        <label
          >选择文件<input
            ref="input"
            type="file"
            accept=".pdf,.txt,.md"
            required
            @change="
              file = ($event.target as HTMLInputElement).files?.[0] ?? null
            "
        /></label>
        <div class="two-col">
          <label>产品<input v-model="product" maxlength="80" required /></label
          ><label
            >版本<input v-model="version" maxlength="80" required
          /></label>
        </div>
        <button class="primary" :disabled="busy || !file">
          {{ busy ? "正在处理…" : "上传并建立索引" }}
        </button>
      </div>
    </form>
    <p v-if="error" role="alert" class="error">{{ error }}</p>
    <p v-if="notice" class="success">{{ notice }}</p>
    <div class="section-title">
      <h2>我的文档</h2>
      <button
        class="text-btn"
        @click="refresh().catch((e) => (error = errorText(e)))"
      >
        刷新 ↻
      </button>
    </div>
    <div v-if="!documents.length" class="empty">
      还没有文档。上传第一份手册，开始有依据的问答。
    </div>
    <div v-for="doc in documents" :key="doc.id" class="document-row">
      <div class="file-icon">文</div>
      <div class="grow">
        <strong>{{ doc.filename }}</strong>
        <p class="muted">
          {{ doc.product }} / {{ doc.version }} ·
          {{ new Date(doc.created_at).toLocaleDateString() }}
        </p>
        <small v-if="doc.error" class="error">{{ doc.error }}</small>
      </div>
      <span class="badge" :class="{ danger: doc.status === 'failed' }">{{
        labels[doc.status] || doc.status
      }}</span>
      <div class="row-actions">
        <button :disabled="busy" @click="action(doc, 'preview')">查看</button
        ><button :disabled="busy" @click="action(doc, 'download')">下载</button
        ><button :disabled="busy" @click="action(doc, 'reindex')">重建</button
        ><button :disabled="busy" @click="action(doc, 'delete')">删除</button>
      </div>
    </div>
    <div v-if="preview" class="modal-backdrop" @click.self="preview = null">
      <section
        class="modal"
        role="dialog"
        aria-modal="true"
        aria-label="文档内容"
      >
        <button class="modal-close" @click="preview = null">关闭 ×</button>
        <h2>{{ preview.filename }}</h2>
        <article v-for="chunk in preview.chunks" :key="chunk.id">
          <p class="eyebrow">第 {{ chunk.page }} 页</p>
          <p class="source-text">{{ chunk.content }}</p>
          <hr />
        </article>
      </section>
    </div>
  </section>
</template>
