import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import toast from "react-hot-toast";
import Profile from "./Profile";
import { clearAccessToken } from "../api/tokenStore";

const logout = vi.fn().mockResolvedValue(undefined);

vi.mock("react-hot-toast", () => ({
  default: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: {
      user_id: "1",
      name: "Ada",
      email: "ada@example.com",
      available_free_doubts: 3,
    },
    logout,
  }),
}));

vi.mock("../api/authApi", () => ({
  getUserDetails: vi.fn(),
}));

import { getUserDetails } from "../api/authApi";

describe("Profile logout", () => {
  beforeEach(() => {
    clearAccessToken();
    vi.clearAllMocks();
    logout.mockResolvedValue(undefined);
  });

  it("logs out and navigates to login", async () => {
    const user = userEvent.setup();
    getUserDetails.mockResolvedValue({
      name: "Ada",
      email: "ada@example.com",
      available_free_doubts: 3,
      doubts_asked: 2,
      bookmarks: 1,
      first_doubt_asked_at: null,
    });

    render(
      <MemoryRouter initialEntries={["/profile"]}>
        <Routes>
          <Route path="/profile" element={<Profile />} />
          <Route path="/" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /log out of your account/i }),
      ).toBeInTheDocument();
    });

    await user.click(
      screen.getByRole("button", { name: /log out of your account/i }),
    );

    await waitFor(() => {
      expect(logout).toHaveBeenCalled();
      expect(toast.success).toHaveBeenCalledWith("Logged out successfully!");
      expect(screen.getByText("Login page")).toBeInTheDocument();
    });
  });
});
