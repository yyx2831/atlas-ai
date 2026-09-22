<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import { useAuth } from "./stores/auth";
import { api } from "./api";
import type { SystemInfo } from "./types";
import LoginView from "./components/LoginView.vue";
import ChatView from "./components/ChatView.vue";
import KnowledgeView from "./components/KnowledgeView.vue";
import DeviceView from "./components/DeviceView.vue";
import AgentView from "./components/AgentView.vue";
import SettingsView from "./components/SettingsView.vue";

const auth = useAuth();
const active = ref("chat");
const info = ref<SystemInfo | null>(null);
const tabs = [
  { id: "chat", name: "知识问答", icon: "◌" },
  { id: "knowledge", name: "知识库", icon: "▤" },
  { id: "devices", name: "设备与告警", icon: "▦" },
  { id: "agent", name: "故障分析", icon: "◇" },
  { id: "settings", name: "工作空间", icon: "⚙" },
];
watch(
  () => auth.user,
  async (user) => {
    info.value = user
      ? await api<SystemInfo>("/system/info").catch(() => null)
      : null;
  },
);
onMounted(() => {
  void auth.restore();
  window.addEventListener("atlas:unauthorized", auth.logout);
});
onUnmounted(() =>
  window.removeEventListener("atlas:unauthorized", auth.logout),
);
</script>
<template>
  <div v-if="!auth.ready" class="loading">正在连接工作空间…</div>
  <LoginView v-else-if="!auth.user" />
  <div v-else class="workspace">
    <aside class="sidebar">
      <div class="brand">
        ◈ <span>ATLAS <small>AI WORKSPACE</small></span>
      </div>
      <p class="nav-label">工作空间</p>
      <nav aria-label="主导航">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="{ active: active === tab.id }"
          @click="active = tab.id"
        >
          <span>{{ tab.icon }}</span
          >{{ tab.name }}
        </button>
      </nav>
      <div class="sidebar-note">
        <span class="status-dot"></span>
        {{ info?.llm_mode === "demo" ? "演示模式" : "模型已配置" }}
        <p>先查询事实，再形成判断。<br />每一步，保留可核验的依据。</p>
      </div>
      <div class="user-box">
        <div class="avatar">{{ auth.user.email[0]?.toUpperCase() }}</div>
        <div>
          <strong>{{ auth.user.email }}</strong
          ><small>{{ auth.user.role === "admin" ? "管理员" : "成员" }}</small>
        </div>
        <button class="icon-btn" aria-label="退出登录" @click="auth.logout">
          ↪
        </button>
      </div>
    </aside>
    <main class="main">
      <header class="topbar">
        <div>
          <span class="muted">Atlas / </span
          >{{ tabs.find((t) => t.id === active)?.name }}
        </div>
        <span class="badge">{{
          info?.llm_mode === "demo"
            ? "演示 · 不代表真实模型推理"
            : info?.model || "模型配置待检查"
        }}</span>
      </header>
      <ChatView v-if="active === 'chat'" />
      <KnowledgeView v-else-if="active === 'knowledge'" />
      <DeviceView v-else-if="active === 'devices'" />
      <AgentView v-else-if="active === 'agent'" />
      <SettingsView v-else :info="info" />
    </main>
  </div>
</template>
