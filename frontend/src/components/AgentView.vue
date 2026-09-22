<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { api, errorText } from "../api";
import type { AgentRun, Device } from "../types";
const devices = ref<Device[]>([]);
const selected = ref<number | null>(null);
const question = ref("这台设备最近频繁断连，应该如何排查？");
const engine = ref("loop");
const transport = ref("local");
const busy = ref(false);
const error = ref("");
const result = ref<AgentRun | null>(null);
const recent = ref<AgentRun[]>([]);
let controller: AbortController | null = null;
const toolNames: Record<string, string> = {
  get_device: "查询设备登记",
  get_alarm: "读取近期告警",
  search_manual: "检索维修手册",
};
async function run() {
  busy.value = true;
  error.value = "";
  result.value = null;
  controller = new AbortController();
  try {
    result.value = await api<AgentRun>("/agent/runs", {
      method: "POST",
      signal: controller.signal,
      body: JSON.stringify({
        question: question.value,
        device_id: selected.value,
        engine: engine.value,
        transport: transport.value,
      }),
    });
    recent.value = await api<AgentRun[]>("/agent/runs");
  } catch (e) {
    error.value = errorText(e);
  } finally {
    busy.value = false;
    controller = null;
  }
}
onMounted(async () => {
  try {
    devices.value = await api<Device[]>("/devices");
    selected.value = devices.value[0]?.id ?? null;
    recent.value = await api<AgentRun[]>("/agent/runs");
  } catch (e) {
    error.value = errorText(e);
  }
});
onUnmounted(() => controller?.abort());
</script>
<template>
  <section class="page">
    <div class="page-heading">
      <div>
        <span class="eyebrow">DEVICE INVESTIGATION</span>
        <h1>从现象，到排查方向。</h1>
        <p class="muted">结合设备、告警与手册，查看每一步查询结果。</p>
      </div>
      <span class="badge">只读分析 · 不控制设备</span>
    </div>
    <form class="card investigation-form" @submit.prevent="run">
      <div class="form-row">
        <label class="grow"
          >选择设备<select v-model="selected" required>
            <option
              v-for="device in devices"
              :key="device.id"
              :value="device.id"
            >
              {{ device.name }} · {{ device.ip }}
            </option>
          </select></label
        ><label
          >执行方式<select v-model="engine">
            <option value="loop">逐步循环</option>
            <option value="graph">图工作流</option>
          </select></label
        ><label
          >数据连接<select v-model="transport">
            <option value="local">应用内工具</option>
            <option value="mcp">MCP 设备服务</option>
          </select></label
        >
      </div>
      <label
        >描述问题<textarea
          v-model="question"
          rows="3"
          maxlength="4000"
          required
        ></textarea>
      </label>
      <div class="form-footer">
        <span class="hint">分析会返回事实与建议，不能替代现场确认。</span
        ><button class="primary" :disabled="busy || !selected">
          {{ busy ? "正在查询与分析…" : "开始分析 →" }}
        </button>
      </div>
    </form>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <div v-if="busy" class="empty pulse">正在连接设备记录与知识，请稍候…</div>
    <div v-if="result" class="analysis-layout">
      <section class="card">
        <span class="eyebrow">ANALYSIS</span>
        <h2>分析结果</h2>
        <p class="source-text">
          {{ result.answer || "任务未完成，请查看步骤或运行记录。" }}
        </p>
      </section>
      <section class="card">
        <span class="eyebrow">EVIDENCE TRAIL</span>
        <h2>查询过程</h2>
        <div
          v-for="(step, index) in result.steps"
          :key="index"
          class="trace-step"
        >
          <span class="step-number">{{ index + 1 }}</span>
          <div class="grow">
            <strong>{{ toolNames[step.tool] || step.tool }}</strong>
            <p class="muted">
              {{ step.result.ok ? "已返回结果" : "未成功" }} ·
              {{ step.duration_ms }} ms · {{ step.transport }}
            </p>
            <details>
              <summary>查看返回数据</summary>
              <pre>{{ JSON.stringify(step.result, null, 2) }}</pre>
            </details>
          </div>
        </div>
      </section>
    </div>
    <div class="section-title">
      <h2>最近分析</h2>
      <small class="muted">仅展示你自己的任务</small>
    </div>
    <button
      v-for="item in recent"
      :key="item.id"
      class="run-row"
      @click="result = item"
    >
      <span>{{ item.question }}</span
      ><span class="badge">{{
        item.status === "completed"
          ? "已完成"
          : item.status === "failed"
            ? "未完成"
            : "运行中"
      }}</span>
    </button>
  </section>
</template>
