import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateInput: string | Date | null | undefined): string {
  if (!dateInput) return "TBD";
  const date = typeof dateInput === "string" ? new Date(dateInput) : dateInput;
  if (isNaN(date.getTime())) return "TBD";
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function timeAgo(dateInput: string | Date | null | undefined): string {
  if (!dateInput) return "Just now";
  const date = typeof dateInput === "string" ? new Date(dateInput) : dateInput;
  if (isNaN(date.getTime())) return "Just now";
  
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (seconds < 60) return "Just now";
  
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

export function getStatusColor(status: string): string {
  if (!status) return "bg-zinc-500/20 text-zinc-400 border-zinc-500/30";
  const colors: Record<string, string> = {
    draft: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
    applied: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    screening: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    interview: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    assessment: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
    offer: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    rejected: "bg-rose-500/20 text-rose-400 border-rose-500/30",
    withdrawn: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    accepted: "bg-teal-500/20 text-teal-400 border-teal-500/30",
  };
  return colors[status.toLowerCase()] || "bg-zinc-500/20 text-zinc-400 border-zinc-500/30";
}

export function getPriorityColor(priority: string): string {
  if (!priority) return "bg-zinc-500/20 text-zinc-400 border-zinc-500/30";
  const colors: Record<string, string> = {
    low: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    medium: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    high: "bg-rose-500/20 text-rose-400 border-rose-500/30",
  };
  return colors[priority.toLowerCase()] || "bg-zinc-500/20 text-zinc-400 border-zinc-500/30";
}
