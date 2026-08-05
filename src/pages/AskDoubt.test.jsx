import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import toast from "react-hot-toast";
import AskDoubt from "./AskDoubt";

const mockUser = {
  user_id: "1",
  name: "Ada",
  email: "ada@example.com",
  available_free_doubts: 5,
};

const mockSetUser = vi.fn();
const mockRefreshUser = vi.fn().mockResolvedValue({
  available_free_doubts: 5,
  doubts_asked: 0,
});

vi.mock("react-hot-toast", () => ({
  default: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: mockUser,
    setUser: mockSetUser,
    refreshUser: mockRefreshUser,
  }),
}));

vi.mock("../api/doubtApi", () => ({
  solveDoubt: vi.fn(),
  submitFeedback: vi.fn(),
  submitBookmark: vi.fn(),
}));

vi.mock("../components/MarkdownAnswer", () => ({
  default: ({ content }) => <div>{content}</div>,
}));

import { solveDoubt, submitBookmark } from "../api/doubtApi";

function renderAskDoubt() {
  return render(
    <MemoryRouter>
      <AskDoubt />
    </MemoryRouter>,
  );
}

async function fillAndSubmit(user, question = "What is 2+2?") {
  await waitFor(() => {
    expect(screen.getByRole("button", { name: /solve doubt/i })).toBeEnabled();
  });

  await user.type(screen.getByPlaceholderText(/type your doubt/i), question);
  await user.selectOptions(screen.getByLabelText(/^subject$/i), "Mathematics");
  await user.selectOptions(screen.getByLabelText(/^class$/i), "8");
  await user.click(screen.getByRole("button", { name: /solve doubt/i }));
}

describe("AskDoubt", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRefreshUser.mockResolvedValue({
      available_free_doubts: 5,
      doubts_asked: 0,
    });
  });

  it("shows loading state while solving", async () => {
    const user = userEvent.setup();
    let resolveSolve;
    solveDoubt.mockReturnValue(
      new Promise((resolve) => {
        resolveSolve = resolve;
      }),
    );

    renderAskDoubt();
    await fillAndSubmit(user);

    expect(await screen.findByText("Solving doubt...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /solving/i })).toBeDisabled();

    resolveSolve({
      doubt_id: "d1",
      answer: "4",
      hints: ["Add"],
      steps: ["2+2=4"],
    });

    await waitFor(() => {
      expect(screen.getByText("4")).toBeInTheDocument();
    });
  });

  it("shows API error state when solve fails", async () => {
    const user = userEvent.setup();
    solveDoubt.mockRejectedValue({
      response: {
        data: {
          error: {
            code: "LLM_PROVIDER_ERROR",
            message:
              "The AI service is temporarily unavailable. Please try again later.",
          },
        },
      },
    });

    renderAskDoubt();
    await fillAndSubmit(user, "Hard question");

    expect(
      await screen.findByText(
        /the ai service is temporarily unavailable\. please try again later\./i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("submits a doubt successfully", async () => {
    const user = userEvent.setup();
    solveDoubt.mockResolvedValue({
      doubt_id: "d1",
      answer: "The answer is 4.",
      hints: ["Think addition"],
      steps: ["Add the numbers"],
    });

    renderAskDoubt();
    await fillAndSubmit(user);

    await waitFor(() => {
      expect(solveDoubt).toHaveBeenCalled();
      expect(screen.getByText("The answer is 4.")).toBeInTheDocument();
    });
  });

  it("bookmarks a solved doubt", async () => {
    const user = userEvent.setup();
    solveDoubt.mockResolvedValue({
      doubt_id: "d1",
      answer: "42",
      hints: ["hint"],
      steps: ["step"],
    });
    submitBookmark.mockResolvedValue({ isBookmarkSubmitted: true });

    renderAskDoubt();
    await fillAndSubmit(user, "Meaning of life?");

    await waitFor(() => {
      expect(screen.getByText("42")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /bookmark doubt/i }));

    await waitFor(() => {
      expect(submitBookmark).toHaveBeenCalledWith({
        doubt_id: "d1",
        is_bookmarked: true,
      });
      expect(toast.success).toHaveBeenCalledWith("Doubt bookmarked successfully!");
    });
  });
});
