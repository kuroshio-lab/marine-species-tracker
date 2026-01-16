"use client";

import { User } from "@/types/user";

interface UserRoleBadgeProps {
  user: User;
  variant?: "compact" | "full";
}

export default function UserRoleBadge({
  user,
  variant = "full",
}: UserRoleBadgeProps) {
  const roleConfig = {
    hobbyist: {
      label: "Hobbyist",
      shortLabel: "Hobbyist",
      icon: "🔍",
      bgColor: "bg-white/10",
      textColor: "text-white/90",
      borderColor: "border-white/20",
      description: "Observer",
    },
    researcher_pending: {
      label: "Researcher - Pending",
      shortLabel: "Pending",
      icon: "⏱️",
      bgColor: "bg-semantic-warning-500/20",
      textColor: "text-semantic-warning-500",
      borderColor: "border-semantic-warning-500/50",
      description: "Under Review",
      clickable: true,
    },
    researcher_community: {
      label: "Community Researcher",
      shortLabel: "Verified",
      icon: "✓",
      bgColor: "bg-semantic-success-500/20",
      textColor: "text-semantic-success-500",
      borderColor: "border-semantic-success-500/50",
      description: "Can Validate",
    },
    researcher_institutional: {
      label: "Institutional Researcher",
      shortLabel: "Institutional",
      icon: "✓✓",
      bgColor: "bg-brand-primary-300/20",
      textColor: "text-brand-primary-300",
      borderColor: "border-brand-primary-300/50",
      description: "Full Access",
    },
  };

  const config = roleConfig[user.role] || roleConfig.hobbyist;

  if (variant === "compact") {
    return (
      <button
        // onClick and disabled attributes removed
        className={`
          flex items-center gap-2 px-3 py-1.5 rounded-lg border backdrop-blur-sm
          ${config.bgColor} ${config.borderColor}
          cursor-default // Always default cursor
        `}
        type="button"
      >
        <span className="text-sm">{config.icon}</span>
        <span className={`text-xs font-semibold ${config.textColor}`}>
          {config.shortLabel}
        </span>
      </button>
    );
  }

  return (
    <button
      // onClick and disabled attributes removed
      className={`
        group relative flex items-center gap-2.5 px-4 py-2 rounded-lg border backdrop-blur-sm
        ${config.bgColor} ${config.borderColor}
        cursor-default // Always default cursor
      `}
      type="button"
    >
      {/* Icon */}
      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white/10">
        <span className="text-lg">{config.icon}</span>
      </div>

      {/* Text Content */}
      <div className="flex flex-col items-start">
        <span
          className={`text-xs font-semibold ${config.textColor} leading-tight`}
        >
          {config.label}
        </span>
        <span className="text-[10px] text-white/60 leading-tight">
          {config.description}
        </span>
      </div>
    </button>
  );
}
