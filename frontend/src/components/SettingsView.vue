<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { api, errorText } from "../api";
import { useAuth } from "../stores/auth";
import type { SystemInfo, User } from "../types";
defineProps<{ info: SystemInfo | null }>();
const auth = useAuth();
const users = ref<User[]>([]);
const form = reactive({ email: "", password: "", role: "viewer" });
const error = ref("");
const notice = ref("");
const busy = ref(false);
async function loadUsers() {
  if (auth.user?.role === "admin")
    users.value = await api<User[]>("/auth/users");
}
async function add() {
  error.value = "";
  notice.value = "";
  busy.value = true;
  try {
    await api("/auth/users", { method: "POST", body: JSON.stringify(form) });
    notice.value = "账户已创建";
    form.email = "";
    form.password = "";
    await loadUsers();
  } catch (e) {
    error.value = errorText(e);
  } finally {
    busy.value = false;
  }
}
onMounted(() =>
  loadUsers().catch((e) => {
    error.value = errorText(e);
  }),
);
</script>
<template>
  <section class="page">
    <div class="page-heading">
      <div>
        <span class="eyebrow">WORKSPACE</span>
        <h1>了解你的工作空间。</h1>
        <p class="muted">确认当前能力，再开始使用。</p>
      </div>
    </div>
    <div class="settings-grid">
      <article class="card">
        <h2>当前模式</h2>
        <p class="big-text">
          {{ info?.llm_mode === "demo" ? "演示模式" : "真实模型接口" }}
        </p>
        <p class="muted">
          {{
            info?.llm_mode === "demo"
              ? "用于学习完整业务流程。演示回答是确定性生成，不代表真实推理能力。"
              : `当前模型：${info?.model}`
          }}
        </p>
        <p class="hint">
          {{
            info?.embedding_mode === "demo"
              ? "检索使用教学哈希向量，不等同语义 Embedding。"
              : "检索已配置 Embedding 服务。"
          }}
        </p>
      </article>
      <article class="card">
        <h2>数据与权限</h2>
        <p>设备记录为工作空间共享。文档、会话与分析记录仅由创建者访问。</p>
        <p class="muted">
          管理员可维护设备、告警与账户。当前工具只读，不会执行真实设备操作。
        </p>
        <p class="hint">重排：{{ info?.reranker }}</p>
      </article>
    </div>
    <section v-if="auth.user?.role === 'admin'" class="card account-card">
      <h2>创建成员账户</h2>
      <form @submit.prevent="add">
        <div class="form-row">
          <label class="grow"
            >邮箱<input v-model="form.email" type="email" required /></label
          ><label class="grow"
            >初始密码<input
              v-model="form.password"
              type="password"
              minlength="12"
              maxlength="128"
              autocomplete="new-password"
              required /></label
          ><label
            >角色<select v-model="form.role">
              <option value="viewer">成员</option>
              <option value="admin">管理员</option>
            </select></label
          ><button class="primary" :disabled="busy">创建</button>
        </div>
      </form>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <p v-if="notice" class="success">{{ notice }}</p>
      <div v-for="user in users" :key="user.id" class="alarm-row">
        <span class="grow">{{ user.email }}</span
        ><span class="badge">{{
          user.role === "admin" ? "管理员" : "成员"
        }}</span>
      </div>
    </section>
  </section>
</template>
