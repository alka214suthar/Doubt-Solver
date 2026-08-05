import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import toast from "react-hot-toast";
import Register from "./Register";
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

import { getUserDetails, registerUser } from "../api/authApi";

function renderRegister() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="/register" element={<Register />} />
          <Route path="/ask-doubt" element={<div>Ask Doubt Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe("Register", () => {
  beforeEach(() => {
    clearAccessToken();
    vi.clearAllMocks();
  });

  it("shows validation error when passwords do not match", async () => {
    const user = userEvent.setup();
    renderRegister();

    await waitFor(() => {
      expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/^name$/i), "Ada");
    await user.type(screen.getByLabelText(/^email$/i), "ada@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "secret123");
    await user.type(screen.getByLabelText(/confirm password/i), "different");
    await user.click(screen.getByRole("button", { name: /register/i }));

    expect(await screen.findByText("Passwords do not match")).toBeInTheDocument();
    expect(registerUser).not.toHaveBeenCalled();
  });

  it("registers successfully when form is valid", async () => {
    const user = userEvent.setup();
    registerUser.mockResolvedValue({
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

    renderRegister();

    await waitFor(() => {
      expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/^name$/i), "Ada");
    await user.type(screen.getByLabelText(/^email$/i), "ada@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "secret123");
    await user.type(screen.getByLabelText(/confirm password/i), "secret123");
    await user.click(screen.getByRole("button", { name: /register/i }));

    await waitFor(() => {
      expect(registerUser).toHaveBeenCalled();
      expect(toast.success).toHaveBeenCalledWith("Registration successful!");
      expect(screen.getByText("Ask Doubt Page")).toBeInTheDocument();
    });
  });
});
