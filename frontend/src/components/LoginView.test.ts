import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { describe, expect, it, vi } from "vitest";
import LoginView from "./LoginView.vue";
import { useAuth } from "../stores/auth";
describe("login form", () => {
  it("passes credentials to the auth store and shows failure without losing input", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const auth = useAuth();
    const login = vi
      .spyOn(auth, "login")
      .mockRejectedValue(new Error("账户或密码错误"));
    const wrapper = mount(LoginView, { global: { plugins: [pinia] } });
    await wrapper.get("input[type=email]").setValue("learner@example.test");
    await wrapper.get("input[type=password]").setValue("password-example");
    await wrapper.get("form").trigger("submit");
    await vi.waitFor(() =>
      expect(wrapper.get("[role=alert]").text()).toContain("账户或密码错误"),
    );
    expect(login).toHaveBeenCalledWith(
      "learner@example.test",
      "password-example",
    );
    expect(
      (wrapper.get("input[type=email]").element as HTMLInputElement).value,
    ).toBe("learner@example.test");
  });
});
