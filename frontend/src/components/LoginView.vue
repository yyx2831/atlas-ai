<script setup lang="ts">
import { ref } from "vue";
import { useAuth } from "../stores/auth";
import { errorText } from "../api";
const auth = useAuth();
const email = ref("");
const password = ref("");
const busy = ref(false);
const error = ref("");
async function submit() {
  busy.value = true;
  error.value = "";
  try {
    await auth.login(email.value, password.value);
  } catch (e) {
    error.value = errorText(e);
  } finally {
    busy.value = false;
  }
}
</script>
<template>
  <main class="login-layout">
    <section class="login-story">
      <div class="brand">
        ◈ <span>ATLAS <small>AI WORKSPACE</small></span>
      </div>
      <div>
        <span class="eyebrow">KNOWLEDGE INTO ACTION</span>
        <h1>每一个设备问题，<br />都有迹可循。</h1>
        <p>连接设备记录、告警与维修知识。<br />让排查从有依据的回答开始。</p>
      </div>
      <span class="subtle">你的知识 · 你的工作空间</span>
    </section>
    <section class="login-form">
      <span class="eyebrow">WELCOME BACK</span>
      <h2>进入 Atlas</h2>
      <p class="muted">使用管理员为你创建的账户登录。</p>
      <form @submit.prevent="submit">
        <label
          >邮箱<input
            v-model="email"
            type="email"
            autocomplete="username"
            required
            placeholder="you@company.com"
        /></label>
        <label
          >密码<input
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
        /></label>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <button class="primary" :disabled="busy">
          {{ busy ? "正在登录…" : "登录工作空间 →" }}
        </button>
      </form>
      <p class="hint">
        首次使用？请按照项目 README 初始化管理员账户。系统不提供默认密码。
      </p>
    </section>
  </main>
</template>
