import { describe, it, expect, vi, beforeEach } from "vitest";
import MockAdapter from "axios-mock-adapter";
import axios from "axios";

vi.mock("./config", () => ({
  API_BASE_URL: "http://localhost:8000/api/v1",
}));

describe("axios expired-session interceptor", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  it("dispatches auth:logout when refresh fails after a 401", async () => {
    const { default: api } = await import("./axios");
    const tokenStore = await import("./tokenStore");
    tokenStore.clearAccessToken();
    tokenStore.setAccessToken("expired-access");

    const logoutListener = vi.fn();
    window.addEventListener("auth:logout", logoutListener);

    const apiMock = new MockAdapter(api);
    apiMock.onGet("/user_doubts").replyOnce(401);

    const refreshMock = new MockAdapter(axios);
    refreshMock.onPost("http://localhost:8000/api/v1/auth/refresh").reply(401);

    await expect(api.get("/user_doubts")).rejects.toBeTruthy();

    expect(logoutListener).toHaveBeenCalled();
    expect(tokenStore.getAccessToken()).toBeNull();

    window.removeEventListener("auth:logout", logoutListener);
    refreshMock.restore();
    apiMock.restore();
  });
});
