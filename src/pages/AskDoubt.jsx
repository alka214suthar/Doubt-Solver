import { useEffect, useId, useState } from "react";
import { solveDoubt, submitFeedback, submitBookmark } from "../api/doubtApi";
import { getUserFacingError } from "../api/getUserFacingError";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";
import MarkdownAnswer from "../components/MarkdownAnswer";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import LoadingState from "../components/ui/LoadingState";

function AskDoubt() {
  const { user, setUser, refreshUser } = useAuth();
  const formId = useId();
  const doubtFieldId = `${formId}-doubt`;
  const subjectFieldId = `${formId}-subject`;
  const classFieldId = `${formId}-class`;
  const imageFieldId = `${formId}-image`;

  const [doubt, setDoubt] = useState("");
  const [image, setImage] = useState(null);
  const [subject, setSubject] = useState("");
  const [studentClass, setStudentClass] = useState("");
  const [answer, setAnswer] = useState("");
  const [hints, setHints] = useState([]);
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [doubtId, setDoubtId] = useState(null);
  const [actionLoading, setActionLoading] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [freeDoubtsLeft, setFreeDoubtsLeft] = useState(
    Number(user?.available_free_doubts) || 0,
  );

  const canAskDoubt = Boolean(user) && freeDoubtsLeft > 0;

  useEffect(() => {
    if (!user) {
      setFreeDoubtsLeft(0);
      return;
    }

    let isMounted = true;

    const loadFreeDoubts = async () => {
      try {
        const details = await refreshUser();
        if (!isMounted) return;
        setFreeDoubtsLeft(Number(details.available_free_doubts) || 0);
      } catch {
        if (!isMounted) return;
        setFreeDoubtsLeft(Number(user?.available_free_doubts) || 0);
      }
    };

    loadFreeDoubts();

    return () => {
      isMounted = false;
    };
  }, [user?.user_id, refreshUser]);

  const validate = () => {
    const next = {};
    if (!doubt.trim()) next.doubt = "Please describe your doubt";
    if (!subject) next.subject = "Select a subject";
    if (!studentClass) next.studentClass = "Select a class";
    setFieldErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError("");
      setSuccessMessage("");

      if (!user) {
        setError("Please log in before asking a doubt.");
        return;
      }

      if (freeDoubtsLeft <= 0) {
        const message = "No free doubts left. You cannot ask a new doubt.";
        setError(message);
        toast.error(message);
        return;
      }

      if (!validate()) {
        setError("Please fill in all required fields.");
        return;
      }

      const formData = new FormData();
      formData.append("question", doubt);
      formData.append("subject", subject);
      formData.append("class_name", studentClass);
      if (image) formData.append("image", image);

      const data = await solveDoubt(formData);

      setAnswer(data.answer);
      setHints(data.hints || []);
      setSteps(data.steps || []);
      setDoubtId(data.doubt_id);
      setSuccessMessage("Doubt solved successfully.");
      toast.success("Doubt solved successfully!");

      try {
        const details = await refreshUser();
        setFreeDoubtsLeft(Number(details.available_free_doubts) || 0);
      } catch {
        const remaining = Math.max(0, freeDoubtsLeft - 1);
        setFreeDoubtsLeft(remaining);
        setUser((prev) =>
          prev ? { ...prev, available_free_doubts: remaining } : prev,
        );
      }
    } catch (err) {
      const message = getUserFacingError(
        err,
        "Something went wrong. Please try again.",
      );
      setError(message);
      setAnswer("");
      setHints([]);
      setSteps([]);
      if (String(message).toLowerCase().includes("free doubt")) {
        setFreeDoubtsLeft(0);
        setUser((prev) =>
          prev ? { ...prev, available_free_doubts: 0 } : prev,
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFeedbackSubmit = async (event) => {
    const feedbackType = event.currentTarget.value;
    if (!doubtId || !answer) {
      setError("Solve a doubt before sending feedback.");
      return;
    }

    try {
      setActionLoading(feedbackType);
      setError("");
      await submitFeedback({
        is_doubt_helpful: feedbackType === "Helpful",
        doubt_id: doubtId,
      });
      setSuccessMessage("Thank you for your feedback!");
      toast.success("Thank you for your feedback!");
    } catch (err) {
      setError(
        getUserFacingError(err, "Unable to submit feedback right now."),
      );
    } finally {
      setActionLoading("");
    }
  };

  const handleBookmark = async () => {
    if (!doubtId) {
      setError("Solve a doubt before bookmarking it.");
      return;
    }

    try {
      setActionLoading("bookmark");
      setError("");
      await submitBookmark({
        doubt_id: doubtId,
        is_bookmarked: true,
      });
      setSuccessMessage("Doubt bookmarked successfully.");
      toast.success("Doubt bookmarked successfully!");
    } catch (err) {
      setError(
        getUserFacingError(err, "Unable to submit bookmark right now."),
      );
    } finally {
      setActionLoading("");
    }
  };

  return (
    <div className="min-h-[calc(100vh-5rem)] px-3 py-6 sm:px-6 sm:py-8">
      <div className="mx-auto mb-8 max-w-4xl sm:mb-10">
        <form
          onSubmit={handleSubmit}
          className="rounded-3xl bg-white p-4 shadow-2xl sm:p-8"
          noValidate
        >
          {!user && (
            <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-800" role="status">
              Please log in before asking a doubt.
            </div>
          )}

          {user && freeDoubtsLeft <= 0 && (
            <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-800" role="status">
              No free doubts left. You cannot ask a new doubt right now.
            </div>
          )}

          <div className="mb-6">
            <label htmlFor={doubtFieldId} className="mb-2 block font-semibold text-slate-700">
              Your doubt
            </label>
            <textarea
              id={doubtFieldId}
              rows="6"
              placeholder="Type your doubt here..."
              value={doubt}
              onChange={(e) => {
                setDoubt(e.target.value);
                setFieldErrors((prev) => ({ ...prev, doubt: "" }));
              }}
              aria-invalid={Boolean(fieldErrors.doubt)}
              aria-describedby={fieldErrors.doubt ? `${doubtFieldId}-error` : undefined}
              className="w-full resize-none rounded-2xl border border-slate-200 p-3 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 sm:p-4 sm:text-base"
            />
            {fieldErrors.doubt ? (
              <p id={`${doubtFieldId}-error`} role="alert" className="mt-1 text-sm text-red-600">
                {fieldErrors.doubt}
              </p>
            ) : null}
          </div>

          <div className="mb-6">
            <label htmlFor={imageFieldId} className="mb-2 block font-semibold text-slate-700">
              Upload image (optional)
            </label>
            <div className="rounded-2xl border-2 border-dashed border-amber-300 bg-amber-50 p-5 text-center transition hover:bg-amber-100 sm:p-8">
              <input
                id={imageFieldId}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="sr-only"
                onChange={(e) => setImage(e.target.files?.[0] || null)}
              />
              <label
                htmlFor={imageFieldId}
                className="cursor-pointer font-medium text-amber-800 focus-within:outline"
              >
                Click to select image
              </label>
              <p className="mt-1 text-sm text-slate-600">JPG, PNG, WEBP supported</p>
            </div>
          </div>

          {image && (
            <p className="mb-6 break-all font-medium text-green-700" role="status">
              Selected: {image.name}
            </p>
          )}

          <div className="mb-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4">
              <label htmlFor={subjectFieldId} className="mb-2 block font-semibold text-sky-800">
                Subject
              </label>
              <select
                id={subjectFieldId}
                value={subject}
                onChange={(e) => {
                  setSubject(e.target.value);
                  setFieldErrors((prev) => ({ ...prev, subject: "" }));
                }}
                aria-invalid={Boolean(fieldErrors.subject)}
                aria-describedby={fieldErrors.subject ? `${subjectFieldId}-error` : undefined}
                className="w-full rounded-xl border border-sky-200 p-3 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-500"
              >
                <option value="">Select Subject</option>
                <option value="Mathematics">Mathematics</option>
                <option value="Physics">Physics</option>
                <option value="Chemistry">Chemistry</option>
                <option value="Biology">Biology</option>
                <option value="History">History</option>
                <option value="Geography">Geography</option>
                <option value="English">English</option>
                <option value="Computer Science">Computer Science</option>
                <option value="Logical Reasoning">Logical Reasoning</option>
              </select>
              {fieldErrors.subject ? (
                <p id={`${subjectFieldId}-error`} role="alert" className="mt-1 text-sm text-red-600">
                  {fieldErrors.subject}
                </p>
              ) : null}
            </div>

            <div className="rounded-2xl border border-green-200 bg-green-50 p-4">
              <label htmlFor={classFieldId} className="mb-2 block font-semibold text-green-800">
                Class
              </label>
              <select
                id={classFieldId}
                value={studentClass}
                onChange={(e) => {
                  setStudentClass(e.target.value);
                  setFieldErrors((prev) => ({ ...prev, studentClass: "" }));
                }}
                aria-invalid={Boolean(fieldErrors.studentClass)}
                aria-describedby={
                  fieldErrors.studentClass ? `${classFieldId}-error` : undefined
                }
                className="w-full rounded-xl border border-green-200 p-3 focus-visible:outline focus-visible:outline-2 focus-visible:outline-green-600"
              >
                <option value="">Select Class</option>
                <option value="6">Class 6</option>
                <option value="7">Class 7</option>
                <option value="8">Class 8</option>
                <option value="9">Class 9</option>
                <option value="10">Class 10</option>
                <option value="11">Class 11</option>
                <option value="12">Class 12</option>
              </select>
              {fieldErrors.studentClass ? (
                <p id={`${classFieldId}-error`} role="alert" className="mt-1 text-sm text-red-600">
                  {fieldErrors.studentClass}
                </p>
              ) : null}
            </div>
          </div>

          <button
            type="submit"
            disabled={!canAskDoubt || loading}
            aria-busy={loading}
            className={`w-full rounded-2xl py-4 text-lg font-bold text-white transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-700 ${
              !canAskDoubt || loading
                ? "cursor-not-allowed bg-slate-400"
                : "bg-gradient-to-r from-sky-500 to-green-500 hover:scale-105"
            }`}
          >
            {loading
              ? "Solving..."
              : freeDoubtsLeft <= 0
                ? "No Free Doubts Left"
                : "Solve Doubt"}
          </button>
        </form>

        <div className="mt-6 rounded-3xl bg-white p-4 shadow-2xl sm:mt-8 sm:p-6" aria-live="polite">
          <h2 className="mb-4 text-xl font-bold sm:text-2xl">Doubt Solution</h2>

          {successMessage ? (
            <p className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-800" role="status">
              {successMessage}
            </p>
          ) : null}

          {loading ? (
            <LoadingState message="Solving doubt..." />
          ) : error ? (
            <ErrorState
              message={error}
              onRetry={() => {
                setError("");
                if (doubt && subject && studentClass) {
                  document.getElementById(doubtFieldId)?.form?.requestSubmit();
                }
              }}
              retryLabel="Try again"
            />
          ) : answer ? (
            <div className="mt-4 space-y-5 sm:mt-8 sm:space-y-6">
              <div className="rounded-3xl bg-gradient-to-r from-sky-500 to-green-500 p-4 text-white shadow-xl sm:p-6">
                <h3 className="text-2xl font-bold sm:text-3xl">Doubt Solved</h3>
                <p className="mt-2 text-sm opacity-90 sm:text-base">
                  Here&apos;s a detailed explanation for your question.
                </p>
              </div>

              <div className="rounded-3xl border border-sky-100 bg-white p-4 shadow-xl sm:p-6">
                <h3 className="mb-4 text-xl font-bold text-sky-800 sm:text-2xl">Answer</h3>
                <MarkdownAnswer content={answer} />
              </div>

              <div className="rounded-3xl border border-amber-200 bg-amber-50 p-4 shadow-xl sm:p-6">
                <h3 className="mb-4 text-xl font-bold text-amber-800 sm:text-2xl">Hints</h3>
                {hints.length ? (
                  <div className="space-y-3">
                    {hints.map((hint, index) => (
                      <div
                        key={`${hint}-${index}`}
                        className="rounded-2xl bg-white p-3 shadow-sm sm:p-4"
                      >
                        <span className="font-bold text-amber-700">{index + 1}. </span>
                        <MarkdownAnswer content={hint} showCopy={false} className="inline" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    title="No hints"
                    description="No hints were generated for this doubt."
                    className="bg-transparent shadow-none"
                  />
                )}
              </div>

              <div className="rounded-3xl border border-green-200 bg-green-50 p-4 shadow-xl sm:p-6">
                <h3 className="mb-4 text-xl font-bold text-green-800 sm:text-2xl">
                  Step-by-Step Solution
                </h3>
                {steps.length ? (
                  <div className="space-y-4">
                    {steps.map((step, index) => (
                      <div
                        key={`${step}-${index}`}
                        className="flex gap-3 rounded-2xl bg-white p-4 shadow-sm sm:gap-4 sm:p-5"
                      >
                        <div
                          className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-r from-sky-500 to-green-500 text-sm font-bold text-white sm:h-10 sm:w-10"
                          aria-hidden="true"
                        >
                          {index + 1}
                        </div>
                        <MarkdownAnswer content={step} showCopy={false} className="min-w-0 flex-1" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    title="No steps"
                    description="No step-by-step solution was generated."
                    className="bg-transparent shadow-none"
                  />
                )}
              </div>
            </div>
          ) : (
            <EmptyState
              title="No solution yet"
              description="Your answer will appear here after you solve a doubt."
              className="shadow-none"
            />
          )}

          <div className="mt-6 flex flex-col gap-3 sm:mt-8 sm:flex-row sm:flex-wrap sm:gap-4">
            <button
              type="button"
              value="Helpful"
              disabled={!doubtId || !answer || Boolean(actionLoading)}
              onClick={handleFeedbackSubmit}
              className="rounded-xl bg-green-100 px-6 py-3 font-semibold text-green-900 hover:bg-green-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {actionLoading === "Helpful" ? "Submitting..." : "Mark as helpful"}
            </button>

            <button
              type="button"
              value="Not Helpful"
              disabled={!doubtId || !answer || Boolean(actionLoading)}
              onClick={handleFeedbackSubmit}
              className="rounded-xl bg-red-100 px-6 py-3 font-semibold text-red-900 hover:bg-red-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {actionLoading === "Not Helpful" ? "Submitting..." : "Mark as not helpful"}
            </button>

            <button
              type="button"
              disabled={!doubtId || Boolean(actionLoading)}
              onClick={handleBookmark}
              className="rounded-xl bg-yellow-100 px-6 py-3 font-semibold text-yellow-900 hover:bg-yellow-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-yellow-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {actionLoading === "bookmark" ? "Bookmarking..." : "Bookmark doubt"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AskDoubt;
