import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { submitBookmark, submitFeedback } from "../api/doubtApi";
import { apiUrl } from "../api/config";
import { getUserFacingError } from "../api/getUserFacingError";
import MarkdownAnswer from "../components/MarkdownAnswer";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";

function DoubtDetails() {
  const navigate = useNavigate();
  const location = useLocation();

  const {
    id,
    question,
    subject,
    class_name,
    status,
    answer,
    hints,
    steps,
    imageUrl,
    isHelpful,
    createdAt,
    isBookmarked,
  } = location.state || {};

  const hasDoubtPayload = Boolean(location.state && id);
  const [error, setError] = useState("");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [bookmarkLoading, setBookmarkLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const [is_Bookmarked, setIsBookmarked] = useState(Boolean(isBookmarked));
  const [feedbackHelpful, setFeedbackHelpful] = useState(
    isHelpful === true ? true : isHelpful === false ? false : null,
  );

  const toggleBookmark = async () => {
    if (!id) {
      setError("Missing doubt details. Open this doubt again from History.");
      return;
    }

    const nextBookmarked = !is_Bookmarked;
    try {
      setBookmarkLoading(true);
      setError("");
      await submitBookmark({
        doubt_id: id,
        is_bookmarked: nextBookmarked,
      });
      setIsBookmarked(nextBookmarked);
      const message = nextBookmarked
        ? "Doubt bookmarked successfully!"
        : "Bookmark removed successfully!";
      setSuccessMessage(message);
      toast.success(message);
    } catch (err) {
      const message = getUserFacingError(
        err,
        "Unable to update bookmark right now.",
      );
      setError(message);
      toast.error(message);
    } finally {
      setBookmarkLoading(false);
    }
  };

  const handleFeedbackSubmit = async (is_doubt_helpful) => {
    if (!id) {
      const message = "Missing doubt details. Open this doubt again from History.";
      setError(message);
      toast.error(message);
      return;
    }

    try {
      setSubmittingFeedback(true);
      setError("");
      await submitFeedback({
        doubt_id: id,
        is_doubt_helpful,
      });
      setFeedbackHelpful(is_doubt_helpful);
      setSuccessMessage("Thank you for your feedback!");
      toast.success("Thank you for your feedback!");
    } catch (err) {
      const message = getUserFacingError(
        err,
        "Unable to submit feedback right now.",
      );
      setError(message);
      toast.error(message);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const doubt = {
    id: id ?? null,
    question: question ?? "Untitled doubt",
    subject: subject ?? "Unknown subject",
    className: class_name ?? "Unknown class",
    status: String(status ?? (answer ? "solved" : "pending")).toLowerCase(),
    answer: answer ?? "",
    hints: hints ?? [],
    steps: steps ?? [],
    imageUrl: imageUrl ?? null,
    isHelpful: feedbackHelpful,
    createdAt,
    isBookmarked: is_Bookmarked,
  };

  const getImageSrc = (path) => {
    if (!path) return null;
    if (/^https?:\/\//i.test(path)) return path;

    const normalized = String(path).replace(/\\/g, "/").replace(/^\/+/, "");
    const encoded = normalized
      .split("/")
      .map((segment) => encodeURIComponent(segment))
      .join("/");
    return apiUrl(encoded);
  };

  const formatDate = (value) => {
    if (!value) return "Recently asked";
    const date = new Date(value);
    return Number.isNaN(date.getTime())
      ? "Recently asked"
      : date.toLocaleString();
  };

  const statusLabel = doubt?.status === "solved" ? "Solved" : "Pending";
  const statusClasses =
    doubt?.status === "solved"
      ? "bg-emerald-50 text-emerald-800 ring-1 ring-emerald-100"
      : "bg-amber-50 text-amber-900 ring-1 ring-amber-100";

  if (!hasDoubtPayload) {
    return (
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.85),_rgba(219,234,254,0.55)_40%,_rgba(199,210,254,0.35)_75%,_rgba(244,231,255,0.65))] px-4 py-8">
        <div className="mx-auto max-w-xl">
          <EmptyState
            title="Doubt not found"
            description="Open a doubt from History or Bookmarks to view its details."
            action={
              <Link
                to="/history"
                className="inline-flex rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-700"
              >
                Go to history
              </Link>
            }
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.85),_rgba(219,234,254,0.55)_40%,_rgba(199,210,254,0.35)_75%,_rgba(244,231,255,0.65))] px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => navigate("/history")}
            className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/80 px-4 py-2 text-sm font-semibold text-slate-800 shadow-lg backdrop-blur transition hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600"
          >
            Back to history
          </button>

          <button
            type="button"
            onClick={() => navigate("/ask-doubt")}
            className="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-700"
          >
            Ask another doubt
          </button>
        </div>

        {error ? (
          <div className="mb-6">
            <ErrorState
              message={error}
              onRetry={() => setError("")}
              retryLabel="Dismiss and continue"
            />
          </div>
        ) : null}

        {successMessage ? (
          <p
            className="mb-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800"
            role="status"
          >
            {successMessage}
          </p>
        ) : null}

        <div className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/85 shadow-[0_24px_80px_rgba(15,23,42,0.10)] backdrop-blur">
          <div className="relative border-b border-slate-200/70 px-6 py-6 sm:px-8 sm:py-8">
            <div className="absolute inset-0 bg-gradient-to-r from-sky-500/10 via-transparent to-violet-500/10" />
            <div className="relative flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-3xl">
                <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-sky-800">
                  Doubt Details
                </p>
                <h1 className="text-3xl font-black tracking-tight text-slate-950 sm:text-4xl lg:text-5xl">
                  {doubt.question}
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-700 sm:text-base">
                  Review the original question, the generated answer, and the
                  step-by-step solution in one focused view.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                <button
                  type="button"
                  disabled={bookmarkLoading}
                  onClick={toggleBookmark}
                  aria-pressed={is_Bookmarked}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-600 disabled:opacity-60 sm:px-5 ${
                    is_Bookmarked
                      ? "bg-yellow-400 text-slate-900 hover:bg-yellow-500"
                      : "bg-slate-200 text-slate-800 hover:bg-slate-300"
                  }`}
                >
                  {bookmarkLoading
                    ? "Updating..."
                    : is_Bookmarked
                      ? "Bookmarked"
                      : "Bookmark this doubt"}
                </button>

                <div
                  className={`inline-flex items-center rounded-full px-3 py-2 text-sm font-semibold sm:px-4 ${statusClasses}`}
                >
                  {statusLabel}
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-0 lg:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-6 px-6 py-6 sm:px-8">
              <section className="rounded-3xl bg-slate-50 p-5 ring-1 ring-slate-200/70" aria-labelledby="answer-heading">
                <h2 id="answer-heading" className="mb-4 text-lg font-bold text-slate-950">
                  Answer
                </h2>
                {doubt.answer ? (
                  <MarkdownAnswer content={doubt.answer} />
                ) : (
                  <p className="text-slate-600">The answer is not available yet.</p>
                )}
              </section>

              <section className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200/70" aria-labelledby="hints-heading">
                <h2 id="hints-heading" className="text-lg font-bold text-slate-950">
                  Hints
                </h2>
                {doubt.hints?.length ? (
                  <ul className="mt-4 space-y-3">
                    {doubt.hints.map((hint, index) => (
                      <li
                        key={`${hint}-${index}`}
                        className="rounded-2xl bg-amber-50 px-4 py-3 text-slate-800 ring-1 ring-amber-100"
                      >
                        <span className="font-bold text-amber-900">{index + 1}. </span>
                        <MarkdownAnswer content={hint} showCopy={false} />
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-sm text-slate-600">
                    No hints were generated for this doubt.
                  </p>
                )}
              </section>

              <section className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200/70" aria-labelledby="steps-heading">
                <h2 id="steps-heading" className="text-lg font-bold text-slate-950">
                  Steps
                </h2>
                {doubt.steps?.length ? (
                  <div className="mt-4 space-y-4">
                    {doubt.steps.map((step, index) => (
                      <div
                        key={`${step}-${index}`}
                        className="flex gap-4 rounded-2xl bg-slate-50 px-4 py-4 ring-1 ring-slate-200/70"
                      >
                        <div
                          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-900 text-sm font-bold text-white"
                          aria-hidden="true"
                        >
                          {index + 1}
                        </div>
                        <MarkdownAnswer content={step} showCopy={false} className="min-w-0 flex-1" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-600">
                    No step-by-step solution was generated.
                  </p>
                )}
              </section>

              <section className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200/70" aria-labelledby="feedback-heading">
                <h2 id="feedback-heading" className="text-lg font-bold text-slate-950">
                  Feedback
                </h2>
                <div className="mt-4 flex flex-wrap gap-3">
                  {doubt.isHelpful === null ? (
                    <>
                      <p className="w-full text-sm text-slate-600">
                        Mark feedback for this doubt
                      </p>
                      <button
                        type="button"
                        disabled={submittingFeedback}
                        onClick={() => handleFeedbackSubmit(true)}
                        className="rounded-full bg-emerald-100 px-4 py-2 text-sm font-semibold text-emerald-900 transition hover:bg-emerald-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 disabled:opacity-60"
                      >
                        {submittingFeedback ? "Submitting..." : "Mark as helpful"}
                      </button>
                      <button
                        type="button"
                        disabled={submittingFeedback}
                        onClick={() => handleFeedbackSubmit(false)}
                        className="rounded-full bg-rose-100 px-4 py-2 text-sm font-semibold text-rose-900 transition hover:bg-rose-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-700 disabled:opacity-60"
                      >
                        {submittingFeedback ? "Submitting..." : "Mark as not helpful"}
                      </button>
                    </>
                  ) : (
                    <span
                      className={`rounded-full px-4 py-2 text-sm font-semibold ${
                        doubt.isHelpful
                          ? "bg-emerald-100 text-emerald-900"
                          : "bg-rose-100 text-rose-900"
                      }`}
                    >
                      {doubt.isHelpful
                        ? "Marked helpful"
                        : "Marked not helpful"}
                    </span>
                  )}
                </div>
              </section>
            </div>

            <aside className="border-t border-slate-200/70 bg-gradient-to-b from-slate-50 to-white px-6 py-6 lg:border-l lg:border-t-0 sm:px-8">
              <div className="overflow-hidden rounded-[1.75rem] bg-slate-950 shadow-2xl shadow-slate-950/20">
                {doubt.imageUrl ? (
                  <img
                    src={getImageSrc(doubt.imageUrl)}
                    alt={`Uploaded image for doubt: ${doubt.question}`}
                    className="h-auto w-full object-contain bg-slate-950"
                  />
                ) : (
                  <div className="flex h-80 items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.18),_rgba(15,23,42,0.95))] px-8 text-center text-slate-100">
                    <div>
                      <p className="text-lg font-semibold">No image attached</p>
                      <p className="mt-2 text-sm text-slate-300">
                        This doubt was submitted without an uploaded image.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 space-y-3 rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200/70">
                <div className="rounded-3xl bg-sky-50 p-4 ring-1 ring-sky-100">
                  <p className="text-xs uppercase tracking-[0.18em] text-sky-800">
                    Subject
                  </p>
                  <p className="mt-1 text-base font-semibold text-slate-900">
                    {doubt.subject}
                  </p>
                </div>
                <div className="rounded-3xl bg-violet-50 p-4 ring-1 ring-violet-100">
                  <p className="text-xs uppercase tracking-[0.18em] text-violet-800">
                    Class
                  </p>
                  <p className="mt-1 text-base font-semibold text-slate-900">
                    {doubt.className}
                  </p>
                </div>
                <div className="rounded-3xl bg-amber-50 p-4 ring-1 ring-amber-100">
                  <p className="text-xs uppercase tracking-[0.18em] text-amber-800">
                    Asked At
                  </p>
                  <p className="mt-1 text-base font-semibold text-slate-900">
                    {formatDate(doubt.createdAt)}
                  </p>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DoubtDetails;
