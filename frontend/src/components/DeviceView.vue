<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { api, errorText } from "../api";
import { useAuth } from "../stores/auth";
import type { Device, Alarm } from "../types";
const auth = useAuth();
const devices = ref<Device[]>([]);
const error = ref("");
const busy = ref(false);
const editing = ref<number | null>(null);
const form = reactive({
  name: "",
  device_type: "router" as Device["device_type"],
  ip: "",
});
const selected = ref<Device | null>(null);
const alarms = ref<Alarm[]>([]);
const level = ref("warning");
async function refresh() {
  devices.value = await api<Device[]>("/devices");
}
async function save() {
  error.value = "";
  busy.value = true;
  try {
    await api(`/devices${editing.value ? `/${editing.value}` : ""}`, {
      method: editing.value ? "PUT" : "POST",
      body: JSON.stringify(form),
    });
    editing.value = null;
    form.name = "";
    form.ip = "";
    await refresh();
  } catch (e) {
    error.value = errorText(e);
  } finally {
    busy.value = false;
  }
}
function edit(device: Device) {
  editing.value = device.id;
  Object.assign(form, device);
}
async function remove(device: Device) {
  if (!confirm(`删除 ${device.name} 及其所有告警？`)) return;
  try {
    await api(`/devices/${device.id}`, { method: "DELETE" });
    if (selected.value?.id === device.id) selected.value = null;
    await refresh();
  } catch (e) {
    error.value = errorText(e);
  }
}
async function show(device: Device) {
  try {
    alarms.value = await api<Alarm[]>(`/devices/${device.id}/alarms`);
    selected.value = device;
  } catch (e) {
    error.value = errorText(e);
  }
}
async function addAlarm() {
  if (!selected.value) return;
  try {
    await api(`/devices/${selected.value.id}/alarms`, {
      method: "POST",
      body: JSON.stringify({ level: level.value }),
    });
    await show(selected.value);
  } catch (e) {
    error.value = errorText(e);
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
        <span class="eyebrow">DEVICES & SIGNALS</span>
        <h1>设备记录，一处掌握。</h1>
        <p class="muted">登记信息与告警历史，为故障分析提供事实。</p>
      </div>
      <span class="counter">{{ devices.length }} <small>台设备</small></span>
    </div>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <form
      v-if="auth.user?.role === 'admin'"
      class="card device-form"
      @submit.prevent="save"
    >
      <h3>{{ editing ? "编辑设备" : "添加设备" }}</h3>
      <div class="form-row">
        <label>名称<input v-model="form.name" maxlength="100" required /></label
        ><label
          >类型<select v-model="form.device_type">
            <option value="router">路由器</option>
            <option value="switch">交换机</option>
            <option value="camera">摄像头</option>
          </select></label
        ><label
          >IP 地址<input
            v-model="form.ip"
            placeholder="192.0.2.10"
            required /></label
        ><button class="primary" :disabled="busy">
          {{ editing ? "保存修改" : "添加" }}</button
        ><button
          v-if="editing"
          type="button"
          class="outline"
          @click="
            editing = null;
            form.name = '';
            form.ip = '';
          "
        >
          取消
        </button>
      </div>
    </form>
    <div class="device-grid">
      <article v-for="device in devices" :key="device.id" class="device-card">
        <div class="device-card-top">
          <span class="device-symbol">▦</span
          ><span class="badge">{{ device.device_type }}</span>
        </div>
        <h3>{{ device.name }}</h3>
        <p class="muted">
          {{ device.ip }} <span class="subtle">· #{{ device.id }}</span>
        </p>
        <div class="row-actions">
          <button @click="show(device)">查看告警 ↗</button
          ><template v-if="auth.user?.role === 'admin'"
            ><button @click="edit(device)">编辑</button
            ><button @click="remove(device)">删除</button></template
          >
        </div>
      </article>
    </div>
    <p v-if="!devices.length" class="empty">
      暂无设备。管理员可以添加设备，或通过初始化命令加载示例。
    </p>
    <section v-if="selected" class="card alarm-card">
      <div class="section-title">
        <h2>{{ selected.name }} · 最近告警</h2>
        <button class="text-btn" @click="selected = null">关闭 ×</button>
      </div>
      <div v-if="auth.user?.role === 'admin'" class="form-row">
        <label
          >添加测试告警<select v-model="level">
            <option>info</option>
            <option>warning</option>
            <option>critical</option>
          </select></label
        ><button class="outline" @click="addAlarm">添加记录</button>
      </div>
      <p v-if="!alarms.length" class="muted">
        没有告警记录；不代表设备从未发生问题。
      </p>
      <div v-for="alarm in alarms" :key="alarm.id" class="alarm-row">
        <span class="badge" :class="{ danger: alarm.level === 'critical' }">{{
          alarm.level
        }}</span
        ><span>{{ new Date(alarm.created_at).toLocaleString() }}</span
        ><small>#{{ alarm.id }}</small>
      </div>
    </section>
  </section>
</template>
