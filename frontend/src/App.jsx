import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Award,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  CircleHelp,
  Clock3,
  Compass,
  Flame,
  GitBranch,
  GraduationCap,
  Moon,
  Play,
  RotateCcw,
  Send,
  Sparkles,
  Sun,
  Target,
  TrendingUp,
  Trophy,
  X,
  Zap,
} from "lucide-react";
import {
  CartesianGrid,
  ComposedChart,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Radar,
  RadarChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Bar,
  BarChart,
} from "recharts";
import { api } from "./api";

const DEMO_STEPS = [
  "Starting from Aarav's current learning profile",
  "Re-ranking the next best learning action",
  "Completing a recommended resource",
  "Simulating a 45% JavaScript quiz",
  "Adding a remedial JavaScript learning step",
  "Changing the goal to Data Analyst",
  "Recalculating the roadmap and readiness",
];

const delay = (duration) => new Promise((resolve) => window.setTimeout(resolve, duration));

function useCountUp(value, duration = 750) {
  const [shown, setShown] = useState(0);
  const reducedMotion = useMemo(
    () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false,
    [],
  );
  useEffect(() => {
    if (reducedMotion) {
      setShown(value);
      return undefined;
    }
    let frame;
    const start = performance.now();
    const from = shown;
    const animate = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - (1 - progress) ** 3;
      setShown(from + (value - from) * eased);
      if (progress < 1) frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [duration, reducedMotion, value]);
  return shown;
}

function Count({ value, suffix = "", decimals = 0 }) {
  const shown = useCountUp(Number(value) || 0);
  return <>{shown.toFixed(decimals)}{suffix}</>;
}

function formatDate(value) {
  if (!value) return "Not scheduled";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(
    new Date(`${value}T12:00:00`),
  );
}

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(date);
}

function classNames(...values) {
  return values.filter(Boolean).join(" ");
}

function Card({ children, className = "", id, ...props }) {
  return <section id={id} className={classNames("card min-w-0", className)} {...props}>{children}</section>;
}

function CardHeading({ eyebrow, title, action }) {
  return (
    <div className="mb-5 flex items-start justify-between gap-3">
      <div>
        {eyebrow && <p className="mb-1 text-[10px] font-bold uppercase tracking-[.15em] text-muted">{eyebrow}</p>}
        <h2 className="text-[15px] font-semibold tracking-[-.02em] text-ink">{title}</h2>
      </div>
      {action}
    </div>
  );
}

function InfoPopover({ title, children }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        type="button"
        aria-label={`How is ${title} calculated?`}
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        className="rounded-full p-1 text-muted transition hover:bg-canvas hover:text-ink"
      >
        <CircleHelp size={15} strokeWidth={1.8} />
      </button>
      {open && (
        <div className="absolute right-0 top-8 z-30 w-64 rounded-xl border border-line bg-surface p-3 text-xs leading-5 text-muted shadow-card">
          <div className="mb-1 flex items-center justify-between gap-2 font-semibold text-ink">
            {title}
            <button type="button" aria-label="Close calculation details" onClick={() => setOpen(false)}>
              <X size={14} />
            </button>
          </div>
          {children}
        </div>
      )}
    </div>
  );
}

function ProgressRing({ value, color = "var(--chart-primary)", size = 58, stroke = 5, children }) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const safeValue = Math.max(0, Math.min(Number(value) || 0, 100));
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} role="img" aria-label={`${Math.round(safeValue)} percent`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgb(var(--line))" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - safeValue / 100)}
          className="transition-[stroke-dashoffset] duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">{children}</div>
    </div>
  );
}

function MetricCard({ label, value, suffix, decimals = 0, icon: Icon, tone, ring, change, info, subline }) {
  const shown = useCountUp(Number(value) || 0);
  const [open, setOpen] = useState(false);
  const trendIcon = change > 0 ? ArrowUpRight : change < 0 ? ArrowDownRight : null;
  const TrendIcon = trendIcon;
  return (
    <Card className="relative p-4 sm:p-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[12px] font-medium text-muted">
          <span className={classNames("grid h-7 w-7 place-items-center rounded-lg", tone)}><Icon size={15} /></span>
          {label}
        </div>
        <div className="relative">
          <button
            type="button"
            className="rounded-full p-1 text-muted hover:bg-canvas"
            aria-label={`How is ${label} calculated?`}
            aria-expanded={open}
            onClick={() => setOpen((current) => !current)}
          >
            <CircleHelp size={15} />
          </button>
          {open && (
            <div className="absolute right-0 top-7 z-20 w-64 rounded-xl border border-line bg-surface p-3 text-xs leading-5 text-muted shadow-card">
              <div className="mb-1 flex items-center justify-between font-semibold text-ink">
                How is this calculated?
                <button type="button" aria-label="Close" onClick={() => setOpen(false)}><X size={14} /></button>
              </div>
              {info}
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-baseline gap-1">
            <span className="text-[29px] font-bold leading-none tracking-[-.055em] text-ink tabular-nums">
              {shown.toFixed(decimals)}
            </span>
            {suffix && <span className="text-sm font-semibold text-muted">{suffix}</span>}
          </div>
          <div className="mt-2 flex min-h-5 items-center gap-1.5 text-[11px] text-muted">
            {TrendIcon && <TrendIcon size={13} className={change > 0 ? "text-emerald-500" : "text-rose-500"} />}
            {change !== undefined && change !== null && (
              <span className={change > 0 ? "font-semibold text-emerald-600 dark:text-emerald-400" : change < 0 ? "font-semibold text-rose-600 dark:text-rose-400" : ""}>
                {change > 0 ? "+" : ""}{change} pts
              </span>
            )}
            <span>{subline}</span>
          </div>
        </div>
        {ring !== undefined && (
          <ProgressRing value={ring} color={tone.includes("emerald") ? "var(--chart-secondary)" : "var(--chart-primary)"} size={58}>
            <span className="text-[11px] font-bold text-ink">{Math.round(ring)}%</span>
          </ProgressRing>
        )}
      </div>
    </Card>
  );
}

function SkeletonDashboard() {
  return (
    <div role="status" aria-label="Loading dashboard" className="mx-auto max-w-[1600px] space-y-5 px-4 py-6 sm:px-7">
      <span className="sr-only">Loading your learning dashboard</span>
      <div className="skeleton h-12 w-48 rounded-xl" />
      <div className="skeleton h-44 rounded-card" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }, (_, index) => <div key={index} className="skeleton h-36 rounded-card" />)}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="skeleton h-[360px] rounded-card" />
        <div className="skeleton h-[360px] rounded-card" />
      </div>
    </div>
  );
}

function EmptyState({ title, detail, action }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center px-5 py-8 text-center">
      <span className="mb-3 grid h-10 w-10 place-items-center rounded-full bg-primary/10 text-primary"><Compass size={18} /></span>
      <p className="text-sm font-semibold text-ink">{title}</p>
      <p className="mt-1 max-w-xs text-xs leading-5 text-muted">{detail}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

function ChartTooltip({ active, payload, label, valueLabel = "Score" }) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  return (
    <div className="rounded-xl border border-line bg-surface px-3 py-2 text-xs shadow-card">
      <p className="font-semibold text-ink">{label}</p>
      <p className="mt-1 text-muted">{valueLabel}: <span className="font-semibold text-ink">{payload[0].value}%</span></p>
      {row?.event && <p className="mt-1 max-w-48 text-muted">{row.event}</p>}
    </div>
  );
}

function StatusChip({ status }) {
  const styles = {
    missing: "bg-rose-500/10 text-rose-600 dark:text-rose-300",
    weak: "bg-amber-500/10 text-amber-700 dark:text-amber-300",
    satisfied: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  };
  return <span className={classNames("rounded-full px-2 py-1 text-[10px] font-semibold capitalize", styles[status] || "bg-canvas text-muted")}>{status}</span>;
}

function Dashboard({ data, onRefresh, onGoalChange, onComplete, onTakeQuiz, onOpenRoadmap, highlight }) {
  const { learner, metrics, metric_calculations: calculations } = data;
  const visibleGaps = data.gaps.filter((gap) => gap.status !== "satisfied").slice(0, 5);
  const trendLabel = metrics.readiness_trend;
  const chartStyle = getComputedStyle(document.documentElement);
  const primary = chartStyle.getPropertyValue("--chart-primary").trim();
  const emerald = chartStyle.getPropertyValue("--chart-secondary").trim();
  const grid = chartStyle.getPropertyValue("--chart-grid").trim();
  const muted = chartStyle.getPropertyValue("--chart-muted").trim();
  const rose = chartStyle.getPropertyValue("--chart-rose").trim();
  const amber = chartStyle.getPropertyValue("--chart-amber").trim();

  const readiness = data.readiness_history.map((point) => ({
    ...point,
    label: formatTime(point.date),
  }));
  const quizData = [...data.recent_quizzes].reverse().map((quiz) => ({
    ...quiz,
    label: quiz.skill,
  }));

  return (
    <div className="space-y-5">
      <Card className={classNames("hero-wash overflow-visible p-5 sm:p-7", highlight === "hero" && "highlight-card")}>
        <div className="flex flex-col justify-between gap-6 xl:flex-row xl:items-center">
          <div className="min-w-0">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-line bg-surface/75 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[.12em] text-muted">Your learning command center</span>
              {data.target_role && <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary"><Target size={12} /> {data.target_role.name}</span>}
            </div>
            <h1 className="text-[26px] font-bold tracking-[-.055em] text-ink sm:text-[32px]">Welcome back, {learner.name}<span className="text-primary">.</span></h1>
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted">
              <span>Learning path for</span>
              <label className="relative inline-flex">
                <span className="sr-only">Switch target career role</span>
                <select
                  aria-label="Switch target career role"
                  value={learner.goal_role || ""}
                  onChange={(event) => onGoalChange(event.target.value)}
                  className="max-w-[230px] appearance-none rounded-lg border border-line bg-surface py-2 pl-3 pr-8 font-semibold text-ink shadow-sm"
                >
                  {data.roles.map((role) => <option key={role.id} value={role.name}>{role.name}</option>)}
                </select>
                <ChevronDown size={14} className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-muted" />
              </label>
            </div>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2">
            <button type="button" onClick={onRefresh} className="inline-flex items-center gap-2 rounded-xl border border-line bg-surface px-3.5 py-2.5 text-xs font-semibold text-ink transition hover:border-primary/40 hover:text-primary">
              <RotateCcw size={14} /> Refresh
            </button>
          </div>
        </div>
        <div className="mt-6 flex items-start gap-3 rounded-xl border border-primary/10 bg-primary/[.045] px-4 py-3.5">
          <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary"><Sparkles size={15} /></span>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[.13em] text-primary">Your AI learning insight</p>
            <p className="mt-1 text-sm leading-6 text-ink">{data.insight}</p>
          </div>
        </div>
      </Card>

      <div className={classNames("grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4", highlight === "metrics" && "highlight-card")}>
        <MetricCard
          label="Career match"
          value={metrics.career_match_percent}
          suffix="%"
          icon={Target}
          tone="bg-primary/10 text-primary"
          ring={metrics.career_match_percent}
          info={<>{calculations.career_match.weighted_skill_points} weighted skill points across {calculations.career_match.total_weight} role weight, normalized to your target role's required skills.</>}
          subline="weighted role fit"
        />
        <MetricCard
          label="Readiness score"
          value={metrics.readiness_score}
          suffix="%"
          icon={TrendingUp}
          tone="bg-violet-500/10 text-violet-600 dark:text-violet-300"
          ring={metrics.readiness_score}
          change={metrics.readiness_change}
          info={<>{calculations.readiness.weighted_proficiency_points} weighted proficiency points across {calculations.readiness.total_weight} role weight. Trend: {trendLabel}.</>}
          subline={`${trendLabel} since last activity`}
        />
        <MetricCard
          label="Roadmap complete"
          value={metrics.roadmap_completion_percent}
          suffix="%"
          icon={GitBranch}
          tone="bg-emerald-500/10 text-emerald-600 dark:text-emerald-300"
          ring={metrics.roadmap_completion_percent}
          info={<>{calculations.roadmap.completed_hours} hours completed out of {calculations.roadmap.total_hours} planned roadmap hours.</>}
          subline={`${metrics.roadmap_hours_done}h / ${metrics.roadmap_hours_total}h completed`}
        />
        <MetricCard
          label="Estimated completion"
          value={metrics.weeks_remaining}
          suffix="weeks"
          icon={Clock3}
          tone="bg-amber-500/10 text-amber-700 dark:text-amber-300"
          info={<>{calculations.completion.remaining_hours} learning hours remain at {calculations.completion.weekly_hours} hours per week.</>}
          subline={`Target date · ${formatDate(metrics.estimated_completion_date)}`}
        />
      </div>

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <MiniStat icon={Flame} label="Learning streak" value={metrics.learning_streak_days} suffix="days" tone="text-amber-600 dark:text-amber-300" />
        <MiniStat icon={Clock3} label="Hours this week" value={metrics.hours_this_week} suffix="hrs" tone="text-primary" decimals={1} />
        <MiniStat icon={Award} label="Average quiz score" value={metrics.average_quiz_score} suffix={metrics.average_quiz_score == null ? "" : "%"} tone="text-emerald-600 dark:text-emerald-300" empty="Take a quiz to begin" />
        <MiniStat icon={Trophy} label="Skills mastered" value={metrics.skills_mastered_count} suffix="skills" tone="text-violet-600 dark:text-violet-300" />
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.42fr)_minmax(320px,.86fr)]">
        <div className="space-y-4">
          <Card className={classNames("p-5 sm:p-6", highlight === "radar" && "highlight-card")}>
            <CardHeading
              eyebrow="Your skill profile"
              title="Skills vs. role requirements"
              action={<div className="flex items-center gap-3 text-[10px] text-muted"><LegendDot color={primary} label="You" /><LegendDot color={emerald} label="Role target" /></div>}
            />
            {data.radar.length ? (
              <div className="h-[270px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={data.radar} outerRadius="72%">
                    <PolarGrid stroke={grid} />
                    <PolarAngleAxis dataKey="skill" tick={{ fill: muted, fontSize: 10 }} />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
                    <Tooltip content={<RadarTooltip />} />
                    <Radar name="Role target" dataKey="required" stroke={emerald} fill={emerald} fillOpacity={0.08} strokeWidth={2} />
                    <Radar name="You" dataKey="current" stroke={primary} fill={primary} fillOpacity={0.22} strokeWidth={2} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            ) : <EmptyState title="Choose a target role" detail="Your skill radar will appear when a role is selected." />}
          </Card>

          <Card className={classNames("p-5 sm:p-6", highlight === "history" && "highlight-card")}>
            <CardHeading eyebrow="Momentum" title="Readiness over time" action={<span className="rounded-lg bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold capitalize text-emerald-700 dark:text-emerald-300">{trendLabel}</span>} />
            {readiness.length > 1 ? (
              <>
                <div className="h-[190px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={readiness} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
                      <CartesianGrid stroke={grid} vertical={false} />
                      <XAxis dataKey="label" tick={{ fill: muted, fontSize: 10 }} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={{ fill: muted, fontSize: 10 }} axisLine={false} tickLine={false} />
                      <Tooltip content={<ChartTooltip valueLabel="Readiness" />} />
                      <Line
                        type="monotone"
                        dataKey="readiness"
                        stroke={primary}
                        strokeWidth={2.5}
                        dot={(props) => <EventDot {...props} primary={primary} rose={rose} amber={amber} emerald={emerald} />}
                        activeDot={{ r: 5, fill: primary, stroke: "rgb(var(--surface))", strokeWidth: 3 }}
                        isAnimationActive
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 border-t border-line pt-3">
                  <LegendDot color={primary} label="Readiness" />
                  <LegendDot color={emerald} label="Resource completed" />
                  <LegendDot color={rose} label="Quiz taken" />
                  <LegendDot color={amber} label="Goal changed" />
                </div>
              </>
            ) : <EmptyState title="Your momentum starts here" detail="Complete a resource or take a quiz to add your first progress event." />}
          </Card>
        </div>

        <div className="space-y-4">
          <Card className={classNames("overflow-hidden p-5 sm:p-6", highlight === "action" && "highlight-card")}>
            <div className="mb-4 flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[.1em] text-primary"><Zap size={12} /> Next best action</span>
              <span className="text-[10px] text-muted">Personalized for you</span>
            </div>
            {data.next_best_action ? (
              <>
                <div className="mb-4 flex items-start gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary"><BookOpen size={18} /></span>
                  <div className="min-w-0">
                    <p className="text-[15px] font-semibold leading-5 text-ink">{data.next_best_action.title}</p>
                    <p className="mt-1 text-xs text-muted">{data.next_best_action.skill} <span className="px-1">·</span> {data.next_best_action.difficulty}</p>
                  </div>
                </div>
                <p className="mb-4 text-xs leading-5 text-muted">{data.next_best_action.reason}.</p>
                <div className="mb-4 flex items-center gap-3 text-[11px] text-muted">
                  <span className="inline-flex items-center gap-1"><Clock3 size={13} /> {data.next_best_action.duration_hours} hours</span>
                  <span className="rounded-full bg-canvas px-2 py-1 capitalize">{data.next_best_action.type}</span>
                </div>
                <div className="flex gap-2">
                  <a
                    href={data.next_best_action.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary px-3 py-2.5 text-xs font-semibold text-white transition hover:brightness-105"
                  >
                    <Play size={13} fill="currentColor" /> Start learning
                  </a>
                  <button
                    type="button"
                    onClick={() => onComplete(data.next_best_action.resource_id)}
                    className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-line px-3 py-2.5 text-xs font-semibold text-ink transition hover:border-emerald-500/40 hover:text-emerald-600"
                  >
                    <Check size={14} /> Mark done
                  </button>
                </div>
              </>
            ) : <EmptyState title="You're all caught up" detail="Choose a new target role to build your next learning path." />}
          </Card>

          <Card className={classNames("p-5 sm:p-6", highlight === "gaps" && "highlight-card")}>
            <CardHeading eyebrow="Focus next" title="Skill gap priorities" action={<span className="text-[10px] text-muted">Ranked by impact</span>} />
            {visibleGaps.length ? (
              <div className="space-y-4">
                {visibleGaps.map((gap) => {
                  const current = gap.learner_level || 0;
                  return (
                    <div key={gap.skill}>
                      <div className="mb-1.5 flex items-center justify-between gap-2">
                        <div className="flex min-w-0 items-center gap-2">
                          <span className="truncate text-xs font-semibold text-ink">{gap.skill}</span>
                          <StatusChip status={gap.status} />
                        </div>
                        {gap.recommended_resource?.url ? (
                          <a
                            href={gap.recommended_resource.url}
                            target="_blank"
                            rel="noreferrer"
                            className="shrink-0 text-[10px] font-semibold text-primary hover:underline"
                          >
                            Learn
                          </a>
                        ) : <span className="text-[10px] text-muted">{gap.priority}</span>}
                      </div>
                      <div className="flex items-center gap-2">
                        <div
                          className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-rose-500/15"
                          role="img"
                          aria-label={`${gap.skill}: current ${current}, required ${gap.required_level}`}
                        >
                          <div className="absolute inset-y-0 left-0 rounded-full bg-emerald-500/45" style={{ width: `${gap.required_level}%` }} />
                          {current > 0 && <div className="absolute inset-y-0 left-0 rounded-full bg-primary transition-all duration-700" style={{ width: `${current}%` }} />}
                        </div>
                        <span className="w-16 shrink-0 text-right text-[10px] tabular-nums text-muted">{current} <span className="text-line">/</span> {gap.required_level}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : <EmptyState title="No open skill gaps" detail="Your current skills meet the target role requirements." />}
          </Card>
        </div>
      </div>

      <Card className={classNames("overflow-hidden p-5 sm:p-6", highlight === "roadmap" && "highlight-card")}>
        <div className="mb-5 flex items-center justify-between gap-3">
          <div><p className="mb-1 text-[10px] font-bold uppercase tracking-[.15em] text-muted">Your learning path</p><h2 className="text-[15px] font-semibold text-ink">Roadmap snapshot</h2></div>
          <button type="button" onClick={() => onOpenRoadmap()} className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline">Open roadmap <ArrowRight size={13} /></button>
        </div>
        {data.roadmap.length ? (
          <div className="overflow-x-auto pb-2">
            <div className="flex min-w-max items-start">
              {data.roadmap.map((phase, index) => (
                <button
                  type="button"
                  onClick={() => onOpenRoadmap(phase.name)}
                  key={phase.name}
                  className="group flex w-[220px] items-start text-left focus-visible:rounded-xl"
                >
                  <div className="flex min-w-0 flex-col items-start">
                    <span className={classNames(
                      "mb-2 grid h-8 w-8 place-items-center rounded-full border text-xs font-bold transition group-hover:scale-105",
                      phase.status === "completed" ? "border-emerald-500 bg-emerald-500 text-white" : phase.status === "current" ? "border-primary bg-primary/10 text-primary" : "border-line bg-canvas text-muted",
                    )}>
                      {phase.status === "completed" ? <Check size={14} /> : index + 1}
                    </span>
                    <span className="mb-1 max-w-[190px] truncate text-xs font-semibold text-ink">{phase.name}</span>
                    <span className="text-[10px] text-muted">{phase.completion_percent}% complete</span>
                    <span className="mt-2 h-1.5 w-36 overflow-hidden rounded-full bg-canvas">
                      <span className={classNames("block h-full rounded-full", phase.status === "completed" ? "bg-emerald-500" : "bg-primary")} style={{ width: `${phase.completion_percent}%` }} />
                    </span>
                    {phase.items.some((item) => item.remedial) && <span className="mt-2 rounded-full bg-amber-500/10 px-2 py-1 text-[9px] font-semibold text-amber-700 dark:text-amber-300">Remedial step</span>}
                  </div>
                  {index < data.roadmap.length - 1 && <span className="mr-3 mt-4 h-px w-8 shrink-0 bg-line" />}
                </button>
              ))}
            </div>
          </div>
        ) : <EmptyState title="Your roadmap is ready to be built" detail="Pick a career goal to generate your personalized phases." />}
      </Card>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,.8fr)]">
        <Card className={classNames("p-5 sm:p-6", highlight === "assessment" && "highlight-card")}>
          <CardHeading eyebrow="Knowledge check-ins" title="Assessment & weak spots" action={<span className="text-[10px] text-muted">Recent quiz scores</span>} />
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(180px,.8fr)]">
            <div>
              {quizData.length ? (
                <div className="h-[205px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={quizData} margin={{ top: 10, right: 4, bottom: 0, left: -22 }}>
                      <CartesianGrid stroke={grid} vertical={false} />
                      <XAxis dataKey="label" tick={{ fill: muted, fontSize: 10 }} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={{ fill: muted, fontSize: 9 }} axisLine={false} tickLine={false} />
                      <Tooltip content={<ChartTooltip valueLabel="Quiz score" />} />
                      <ReferenceLine y={data.assessment_thresholds.pass} stroke={amber} strokeDasharray="4 4" />
                      <ReferenceLine y={data.assessment_thresholds.excellent} stroke={emerald} strokeDasharray="4 4" />
                      <Bar dataKey="score" radius={[5, 5, 0, 0]} maxBarSize={34} fill={primary} isAnimationActive />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState
                  title="No quiz scores yet"
                  detail="A quick check-in helps tune your learning path."
                  action={data.assessments[0] && <button type="button" onClick={() => onTakeQuiz(data.assessments[0])} className="rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-white">Take your first quiz</button>}
                />
              )}
              {quizData.length > 0 && <div className="mt-2 flex flex-wrap gap-4 text-[10px] text-muted"><LegendDot color={amber} label={`Pass · ${data.assessment_thresholds.pass}%`} /><LegendDot color={emerald} label={`Excellent · ${data.assessment_thresholds.excellent}%`} /></div>}
            </div>
            <div className="border-t border-line pt-4 xl:border-l xl:border-t-0 xl:pl-4 xl:pt-0">
              <p className="mb-3 text-xs font-semibold text-ink">Needs a little practice</p>
              {data.struggling_skills.length ? (
                <div className="space-y-2.5">
                  {data.struggling_skills.slice(0, 4).map((skill) => (
                    <div className="flex items-center justify-between gap-2" key={skill.skill}>
                      <div className="min-w-0">
                        <p className="truncate text-xs font-medium text-ink">{skill.skill}</p>
                        <p className="text-[10px] text-muted">{skill.level == null ? "Not assessed yet" : `${skill.level} proficiency`}</p>
                      </div>
                      {skill.assessment_id ? (
                        <button type="button" onClick={() => onTakeQuiz(data.assessments.find((quiz) => quiz.id === skill.assessment_id))} className="shrink-0 rounded-lg border border-line px-2 py-1.5 text-[10px] font-semibold text-primary hover:bg-primary/5">Take quiz</button>
                      ) : <span className="text-[10px] text-muted">Coming soon</span>}
                    </div>
                  ))}
                </div>
              ) : <p className="text-xs leading-5 text-muted">No struggling skills right now. Keep your momentum going.</p>}
            </div>
          </div>
        </Card>

        <Card className={classNames("p-5 sm:p-6", highlight === "activity" && "highlight-card")}>
          <CardHeading eyebrow="Learning signals" title="Recent progress" action={<Activity size={16} className="text-muted" />} />
          {data.agent_activity.length ? (
            <div className="relative space-y-4 before:absolute before:bottom-3 before:left-[13px] before:top-3 before:w-px before:bg-line">
              {data.agent_activity.slice(-4).reverse().map((item) => (
                <div className="relative flex gap-3" key={item.id}>
                  <span className="z-10 grid h-7 w-7 shrink-0 place-items-center rounded-full border border-line bg-surface text-primary"><Sparkles size={13} /></span>
                  <div className="min-w-0 flex-1 pt-0.5">
                    <p className="text-xs font-medium leading-5 text-ink">{item.action}</p>
                    <p className="mt-0.5 text-[10px] text-muted">{item.agent} <span className="px-1">·</span> {formatTime(item.created_at)}</p>
                  </div>
                  <ArrowRight size={13} className="mt-1 shrink-0 text-muted/60" />
                </div>
              ))}
              <button type="button" onClick={() => document.getElementById("agent-activity")?.scrollIntoView({ behavior: "smooth" })} className="ml-10 text-[11px] font-semibold text-primary hover:underline">View full trace</button>
            </div>
          ) : <EmptyState title="Your activity will show up here" detail="Complete a learning task to see how your plan adapts." />}
        </Card>
      </div>

      <div id="agent-activity" className="grid gap-4 lg:grid-cols-2">
        <MentorCard data={data} />
        <Card className={classNames("p-5 sm:p-6", highlight === "activity" && "highlight-card")}>
          <CardHeading eyebrow="Behind the plan" title="Agent activity" action={<span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold text-emerald-700 dark:text-emerald-300"><span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" /> Live</span>} />
          {data.agent_activity.length ? (
            <div className="max-h-[270px] space-y-0 overflow-y-auto pr-1">
              {[...data.agent_activity].reverse().map((item, index, entries) => (
                <div key={item.id} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary"><AgentIcon name={item.agent} /></span>
                    {index < entries.length - 1 && <span className="my-1 h-7 w-px bg-line" />}
                  </div>
                  <div className="min-w-0 flex-1 pb-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs font-semibold text-ink">{item.agent}</p>
                      <span className="shrink-0 text-[10px] text-muted">{formatTime(item.created_at)}</span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-muted">{item.action}</p>
                    {index < entries.length - 1 && <div className="mt-2 inline-flex items-center gap-1 text-[9px] text-muted/80"><ArrowDownRight size={11} /> handed off to next step</div>}
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyState title="No agent traces yet" detail="Your learning activity will appear in this timeline." />}
        </Card>
      </div>
    </div>
  );
}

function MiniStat({ icon: Icon, label, value, suffix, tone, decimals = 0, empty }) {
  const isEmpty = value == null;
  const shown = useCountUp(Number(value) || 0);
  return (
    <div className="flex min-w-0 items-center gap-3 rounded-xl border border-line bg-surface/65 px-3.5 py-3">
      <span className={classNames("grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-canvas", tone)}><Icon size={15} /></span>
      <div className="min-w-0">
        <p className="truncate text-[10px] font-medium text-muted">{label}</p>
        <p className="mt-0.5 truncate text-sm font-bold text-ink tabular-nums">{isEmpty ? <span className="text-[11px] font-medium text-muted">{empty}</span> : <>{shown.toFixed(decimals)} <span className="text-[10px] font-medium text-muted">{suffix}</span></>}</p>
      </div>
    </div>
  );
}

function LegendDot({ color, label }) {
  return <span className="inline-flex items-center gap-1.5 whitespace-nowrap"><span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />{label}</span>;
}

function EventDot(props) {
  const { cx, cy, payload, primary, rose, amber, emerald } = props;
  const color = payload?.kind === "quiz" ? rose : payload?.kind === "goal_changed" ? amber : payload?.kind === "resource_completed" ? emerald : primary;
  return <circle cx={cx} cy={cy} r={4} fill={color} stroke="rgb(var(--surface))" strokeWidth={2} />;
}

function RadarTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  return (
    <div className="rounded-xl border border-line bg-surface px-3 py-2 text-xs shadow-card">
      <p className="mb-1 font-semibold text-ink">{row?.skill}</p>
      <p className="text-muted">Current: <span className="font-semibold text-primary">{row?.current}</span></p>
      <p className="text-muted">Role target: <span className="font-semibold text-emerald-600 dark:text-emerald-300">{row?.required}</span></p>
    </div>
  );
}

function AgentIcon({ name }) {
  if (name?.includes("Progress")) return <Activity size={15} />;
  if (name?.includes("Assessment")) return <GraduationCap size={15} />;
  if (name?.includes("Roadmap")) return <GitBranch size={15} />;
  return <Sparkles size={15} />;
}

function MentorCard({ data }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);
  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), [messages]);
  const replies = {
    "What should I do this week?": data.next_best_action
      ? `Start with ${data.next_best_action.title}. It should take about ${data.next_best_action.duration_hours} hours and closes your highest-impact ${data.next_best_action.skill} gap.`
      : "You have no open gaps in this roadmap. A new career goal will give us a fresh direction.",
    "Why was this recommended?": data.next_best_action
      ? `${data.next_best_action.reason}. The ranking weighs gap impact against the time needed to learn.`
      : "Your current roadmap is complete. Choose another role to see new recommendations.",
    "I'm struggling with JavaScript": (() => {
      const gap = data.gaps.find((item) => item.skill.toLowerCase() === "javascript");
      return gap
        ? `That's okay—JavaScript is ${gap.status} at ${gap.learner_level ?? "not assessed"} against a target of ${gap.required_level}. Try a short beginner exercise, then take a quick quiz.`
        : "Your current role doesn't require JavaScript. Want to switch back to a web development path?";
    })(),
  };
  const send = (text) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const reply = replies[trimmed] || (data.next_best_action ? `For your ${data.target_role?.name || "career"} goal, ${data.next_best_action.reason.toLowerCase()}.` : "Tell me more about the role you're working toward.");
    setMessages((current) => [...current, { text: trimmed, from: "learner" }, { text: reply, from: "mentor" }]);
    setInput("");
  };
  return (
    <Card className="p-5 sm:p-6">
      <CardHeading eyebrow="Your learning copilot" title="Mentor" action={<span className="grid h-8 w-8 place-items-center rounded-xl bg-primary/10 text-primary"><Sparkles size={16} /></span>} />
      <div className="mb-4 max-h-40 min-h-[72px] space-y-2 overflow-y-auto">
        {!messages.length ? (
          <div className="rounded-xl rounded-tl-sm bg-canvas px-3 py-2.5 text-xs leading-5 text-muted">I’m here to help you keep moving. Your plan is based on your current skills and career goal.</div>
        ) : messages.map((message, index) => (
          <div key={`${message.from}-${index}`} className={classNames("max-w-[90%] rounded-xl px-3 py-2 text-xs leading-5", message.from === "learner" ? "ml-auto rounded-tr-sm bg-primary text-white" : "rounded-tl-sm bg-canvas text-muted")}>{message.text}</div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="mb-3 flex flex-wrap gap-1.5">
        {Object.keys(replies).map((prompt) => (
          <button key={prompt} type="button" onClick={() => send(prompt)} className="rounded-full border border-line px-2.5 py-1.5 text-[10px] font-medium text-muted transition hover:border-primary/35 hover:text-primary">{prompt}</button>
        ))}
      </div>
      <form className="flex gap-2" onSubmit={(event) => { event.preventDefault(); send(input); }}>
        <label className="sr-only" htmlFor="mentor-input">Ask your mentor</label>
        <input id="mentor-input" value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask your mentor..." className="min-w-0 flex-1 rounded-xl border border-line bg-canvas px-3 py-2.5 text-xs text-ink placeholder:text-muted focus:border-primary/50 focus:outline-none" />
        <button type="submit" aria-label="Send message" className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-primary text-white transition hover:brightness-105"><Send size={14} /></button>
      </form>
    </Card>
  );
}

function RoadmapPage({ data, initialPhase, onBack, onComplete, highlight }) {
  return (
    <main className="mx-auto max-w-[1280px] space-y-5 px-4 py-6 sm:px-7">
      <button type="button" onClick={onBack} className="inline-flex items-center gap-1.5 text-xs font-semibold text-muted hover:text-primary"><ChevronLeft size={15} /> Dashboard</button>
      <Card className="hero-wash p-6 sm:p-8">
        <p className="text-[10px] font-bold uppercase tracking-[.15em] text-primary">Learning roadmap</p>
        <h1 className="mt-2 text-2xl font-bold tracking-[-.04em] text-ink">{data.learner.name}'s path to {data.target_role?.name}</h1>
        <p className="mt-2 text-sm text-muted">{data.metrics.roadmap_hours_done} of {data.metrics.roadmap_hours_total} roadmap hours completed · {data.metrics.weeks_remaining} weeks at your current pace</p>
      </Card>
      {data.roadmap.map((phase, index) => (
        <Card key={phase.name} className={classNames("p-5 sm:p-6", highlight === "roadmap" && initialPhase === phase.name && "highlight-card")}>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className={classNames("grid h-9 w-9 place-items-center rounded-full text-sm font-bold", phase.status === "completed" ? "bg-emerald-500 text-white" : phase.status === "current" ? "bg-primary/10 text-primary" : "bg-canvas text-muted")}>{phase.status === "completed" ? <Check size={16} /> : index + 1}</span>
              <div><h2 className="text-sm font-semibold text-ink">{phase.name}</h2><p className="mt-0.5 text-xs text-muted">{phase.completion_percent}% complete</p></div>
            </div>
            {phase.items.some((item) => item.remedial) && <span className="rounded-full bg-amber-500/10 px-2.5 py-1 text-[10px] font-semibold text-amber-700 dark:text-amber-300">Remedial focus</span>}
          </div>
          <div className="space-y-2">
            {phase.items.map((item) => (
              <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line bg-surface px-3.5 py-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span className={classNames("grid h-8 w-8 shrink-0 place-items-center rounded-lg", item.status === "done" ? "bg-emerald-500/10 text-emerald-600" : "bg-canvas text-muted")}>{item.status === "done" ? <CheckCircle2 size={16} /> : <BookOpen size={15} />}</span>
                  <div className="min-w-0"><p className="truncate text-xs font-semibold text-ink">{item.title}</p><p className="mt-0.5 text-[10px] capitalize text-muted">{item.skill || "Learning activity"} · {item.status.replace("_", " ")}</p></div>
                </div>
                <div className="flex items-center gap-2">
                  {item.remedial && <span className="rounded-full bg-amber-500/10 px-2 py-1 text-[9px] font-semibold text-amber-700 dark:text-amber-300">Remedial</span>}
                  {item.status !== "done" && item.resource_id && <button type="button" onClick={() => onComplete(item.resource_id)} className="rounded-lg border border-line px-2.5 py-1.5 text-[10px] font-semibold text-primary hover:bg-primary/5">Mark done</button>}
                </div>
              </div>
            ))}
          </div>
        </Card>
      ))}
    </main>
  );
}

function Toasts({ items, dismiss }) {
  return (
    <div className="fixed right-4 top-4 z-[80] flex w-[min(360px,calc(100vw-2rem))] flex-col gap-2" aria-live="polite">
      {items.map((toast) => (
        <div key={toast.id} role="status" className="toast-enter flex items-start gap-2.5 rounded-xl border border-line bg-surface px-3.5 py-3 shadow-card">
          <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-emerald-500" />
          <p className="flex-1 text-xs leading-5 text-ink">{toast.message}</p>
          <button type="button" onClick={() => dismiss(toast.id)} aria-label="Dismiss notification" className="text-muted hover:text-ink"><X size={14} /></button>
        </div>
      ))}
    </div>
  );
}

function QuizModal({ assessment, onClose, onSubmit, submitting }) {
  const [answers, setAnswers] = useState(() => assessment.questions.map(() => -1));
  const allAnswered = answers.every((answer) => answer >= 0);
  return (
    <div className="fixed inset-0 z-[70] grid place-items-center bg-slate-950/45 p-4" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section role="dialog" aria-modal="true" aria-labelledby="quiz-title" className="max-h-[88vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-line bg-surface p-5 shadow-2xl sm:p-7">
        <div className="mb-5 flex items-start justify-between gap-3">
          <div><p className="text-[10px] font-bold uppercase tracking-[.14em] text-primary">Skill check-in</p><h2 id="quiz-title" className="mt-1 text-lg font-bold text-ink">{assessment.title}</h2><p className="mt-1 text-xs text-muted">{assessment.questions.length} questions · your result updates your skill profile</p></div>
          <button type="button" aria-label="Close quiz" onClick={onClose} className="rounded-lg p-2 text-muted hover:bg-canvas"><X size={16} /></button>
        </div>
        <div className="space-y-5">
          {assessment.questions.map((question, questionIndex) => (
            <fieldset key={`${assessment.id}-${questionIndex}`}>
              <legend className="mb-2 text-xs font-semibold leading-5 text-ink">{questionIndex + 1}. {question.question}</legend>
              <div className="grid gap-2 sm:grid-cols-2">
                {question.options.map((option, optionIndex) => (
                  <label key={option} className={classNames("flex cursor-pointer items-start gap-2.5 rounded-xl border px-3 py-2.5 text-xs transition", answers[questionIndex] === optionIndex ? "border-primary bg-primary/5 text-ink" : "border-line text-muted hover:border-primary/30")}>
                    <input type="radio" name={`q-${questionIndex}`} value={optionIndex} checked={answers[questionIndex] === optionIndex} onChange={() => setAnswers((current) => current.map((answer, index) => index === questionIndex ? optionIndex : answer))} className="mt-0.5 accent-[rgb(var(--primary))]" />
                    <span>{option}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          ))}
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-xl border border-line px-4 py-2.5 text-xs font-semibold text-muted hover:text-ink">Cancel</button>
          <button type="button" disabled={!allAnswered || submitting} onClick={() => onSubmit(answers)} className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">{submitting ? "Submitting..." : "Submit quiz"} <ArrowRight size={13} /></button>
        </div>
      </section>
    </div>
  );
}

function DemoBanner({ step, total }) {
  return (
    <div className="fixed inset-x-0 bottom-0 z-50 border-t border-primary/20 bg-surface/95 px-4 py-3 shadow-[0_-8px_30px_rgba(15,23,42,.08)] backdrop-blur-md" role="status" aria-live="polite">
      <div className="mx-auto flex max-w-[1500px] items-center gap-3">
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary"><Play size={15} fill="currentColor" /></span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center justify-between gap-1">
            <p className="truncate text-xs font-semibold text-ink">Demo scenario <span className="font-normal text-muted">· Step {step}/{total}: {DEMO_STEPS[step - 1]}</span></p>
            <span className="text-[10px] font-medium text-primary">{Math.round(step / total * 100)}%</span>
          </div>
          <div className="mt-2 h-1 overflow-hidden rounded-full bg-canvas"><div className="h-full rounded-full bg-primary transition-all duration-500" style={{ width: `${step / total * 100}%` }} /></div>
        </div>
      </div>
    </div>
  );
}

function ErrorState({ error, onRetry }) {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-lg flex-col items-center justify-center px-5 text-center">
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-rose-500/10 text-rose-500"><Activity size={20} /></span>
      <h1 className="mt-4 text-lg font-bold text-ink">We couldn't load your dashboard</h1>
      <p className="mt-2 text-sm leading-6 text-muted">{error}</p>
      <p className="mt-2 text-xs text-muted">Make sure the FastAPI server is running and the database has been seeded.</p>
      <button type="button" onClick={onRetry} className="mt-5 rounded-xl bg-primary px-4 py-2.5 text-xs font-semibold text-white">Try again</button>
    </div>
  );
}

export default function App() {
  const [learnerId, setLearnerId] = useState(() => Number(localStorage.getItem("skillpath-learner-id")) || null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [theme, setTheme] = useState(() => localStorage.getItem("skillpath-theme") || "light");
  const [toasts, setToasts] = useState([]);
  const [busy, setBusy] = useState("");
  const [demoStep, setDemoStep] = useState(0);
  const [highlight, setHighlight] = useState("");
  const [quiz, setQuiz] = useState(null);
  const [submittingQuiz, setSubmittingQuiz] = useState(false);
  const [view, setView] = useState("dashboard");
  const [selectedPhase, setSelectedPhase] = useState("");
  const [showCreateProfile, setShowCreateProfile] = useState(false);
  const idRef = useRef(learnerId);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("skillpath-theme", theme);
  }, [theme]);

  const notify = useCallback((message) => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((current) => [...current.slice(-2), { id, message }]);
    window.setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), 5500);
  }, []);

  const refresh = useCallback(async (id = idRef.current) => {
    if (!id) {
      setLoading(true);
      try {
        const learners = await api("/api/learners");
        const selected = learners.find((item) => item.name === "Aarav") || learners[0];
        if (!selected) {
          setShowCreateProfile(true);
          setData(null);
          setLoading(false);
          return;
        }
        idRef.current = selected.id;
        setLearnerId(selected.id);
        localStorage.setItem("skillpath-learner-id", selected.id);
        const dashboard = await api(`/api/dashboard/${selected.id}`);
        setData(dashboard);
        setError("");
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
      return;
    }
    setLoading(true);
    try {
      const dashboard = await api(`/api/dashboard/${id}`);
      setData(dashboard);
      setError("");
      setShowCreateProfile(false);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const createProfile = async () => {
    setBusy("create");
    try {
      const profile = await api("/api/learners", {
        method: "POST",
        body: JSON.stringify({ name: "Aarav", education: "Undergraduate", goal_role: "Full Stack Developer", weekly_hours: 8 }),
      });
      idRef.current = profile.id;
      setLearnerId(profile.id);
      localStorage.setItem("skillpath-learner-id", profile.id);
      setShowCreateProfile(false);
      await refresh(profile.id);
      notify("Profile created. Seed the catalog to load roles and learning resources.");
    } catch (requestError) {
      notify(requestError.message);
    } finally {
      setBusy("");
    }
  };

  const handleGoalChange = async (goalRole) => {
    if (!data || goalRole === data.learner.goal_role) return;
    setBusy("goal");
    try {
      const result = await api(`/api/learners/${data.learner.id}/goal`, {
        method: "POST",
        body: JSON.stringify({ goal_role: goalRole }),
      });
      await refresh(data.learner.id);
      setHighlight("hero");
      notify(result.message);
      window.setTimeout(() => setHighlight(""), 2600);
    } catch (requestError) {
      notify(requestError.message);
    } finally {
      setBusy("");
    }
  };

  const completeResource = async (resourceId) => {
    if (!data || !resourceId) return;
    setBusy("resource");
    try {
      const result = await api(`/api/learners/${data.learner.id}/resources/${resourceId}/complete`, { method: "POST" });
      await refresh(data.learner.id);
      setHighlight("metrics");
      notify(`Roadmap updated: ${result.message}`);
      window.setTimeout(() => setHighlight(""), 2600);
    } catch (requestError) {
      notify(requestError.message);
    } finally {
      setBusy("");
    }
  };

  const submitQuiz = async (answers) => {
    if (!quiz || !data) return;
    setSubmittingQuiz(true);
    try {
      const result = await api(`/api/learners/${data.learner.id}/assessments/${quiz.id}/submit`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      });
      setQuiz(null);
      await refresh(data.learner.id);
      setHighlight("assessment");
      notify(`${result.skill} assessment updated your readiness and recommendations.`);
      window.setTimeout(() => setHighlight(""), 2600);
    } catch (requestError) {
      notify(requestError.message);
    } finally {
      setSubmittingQuiz(false);
    }
  };

  const resetDemo = async () => {
    if (!data) return;
    setBusy("reset");
    setDemoStep(0);
    try {
      const result = await api(`/api/demo/${data.learner.id}/reset`, { method: "POST" });
      await refresh(data.learner.id);
      setView("dashboard");
      setHighlight("hero");
      notify(result.message);
      window.setTimeout(() => setHighlight(""), 2600);
    } catch (requestError) {
      notify(requestError.message);
    } finally {
      setBusy("");
    }
  };

  const runDemo = async () => {
    if (!data || busy) return;
    setBusy("demo");
    setView("dashboard");
    const learner = data.learner;
    const firstResource = data.next_best_action?.resource_id;
    try {
      for (let step = 1; step <= DEMO_STEPS.length; step += 1) {
        setDemoStep(step);
        await delay(1050);
        if (step === 3 && firstResource) {
          await api(`/api/learners/${learner.id}/resources/${firstResource}/complete`, { method: "POST" });
          await refresh(learner.id);
          setHighlight("action");
        }
        if (step === 4) {
          await api(`/api/demo/${learner.id}/quiz`, {
            method: "POST",
            body: JSON.stringify({ skill: "JavaScript", score: 45 }),
          });
          await refresh(learner.id);
          setHighlight("assessment");
        }
        if (step === 5) {
          await refresh(learner.id);
          setHighlight("gaps");
        }
        if (step === 6) {
          await api(`/api/learners/${learner.id}/goal`, {
            method: "POST",
            body: JSON.stringify({ goal_role: "Data Analyst" }),
          });
          await refresh(learner.id);
          setHighlight("hero");
        }
        if (step === 7) {
          await refresh(learner.id);
          setHighlight("history");
        }
        await delay(450);
      }
      setDemoStep(0);
      notify("Demo complete: your learning plan adapted to your resource, quiz, and new career goal.");
      window.setTimeout(() => setHighlight(""), 3200);
    } catch (requestError) {
      setDemoStep(0);
      notify(`Demo stopped: ${requestError.message}`);
    } finally {
      setBusy("");
    }
  };

  const handleCreateProfile = async () => {
    await createProfile();
  };

  if (loading && !data && !error) return <SkeletonDashboard />;
  if (error && !data) return <><ErrorState error={error} onRetry={() => refresh()} /><Toasts items={toasts} dismiss={(id) => setToasts((current) => current.filter((item) => item.id !== id))} /></>;
  if (!data && showCreateProfile) {
    return (
      <div className="mx-auto grid min-h-screen max-w-lg place-items-center px-5">
        <Card className="w-full p-7 text-center">
          <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-primary/10 text-primary"><GraduationCap size={22} /></span>
          <h1 className="mt-4 text-xl font-bold text-ink">Start your learning journey</h1>
          <p className="mt-2 text-sm leading-6 text-muted">No learner profile is available yet. Seed the backend demo data or create Aarav's starter profile.</p>
          <button type="button" disabled={busy === "create"} onClick={handleCreateProfile} className="mt-5 rounded-xl bg-primary px-4 py-2.5 text-xs font-semibold text-white disabled:opacity-50">{busy === "create" ? "Creating..." : "Create starter profile"}</button>
        </Card>
      </div>
    );
  }
  if (!data) return <SkeletonDashboard />;

  return (
    <div className="min-h-screen bg-canvas pb-8 text-ink">
      <header className="sticky top-0 z-40 border-b border-line bg-surface/90 backdrop-blur-xl">
        <div className="mx-auto flex h-[62px] max-w-[1600px] items-center justify-between gap-3 px-4 sm:px-7">
          <a href="#" className="flex shrink-0 items-center gap-2.5" aria-label="SkillPath AI home">
            <span className="grid h-8 w-8 place-items-center rounded-xl bg-primary text-white shadow-sm"><Sparkles size={17} /></span>
            <span className="text-sm font-bold tracking-[-.035em] text-ink">SkillPath<span className="text-primary">.</span></span>
            <span className="hidden rounded-full bg-primary/10 px-1.5 py-0.5 text-[9px] font-bold text-primary sm:inline">AI</span>
          </a>
          <nav aria-label="Primary navigation" className="hidden items-center gap-1 sm:flex">
            <button type="button" onClick={() => setView("dashboard")} className={classNames("rounded-lg px-3 py-2 text-xs font-semibold transition", view === "dashboard" ? "bg-canvas text-ink" : "text-muted hover:text-ink")}>Overview</button>
            <button type="button" onClick={() => setView("roadmap")} className={classNames("rounded-lg px-3 py-2 text-xs font-semibold transition", view === "roadmap" ? "bg-canvas text-ink" : "text-muted hover:text-ink")}>Roadmap</button>
          </nav>
          <div className="flex items-center gap-2">
            <button type="button" disabled={Boolean(busy)} onClick={runDemo} className="hidden items-center gap-1.5 rounded-lg border border-line bg-surface px-3 py-2 text-[11px] font-semibold text-ink transition hover:border-primary/40 hover:text-primary sm:inline-flex">
              <Play size={12} fill="currentColor" /> {busy === "demo" ? "Running demo..." : "Run demo"}
            </button>
            <button type="button" disabled={Boolean(busy)} onClick={resetDemo} aria-label="Reset demo" title="Reset demo" className="hidden rounded-lg border border-line p-2 text-muted transition hover:border-rose-300 hover:text-rose-500 sm:grid"><RotateCcw size={14} /></button>
            <button type="button" onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")} className="grid h-9 w-9 place-items-center rounded-lg border border-line text-muted transition hover:text-ink" aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}>{theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}</button>
            <span className="grid h-8 w-8 place-items-center rounded-full bg-primary/10 text-[11px] font-bold text-primary">{data.learner.name.slice(0, 1).toUpperCase()}</span>
          </div>
        </div>
        <div className="flex gap-2 border-t border-line px-4 py-2 sm:hidden">
          <button type="button" disabled={Boolean(busy)} onClick={runDemo} className="inline-flex items-center gap-1.5 rounded-lg border border-line px-2.5 py-1.5 text-[10px] font-semibold text-ink"><Play size={11} fill="currentColor" />Run demo</button>
          <button type="button" disabled={Boolean(busy)} onClick={resetDemo} className="inline-flex items-center gap-1.5 rounded-lg border border-line px-2.5 py-1.5 text-[10px] font-semibold text-muted"><RotateCcw size={11} />Reset</button>
          <button type="button" onClick={() => setView(view === "dashboard" ? "roadmap" : "dashboard")} className="rounded-lg border border-line px-2.5 py-1.5 text-[10px] font-semibold text-muted">{view === "dashboard" ? "Roadmap" : "Overview"}</button>
        </div>
      </header>

      {view === "roadmap" ? (
        <RoadmapPage
          data={data}
          initialPhase={selectedPhase}
          onBack={() => setView("dashboard")}
          onComplete={completeResource}
          highlight={highlight}
        />
      ) : (
        <main className="mx-auto max-w-[1600px] space-y-5 px-4 py-5 sm:px-7 sm:py-7">
          <Dashboard
            data={data}
            onRefresh={() => refresh(data.learner.id)}
            onGoalChange={handleGoalChange}
            onComplete={completeResource}
            onTakeQuiz={(selected) => selected && setQuiz(selected)}
            onOpenRoadmap={(phase = "") => { setSelectedPhase(phase); setView("roadmap"); }}
            highlight={highlight}
          />
        </main>
      )}
      {demoStep > 0 && <DemoBanner step={demoStep} total={DEMO_STEPS.length} />}
      {quiz && <QuizModal assessment={quiz} onClose={() => setQuiz(null)} onSubmit={submitQuiz} submitting={submittingQuiz} />}
      <Toasts items={toasts} dismiss={(id) => setToasts((current) => current.filter((item) => item.id !== id))} />
    </div>
  );
}
