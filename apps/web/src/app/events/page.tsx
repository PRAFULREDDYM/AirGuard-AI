"use client";

import React, { useState, useEffect } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Filter,
  ShieldCheck,
  Clock,
  Sparkles,
  HelpCircle,
  MessageSquare
} from "lucide-react";
import { api } from "@/lib/api";

export default function EventsPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);

  const loadEvents = async () => {
    try {
      const params: any = {};
      if (filterSeverity !== "ALL") params.severity = filterSeverity;
      const data = await api.getEvents(params);
      setEvents(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [filterSeverity]);

  const handleAcknowledge = async (eventId: string, feedback: string) => {
    await api.acknowledgeEvent(eventId, feedback);
    setFeedbackSuccess(`Feedback '${feedback}' recorded for event.`);
    setTimeout(() => setFeedbackSuccess(null), 3000);
    loadEvents();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Environmental Events & Alerts</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Chronological audit of sensor threshold exceedances, pattern anomalies, and safety alerts.
          </p>
        </div>

        {/* Severity Filter Pills */}
        <div className="flex items-center gap-1.5 bg-card p-1 rounded-xl border border-border text-xs">
          {["ALL", "ELEVATED", "WARNING", "ANOMALY", "CERTIFIED_ALARM"].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                filterSeverity === sev
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              {sev.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {feedbackSuccess && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-medium">
          {feedbackSuccess}
        </div>
      )}

      {/* Events Timeline List */}
      <div className="space-y-4">
        {events.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-card border border-border text-sm text-muted-foreground">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            No events found matching current filter. Air quality within target thresholds.
          </div>
        ) : (
          events.map((event) => (
            <div
              key={event.id}
              className={`p-6 rounded-2xl bg-card border border-border shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                event.acknowledged ? "opacity-75" : ""
              }`}
            >
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                      event.severity === "WARNING"
                        ? "bg-red-500/10 text-red-500"
                        : event.severity === "ELEVATED"
                        ? "bg-amber-500/10 text-amber-500"
                        : event.severity === "CERTIFIED_ALARM"
                        ? "bg-purple-500/10 text-purple-500"
                        : "bg-blue-500/10 text-blue-500"
                    }`}
                  >
                    {event.severity}
                  </span>
                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(event.started_at).toLocaleString()}
                  </span>
                  {event.acknowledged && (
                    <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Acknowledged ({event.user_feedback || "reviewed"})
                    </span>
                  )}
                </div>

                <h2 className="text-base font-bold text-foreground">{event.title}</h2>
                <p className="text-xs text-muted-foreground max-w-2xl">{event.description}</p>

                {event.anomaly_score !== null && (
                  <div className="text-[11px] text-muted-foreground pt-1 flex items-center gap-3">
                    <span>Statistical Anomaly Score: <strong>{event.anomaly_score}</strong></span>
                    {event.classification && (
                      <span>Pattern Classification: <strong>{event.classification}</strong> ({Math.round((event.classification_confidence || 0) * 100)}% conf)</span>
                    )}
                  </div>
                )}
              </div>

              {/* Acknowledgment & Feedback Actions */}
              {!event.acknowledged ? (
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs text-muted-foreground font-medium">Verify:</span>
                  <button
                    onClick={() => handleAcknowledge(event.id, "accurate")}
                    className="px-3 py-1.5 rounded-lg border border-border text-xs font-medium hover:bg-emerald-500/10 hover:text-emerald-500 transition-colors"
                  >
                    Accurate
                  </button>
                  <button
                    onClick={() => handleAcknowledge(event.id, "false_positive")}
                    className="px-3 py-1.5 rounded-lg border border-border text-xs font-medium hover:bg-amber-500/10 hover:text-amber-500 transition-colors"
                  >
                    False Alarm
                  </button>
                  <button
                    onClick={() => handleAcknowledge(event.id, "unknown")}
                    className="px-3 py-1.5 rounded-lg border border-border text-xs font-medium hover:bg-muted"
                  >
                    Unknown
                  </button>
                </div>
              ) : (
                <div className="text-xs text-muted-foreground font-medium shrink-0">
                  Audit Verified
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

