export default function StatCard({
  title,
  value,
  description,
  icon: Icon,
  color,
}) {
  return (
    <div
      className="flex h-full min-h-[176px] flex-col rounded-2xl
      border border-slate-800 bg-[#111C2D] p-5
      transition hover:-translate-y-1 hover:border-slate-700"
    >
      {/* Card heading and icon */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm text-slate-400">
            {title}
          </p>

          <h3 className="mt-3 text-3xl font-bold text-white">
            {value}
          </h3>
        </div>

        <div className={`shrink-0 rounded-xl p-3 ${color}`}>
          <Icon size={22} />
        </div>
      </div>

      {/* Description */}
      <p className="mt-auto min-h-8 pt-4 text-xs leading-5 text-slate-500">
        {description}
      </p>
    </div>
  );
}
