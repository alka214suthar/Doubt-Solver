import { useCallback, useEffect, useId, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { get_user_doubts, submitBookmark } from "../api/doubtApi";
import { getUserFacingError } from "../api/getUserFacingError";
import { useAuth } from "../context/AuthContext";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import LoadingState from "../components/ui/LoadingState";

function History() {
  const { user } = useAuth();
  const searchId = useId();
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [doubtsData, setDoubtsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const openDoubtDetails = (doubt) => {
    navigate("/doubt", {
      state: {
        id: doubt.id,
        question: doubt.question,
        subject: doubt.subject,
        class_name: doubt.className,
        status: doubt.status,
        createdAt: doubt.createdAt,
        isBookmarked: doubt.isBookmarked,
        isHelpful: doubt.isHelpful,
        answer: doubt.answer || null,
        imageUrl: doubt.imageUrl || null,
        hints: doubt.hints || null,
        steps: doubt.steps || null,
      },
    });
  };

  const toggleBookmark = async (event, doubt) => {
    event.stopPropagation();
    if (!doubt?.id) return;

    const nextBookmarked = !doubt.isBookmarked;
    try {
      await submitBookmark({
        doubt_id: doubt.id,
        is_bookmarked: nextBookmarked,
      });
      setDoubtsData((prev) =>
        prev.map((item) => {
          const itemId = item?.doubt_id ?? item?.id;
          if (itemId !== doubt.id) return item;
          return { ...item, is_bookmarked: nextBookmarked };
        }),
      );
      toast.success(
        nextBookmarked
          ? "Doubt bookmarked successfully!"
          : "Bookmark removed successfully!",
      );
    } catch (err) {
      toast.error(
        getUserFacingError(err, "Unable to update bookmark right now."),
      );
    }
  };

  const loadDoubts = useCallback(async () => {
    if (!user) {
      setDoubtsData([]);
      setLoading(false);
      setError("Please log in to view your history.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const response = await get_user_doubts();
      const doubts = Array.isArray(response?.items)
        ? response.items
        : Array.isArray(response)
          ? response
          : [];
      setDoubtsData(doubts);
    } catch (err) {
      setError(getUserFacingError(err, "Unable to load your history right now."));
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadDoubts();
  }, [loadDoubts]);

  const normalizeStatus = (status, solution) => {
    if (status) return String(status).toLowerCase();
    return solution ? "solved" : "unsolved";
  };

  const normalizedDoubts = doubtsData.map((doubt) => {
    const questionText =
      doubt?.question?.question_text ?? doubt?.question ?? "Untitled doubt";
    const subjectText =
      doubt?.subject ?? doubt?.question?.subject ?? "Unknown subject";
    const classText = doubt?.class_name ?? doubt?.class ?? "Unknown class";
    const createdAtValue = doubt?.created_at ?? doubt?.createdAt;

    return {
      id: doubt?.doubt_id ?? doubt?.id,
      question: questionText,
      subject: subjectText,
      className: classText,
      status: normalizeStatus(doubt?.status, doubt?.solution),
      createdAt: createdAtValue
        ? new Date(createdAtValue).toLocaleString()
        : "Recently asked",
      isBookmarked: doubt?.is_bookmarked ?? false,
      isHelpful:
        doubt?.is_doubt_helpful === true
          ? true
          : doubt?.is_doubt_helpful === false
            ? false
            : null,
      answer: doubt?.solution ?? doubt?.answer ?? null,
      imageUrl: doubt?.img_url ?? doubt?.image_url ?? doubt?.imageUrl ?? null,
      hints: doubt?.hints ?? null,
      steps: doubt?.steps ?? null,
    };
  });

  const filteredDoubts = normalizedDoubts.filter((doubt) => {
    const matchesSearch =
      doubt.question.toLowerCase().includes(search.toLowerCase()) ||
      doubt.subject.toLowerCase().includes(search.toLowerCase());

    if (filter === "solved") {
      return matchesSearch && doubt.status === "solved";
    }
    if (filter === "unsolved") {
      return matchesSearch && doubt.status !== "solved";
    }
    return matchesSearch;
  });

  const totalDoubts = normalizedDoubts.length;
  const solvedDoubts = normalizedDoubts.filter(
    (doubt) => doubt.status === "solved",
  ).length;
  const pendingDoubts = totalDoubts - solvedDoubts;

  return (
    <div className="min-h-[calc(100vh-5rem)] px-3 py-6 sm:px-6 sm:py-8">
      <div className="mx-auto max-w-6xl">
        <h1 className="mb-6 text-center text-3xl font-bold text-slate-900 sm:mb-8 sm:text-4xl">
          Doubt History
        </h1>

        <div className="mb-6 grid grid-cols-1 gap-3 sm:mb-8 sm:grid-cols-3 sm:gap-4">
          <div className="rounded-3xl bg-white p-4 shadow-lg sm:p-5">
            <h2 className="text-slate-600">Total Doubts</h2>
            <p className="text-3xl font-bold text-slate-900">{totalDoubts}</p>
          </div>
          <div className="rounded-3xl bg-white p-4 shadow-lg sm:p-5">
            <h2 className="text-slate-600">Solved</h2>
            <p className="text-3xl font-bold text-green-700">{solvedDoubts}</p>
          </div>
          <div className="rounded-3xl bg-white p-4 shadow-lg sm:p-5">
            <h2 className="text-slate-600">Pending</h2>
            <p className="text-3xl font-bold text-amber-700">{pendingDoubts}</p>
          </div>
        </div>

        <div className="mb-6">
          <label htmlFor={searchId} className="mb-2 block text-sm font-semibold text-slate-700">
            Search doubts
          </label>
          <input
            id={searchId}
            type="search"
            placeholder="Search doubts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-2xl border border-slate-200 p-4 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-500"
          />
        </div>

        <div className="mb-8 flex flex-wrap gap-3" role="group" aria-label="Filter doubts by status">
          {[
            { id: "all", label: "All" },
            { id: "solved", label: "Solved" },
            { id: "unsolved", label: "Unsolved" },
          ].map((item) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={filter === item.id}
              onClick={() => setFilter(item.id)}
              className={`rounded-xl px-5 py-2 font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600 ${
                filter === item.id
                  ? item.id === "solved"
                    ? "bg-green-600 text-white"
                    : item.id === "unsolved"
                      ? "bg-red-600 text-white"
                      : "bg-blue-600 text-white"
                  : "bg-white text-slate-800"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {loading ? (
          <LoadingState message="Loading your doubts..." />
        ) : error ? (
          <ErrorState message={error} onRetry={loadDoubts} />
        ) : filteredDoubts.length === 0 ? (
          <EmptyState
            title="No doubts found"
            description={
              normalizedDoubts.length === 0
                ? "Ask your first doubt to build history."
                : "No doubts match your current filters."
            }
          />
        ) : (
          <div className="space-y-5">
            {filteredDoubts.map((doubt) => (
              <article
                key={doubt.id}
                className="rounded-3xl bg-white p-4 shadow-lg transition hover:shadow-2xl sm:p-6"
              >
                <button
                  type="button"
                  onClick={() => openDoubtDetails(doubt)}
                  className="w-full text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600"
                  aria-label={`Open doubt: ${doubt.question}`}
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <h2 className="min-w-0 break-words text-lg font-bold text-slate-900 sm:text-xl">
                      {doubt.question}
                    </h2>
                    <span
                      className={`rounded-full px-3 py-1 text-sm font-semibold sm:px-4 ${
                        doubt.status === "solved"
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {doubt.status}
                    </span>
                  </div>
                  <p className="mt-3 text-slate-600">
                    {doubt.subject} • {doubt.className}
                  </p>
                  <p className="mt-2 text-sm text-slate-500">Asked {doubt.createdAt}</p>
                </button>
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={(event) => toggleBookmark(event, doubt)}
                    aria-pressed={doubt.isBookmarked}
                    className={`rounded-full px-3 py-1 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-600 sm:px-4 ${
                      doubt.isBookmarked
                        ? "bg-yellow-400 text-slate-900"
                        : "bg-slate-100 text-slate-800"
                    }`}
                  >
                    {doubt.isBookmarked ? "Bookmarked" : "Bookmark"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default History;
