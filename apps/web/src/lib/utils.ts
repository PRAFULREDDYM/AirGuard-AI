import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatAQI(pm25: number): { label: string; color: string; bg: string; textColor: string } {
  if (pm25 <= 12.0) {
    return { label: "Good", color: "#10b981", bg: "bg-emerald-500/10", textColor: "text-emerald-500" };
  } else if (pm25 <= 35.4) {
    return { label: "Moderate", color: "#f59e0b", bg: "bg-amber-500/10", textColor: "text-amber-500" };
  } else if (pm25 <= 55.4) {
    return { label: "Unhealthy for Sensitive Groups", color: "#f97316", bg: "bg-orange-500/10", textColor: "text-orange-500" };
  } else if (pm25 <= 150.4) {
    return { label: "Unhealthy", color: "#ef4444", bg: "bg-red-500/10", textColor: "text-red-500" };
  } else if (pm25 <= 250.4) {
    return { label: "Very Unhealthy", color: "#8b5cf6", bg: "bg-purple-500/10", textColor: "text-purple-500" };
  } else {
    return { label: "Hazardous", color: "#881337", bg: "bg-rose-950/20", textColor: "text-rose-600" };
  }
}

