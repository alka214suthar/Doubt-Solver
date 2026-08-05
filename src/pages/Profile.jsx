import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";
import { getUserDetails } from "../api/authApi";
import { getUserFacingError } from "../api/getUserFacingError";
import ErrorState from "../components/ui/ErrorState";

const formatAskedDate = (value) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

function Profile() {
  const { user: currentUser, logout } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadProfile = async () => {
    if (!currentUser) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await getUserDetails();
      const doubtsAsked = Math.max(0, Number(response.doubts_asked) || 0);
      const freeDoubtsLeft = Math.max(
        0,
        Number(response.available_free_doubts) || 0,
      );
      const totalDoubts = doubtsAsked + freeDoubtsLeft;
      const firstDoubtAskedAt = formatAskedDate(response.first_doubt_asked_at);

      setProfile({
        name: response.name,
        email: response.email,
        doubtsAsked,
        freeDoubtsLeft,
        totalDoubts,
        bookmarks: Math.max(0, Number(response.bookmarks) || 0),
        firstDoubtAskedAt,
        hasAskedDoubt: doubtsAsked > 0 || Boolean(firstDoubtAskedAt),
      });
    } catch (err) {
      setError(getUserFacingError(err, "Unable to load your profile right now."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
    // Identity is always re-fetched from /users/me for the authenticated session.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUser?.user_id]);

  const handleLogout = async () => {
    await logout();
    toast.success("Logged out successfully!");
    navigate("/", { replace: true });
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-100 via-blue-50 to-violet-100 px-4 py-10">
        <div className="mx-auto max-w-xl rounded-[2rem] border border-white/70 bg-white/90 p-10 text-center shadow-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-700">
            Profile
          </p>
          <h1 className="mt-3 text-3xl font-bold text-slate-900">
            Sign in to view your profile
          </h1>
          <p className="mt-3 text-slate-500">
            Your learning progress and free doubt balance live here.
          </p>
          <Link
            to="/"
            className="mt-8 inline-flex rounded-2xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-100 via-blue-50 to-violet-100 px-4 py-10">
        <div className="mx-auto max-w-xl rounded-[2rem] border border-white/70 bg-white/90 p-10 text-center shadow-xl">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-sky-500 border-t-transparent" />
          <h2 className="mt-5 text-xl font-semibold text-slate-800">
            Loading your profile...
          </h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-100 via-blue-50 to-violet-100 px-4 py-10">
        <div className="mx-auto max-w-xl">
          <ErrorState
            title="Couldn't load profile"
            message={error}
            onRetry={loadProfile}
          />
        </div>
      </div>
    );
  }

  const totalDoubts = Math.max(
    1,
    profile.totalDoubts ?? profile.doubtsAsked + profile.freeDoubtsLeft,
  );
  const usedPercent = Math.min(
    100,
    Math.round((profile.doubtsAsked / totalDoubts) * 100),
  );
  const remainingPercent = Math.max(0, 100 - usedPercent);
  const initials = (profile.name || "U")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");

  const milestones = [
    {
      title: "First Doubt",
      detail: profile.hasAskedDoubt
        ? profile.firstDoubtAskedAt
          ? `Asked on ${profile.firstDoubtAskedAt}`
          : "Unlocked"
        : "Ask your first doubt",
      done: Boolean(profile.hasAskedDoubt),
    },
    {
      title: "Curious Learner",
      detail:
        profile.doubtsAsked >= 3
          ? `Unlocked · ${profile.doubtsAsked} doubts asked`
          : `${profile.doubtsAsked} / 3 doubts asked`,
      done: profile.doubtsAsked >= 3,
    },
    {
      title: "Bookmark Keeper",
      detail:
        profile.bookmarks > 0
          ? `${profile.bookmarks} saved`
          : "Save a doubt to unlock",
      done: profile.bookmarks > 0,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-100 via-blue-50 to-violet-100 px-4 py-8 sm:px-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <section className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/90 shadow-[0_24px_60px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="relative border-b border-slate-200/70 px-6 py-8 sm:px-8">
            <div className="absolute inset-0 bg-gradient-to-r from-sky-500/10 via-transparent to-amber-400/10" />
            <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-center">
                <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-[1.75rem] bg-gradient-to-br from-sky-500 to-blue-600 text-3xl font-bold text-white shadow-lg shadow-sky-200">
                  {initials}
                </div>

                <div className="text-center sm:text-left">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-700">
                    Your Profile
                  </p>
                  <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950 sm:text-4xl">
                    {profile.name}
                  </h1>
                  <p className="mt-2 text-slate-500">{profile.email}</p>
                  <p className="mt-3 max-w-xl text-sm leading-6 text-slate-600">
                    Track your free doubt balance, saved questions, and learning
                    progress in one place.
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={handleLogout}
                className="w-full rounded-2xl bg-rose-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-rose-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-800 sm:w-auto"
              >
                Log out of your account
              </button>
            </div>
          </div>

          <div className="grid gap-4 px-6 py-6 sm:grid-cols-3 sm:px-8">
            {[
              {
                label: "Doubts Asked",
                value: profile.doubtsAsked,
                tone: "from-sky-50 to-white text-sky-700",
              },
              {
                label: "Free Left",
                value: profile.freeDoubtsLeft,
                tone: "from-emerald-50 to-white text-emerald-700",
              },
              {
                label: "Bookmarks",
                value: profile.bookmarks,
                tone: "from-amber-50 to-white text-amber-700",
              },
            ].map((stat) => (
              <div
                key={stat.label}
                className={`rounded-3xl bg-gradient-to-b p-5 ring-1 ring-slate-200/70 ${stat.tone}`}
              >
                <p className="text-sm font-medium text-slate-500">{stat.label}</p>
                <p className="mt-2 text-4xl font-bold">{stat.value}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-lg sm:p-8">
            <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:gap-4">
              <div className="min-w-0">
                <h2 className="text-xl font-bold text-slate-950 sm:text-2xl">
                  Doubt usage
                </h2>
                <p className="mt-2 text-sm text-slate-500">
                  You have asked {profile.doubtsAsked} doubts. Total available
                  pool is {totalDoubts} (asked + free left).
                </p>
              </div>
              <span className="shrink-0 rounded-full bg-sky-50 px-3 py-1 text-sm font-semibold text-sky-700 ring-1 ring-sky-100">
                {remainingPercent}% left
              </span>
            </div>

            <div className="mt-8">
              <div className="mb-2 flex justify-between text-sm font-medium text-slate-600">
                <span>Used</span>
                <span>
                  {profile.doubtsAsked} / {totalDoubts}
                </span>
              </div>
              <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-sky-500 to-blue-600 transition-all duration-500"
                  style={{ width: `${usedPercent}%` }}
                />
              </div>
            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              <Link
                to="/ask-doubt"
                className="rounded-2xl bg-slate-900 px-5 py-4 text-center text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                Ask a new doubt
              </Link>
              <Link
                to="/history"
                className="rounded-2xl bg-sky-100 px-5 py-4 text-center text-sm font-semibold text-sky-800 transition hover:bg-sky-200"
              >
                View history
              </Link>
            </div>
          </div>

          <div className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-lg sm:p-8">
            <h2 className="text-2xl font-bold text-slate-950">Milestones</h2>
            <p className="mt-2 text-sm text-slate-500">
              Small wins as you keep learning.
            </p>

            <div className="mt-6 space-y-3">
              {milestones.map((item) => (
                <div
                  key={item.title}
                  className={`rounded-2xl p-4 ring-1 ${
                    item.done
                      ? "bg-emerald-50 ring-emerald-100"
                      : "bg-slate-50 ring-slate-200/70"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold text-slate-900">{item.title}</p>
                    <span
                      className={`text-xs font-semibold uppercase tracking-wide ${
                        item.done ? "text-emerald-700" : "text-slate-400"
                      }`}
                    >
                      {item.done ? "Done" : "Locked"}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{item.detail}</p>
                </div>
              ))}
            </div>

            <Link
              to="/bookmarks"
              className="mt-6 inline-flex w-full items-center justify-center rounded-2xl bg-amber-100 px-5 py-4 text-sm font-semibold text-amber-800 transition hover:bg-amber-200"
            >
              Open bookmarks
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}

export default Profile;
