import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import toast from "react-hot-toast";
import Login from "../pages/Login";
import { AuthProvider } from "../context/AuthContext";
import { clearAccessToken } from "../api/tokenStore";

vi.mock("react-hot-toast", () => ({
  default: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

vi.mock("../api/authApi", () => ({
  loginUser: vi.fn(),
  registerUser: vi.fn(),
  getUserDetails: vi.fn(),
  refreshSession: vi.fn().mockRejectedValue(new Error("no session")),
  logoutUser: vi.fn(),
}));

import { getUserDetails, loginUser } from "../api/authApi";

function renderLogin() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/ask-doubt" element={<div>Ask Doubt Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe("Login", () => {
  beforeEach(() => {
    clearAccessToken();
    vi.clearAllMocks();
  });

  it("shows validation errors when fields are empty", async () => {
    const user = userEvent.setup();
    renderLogin();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /login/i }));

    expect(await screen.findByText("Email is required")).toBeInTheDocument();
    expect(screen.getByText("Password is required")).toBeInTheDocument();
    expect(loginUser).not.toHaveBeenCalled();
  });

  it("logs in successfully and navigates", async () => {
    const user = userEvent.setup();
    loginUser.mockResolvedValue({
      access_token: "token",
      user: {
        user_id: "1",
        name: "Ada",
        email: "ada@example.com",
        available_free_doubts: 10,
      },
    });
    getUserDetails.mockResolvedValue({
      user_id: "1",
      name: "Ada",
      email: "ada@example.com",
      available_free_doubts: 10,
      doubts_asked: 0,
      bookmarks: 0,
    });

    renderLogin();

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/enter email/i)).toBeInTheDocument();
    });

    await user.type(screen.getByPlaceholderText(/enter email/i), "ada@example.com");
    await user.type(screen.getByPlaceholderText(/enter password/i), "secret123");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(loginUser).toHaveBeenCalledWith({
        email: "ada@example.com",
        password: "secret123",
      });
      expect(toast.success).toHaveBeenCalledWith("Login successful!");
      expect(screen.getByText("Ask Doubt Page")).toBeInTheDocument();
    });
  });
});
