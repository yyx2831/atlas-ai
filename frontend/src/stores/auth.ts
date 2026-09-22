import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api";
import type { User } from "../types";

export const useAuth = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const ready = ref(false);
  async function restore() {
    try {
      if (sessionStorage.getItem("atlas-token"))
        user.value = await api<User>("/auth/me");
    } catch {
      logout();
    } finally {
      ready.value = true;
    }
  }
  async function login(email: string, password: string) {
    const result = await api<{ access_token: string; user: User }>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      },
    );
    sessionStorage.setItem("atlas-token", result.access_token);
    user.value = result.user;
  }
  function logout() {
    sessionStorage.removeItem("atlas-token");
    user.value = null;
  }
  return { user, ready, restore, login, logout };
});
