function ErrorState({
  title = "Something went wrong",
  message = "Please try again.",
  onRetry = null,
  retryLabel = "Retry",
  className = "",
}) {
  return (
    <div
      role="alert"
      className={`relative overflow-hidden rounded-3xl border border-red-200 bg-white shadow-xl ${className}`}
    >
      <div className="absolute top-0 left-0 h-full w-2 bg-red-500" aria-hidden="true" />
      <div className="p-4 sm:p-6">
        <h3 className="text-lg font-bold text-red-700 sm:text-xl">{title}</h3>
        <p className="mt-2 break-words text-slate-700">{message}</p>
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 rounded-xl bg-red-500 px-4 py-2 font-semibold text-white transition hover:bg-red-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600"
          >
            {retryLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}

export default ErrorState;
