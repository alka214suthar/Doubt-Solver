import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import MainLayout from "../Layouts/MainLayout";
import { AuthProvider } from "../context/AuthContext";
import { clearAccessToken } from "../api/tokenStore";

vi.mock("../api/authApi", () => ({
  loginUser: vi.fn(),
  registerUser: vi.fn(),
  getUserDetails: vi.fn(),
  refreshSession: vi.fn(),
  logoutUser: vi.fn(),
}));

vi.mock("../components/Navbar", () => ({
  default: () => <nav>Navbar</nav>,
}));

import { getUserDetails, refreshSession } from "../api/authApi";

const profile = {
  user_id: "1",
  name: "Ada",
  email: "ada@example.com",
  available_free_doubts: 5,
  doubts_asked: 0,
  bookmarks: 0,
};

describe("MainLayout protected routes", () => {
  beforeEach(() => {
    clearAccessToken();
    vi.clearAllMocks();
  });

  it("shows loading state while session is restoring", () => {
    refreshSession.mockReturnValue(new Promise(() => {}));

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/ask-doubt"]}>
          <Routes>
            <Route element={<MainLayout />}>
              <Route path="/ask-doubt" element={<div>Protected content</div>} />
            </Route>
            <Route path="/" element={<div>Login page</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    );

    expect(screen.getByText(/restoring your session/i)).toBeInTheDocument();
  });

  it("redirects unauthenticated users to login", async () => {
    refreshSession.mockRejectedValue(new Error("expired"));

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/ask-doubt"]}>
          <Routes>
            <Route element={<MainLayout />}>
              <Route path="/ask-doubt" element={<div>Protected content</div>} />
            </Route>
            <Route path="/" element={<div>Login page</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("Login page")).toBeInTheDocument();
    });
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });

  it("renders protected content for authenticated users", async () => {
    refreshSession.mockResolvedValue({
      access_token: "token",
      user: profile,
    });
    getUserDetails.mockResolvedValue(profile);

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/ask-doubt"]}>
          <Routes>
            <Route element={<MainLayout />}>
              <Route path="/ask-doubt" element={<div>Protected content</div>} />
            </Route>
            <Route path="/" element={<div>Login page</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("Protected content")).toBeInTheDocument();
    });
  });
});
