function EmptyState({
  title = "Nothing here yet",
  description = "",
  action = null,
  className = "",
}) {
  return (
    <div
      role="status"
      className={`rounded-3xl bg-white p-8 text-center shadow-lg ${className}`}
    >
      <h2 className="text-2xl font-bold text-slate-500">{title}</h2>
      {description ? (
        <p className="mt-2 text-slate-400">{description}</p>
      ) : null}
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}

export default EmptyState;
