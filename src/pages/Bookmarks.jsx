import { useCallback, useEffect, useId, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { get_bookmarked_doubts, submitBookmark } from "../api/doubtApi";
import { getUserFacingError } from "../api/getUserFacingError";
import { useAuth } from "../context/AuthContext";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import LoadingState from "../components/ui/LoadingState";

function Bookmarks() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const searchId = useId();

  const [bookmarks, setBookmarks] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [removingId, setRemovingId] = useState(null);

  const openDoubtDetails = (doubt) => {
    navigate("/doubt", {
      state: {
        id: doubt.id,
        question: doubt.question,
        subject: doubt.subject,
        class_name: doubt.className,
        status: doubt.status,
        createdAt: doubt.bookmarkedAt,
        isBookmarked: true,
        isHelpful: doubt.isHelpful,
        answer: doubt.answer || null,
        imageUrl: doubt.imageUrl || null,
        hints: doubt.hints || null,
        steps: doubt.steps || null,
      },
    });
  };

  const fetchBookmarks = useCallback(async () => {
    if (!user) {
      setBookmarks([]);
      setLoading(false);
      setError("Please log in to view your bookmarks.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const response = await get_bookmarked_doubts();
      const doubts = Array.isArray(response?.items)
        ? response.items
        : Array.isArray(response)
          ? response
          : [];

      const normalized = doubts.map((doubt) => {
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
          status: String(
            doubt?.status ?? (doubt?.answer ? "solved" : "unsolved"),
          ).toLowerCase(),
          bookmarkedAt: createdAtValue
            ? new Date(createdAtValue).toLocaleString()
            : "Recently",
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

      setBookmarks(normalized);
    } catch (err) {
      setError(
        getUserFacingError(err, "Unable to load your bookmarks right now."),
      );
      setBookmarks([]);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchBookmarks();
  }, [fetchBookmarks]);

  const removeBookmark = async (id) => {
    try {
      setRemovingId(id);
      await submitBookmark({ doubt_id: id, is_bookmarked: false });
      setBookmarks((prev) => prev.filter((item) => item.id !== id));
      toast.success("Bookmark removed successfully!");
    } catch (err) {
      const message = getUserFacingError(
        err,
        "Unable to remove that bookmark right now.",
      );
      setError(message);
      toast.error(message);
    } finally {
      setRemovingId(null);
    }
  };

  const filteredBookmarks = bookmarks.filter(
    (item) =>
      item.question.toLowerCase().includes(search.toLowerCase()) ||
      item.subject.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="min-h-[calc(100vh-5rem)] px-3 py-6 sm:px-6 sm:py-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 rounded-3xl bg-white p-4 shadow-xl sm:mb-8 sm:p-6">
          <h1 className="text-center text-3xl font-bold text-slate-900 sm:text-4xl">
            Bookmarked Doubts
          </h1>
          <p className="mt-2 text-center text-sm text-slate-600 sm:text-base">
            Your saved doubts for quick revision
          </p>
        </div>

        <div className="mb-6 rounded-3xl bg-white p-4 shadow-lg sm:mb-8 sm:p-5">
          <h2 className="text-lg font-semibold text-slate-800">Total Bookmarks</h2>
          <p className="mt-2 text-3xl font-bold text-amber-700 sm:text-4xl">
            {bookmarks.length}
          </p>
        </div>

        <div className="mb-6 sm:mb-8">
          <label htmlFor={searchId} className="mb-2 block text-sm font-semibold text-slate-700">
            Search bookmarks
          </label>
          <input
            id={searchId}
            type="search"
            placeholder="Search bookmarked doubts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-2xl border border-slate-200 p-3 outline-none focus-visible:ring-2 focus-visible:ring-amber-500 sm:p-4"
          />
        </div>

        {loading ? (
          <LoadingState message="Loading your bookmarks..." />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchBookmarks} />
        ) : filteredBookmarks.length === 0 ? (
          <EmptyState
            title="No Bookmarks Found"
            description={
              bookmarks.length === 0
                ? "Save doubts to view them here."
                : "No bookmarks match your search."
            }
          />
        ) : (
          <div className="space-y-5">
            {filteredBookmarks.map((doubt) => (
              <article
                key={doubt.id}
                className="rounded-3xl bg-white p-4 shadow-lg transition hover:shadow-2xl sm:p-6"
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <button
                    type="button"
                    className="min-w-0 flex-1 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600"
                    onClick={() => openDoubtDetails(doubt)}
                    aria-label={`Open bookmarked doubt: ${doubt.question}`}
                  >
                    <h2 className="break-words text-lg font-bold text-slate-900 sm:text-xl">
                      {doubt.question}
                    </h2>
                    <div className="mt-3 flex flex-wrap gap-2 sm:gap-3">
                      <span className="rounded-full bg-sky-100 px-3 py-1 text-sm text-sky-800">
                        {doubt.subject}
                      </span>
                      <span className="rounded-full bg-green-100 px-3 py-1 text-sm text-green-800">
                        {doubt.className}
                      </span>
                      <span
                        className={`rounded-full px-3 py-1 text-sm ${
                          doubt.status === "solved"
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {doubt.status}
                      </span>
                    </div>
                    <p className="mt-3 text-sm text-slate-500">
                      Bookmarked {doubt.bookmarkedAt}
                    </p>
                  </button>

                  <button
                    type="button"
                    disabled={removingId === doubt.id}
                    onClick={() => removeBookmark(doubt.id)}
                    className="w-full rounded-xl bg-red-100 px-4 py-2 font-semibold text-red-800 hover:bg-red-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700 disabled:cursor-not-allowed disabled:opacity-60 sm:ml-4 sm:w-auto"
                  >
                    {removingId === doubt.id ? "Removing..." : "Remove bookmark"}
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

export default Bookmarks;
