function LoadingState({ message = "Loading...", className = "" }) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className={`rounded-2xl bg-white/90 p-6 text-center shadow ${className}`}
    >
      <div
        className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-sky-500 border-t-transparent"
        aria-hidden="true"
      />
      <p className="mt-4 font-medium text-slate-600">{message}</p>
    </div>
  );
}

export default LoadingState;
