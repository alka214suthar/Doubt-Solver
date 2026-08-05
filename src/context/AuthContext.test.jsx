import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "../context/AuthContext";
import { clearAccessToken, getAccessToken } from "../api/tokenStore";

vi.mock("../api/authApi", () => ({
  refreshSession: vi.fn(),
  logoutUser: vi.fn(),
  getUserDetails: vi.fn(),
}));

import { getUserDetails, refreshSession } from "../api/authApi";

function SessionProbe() {
  const { user, initializing } = useAuth();
  if (initializing) return <div>initializing</div>;
  if (!user) return <div>logged-out</div>;
  return <div>logged-in:{user.email}</div>;
}

describe("Expired session handling", () => {
  beforeEach(() => {
    clearAccessToken();
    vi.clearAllMocks();
  });

  it("clears the session when auth:logout is dispatched", async () => {
    refreshSession.mockResolvedValue({
      access_token: "token",
      user: {
        user_id: "1",
        name: "Ada",
        email: "ada@example.com",
        available_free_doubts: 4,
      },
    });
    getUserDetails.mockResolvedValue({
      user_id: "1",
      name: "Ada",
      email: "ada@example.com",
      available_free_doubts: 4,
    });

    render(
      <AuthProvider>
        <SessionProbe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("logged-in:ada@example.com")).toBeInTheDocument();
    });

    act(() => {
      clearAccessToken();
      window.dispatchEvent(new Event("auth:logout"));
    });

    await waitFor(() => {
      expect(screen.getByText("logged-out")).toBeInTheDocument();
    });
    expect(getAccessToken()).toBeNull();
  });

  it("ends initializing as logged out when refresh fails", async () => {
    refreshSession.mockRejectedValue(new Error("refresh expired"));

    render(
      <AuthProvider>
        <SessionProbe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("logged-out")).toBeInTheDocument();
    });
  });
});
