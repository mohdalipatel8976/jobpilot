"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { interviewsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Interview } from "@/types";

export default function InterviewsPage() {
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [upcoming, setUpcoming] = useState<Interview[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      interviewsApi.list(),
      interviewsApi.upcoming(20),
    ]).then(([allData, upData]) => {
      setInterviews((allData as { items: Interview[] }).items || []);
      setUpcoming((upData as { items: Interview[] }).items || []);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      scheduled: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      completed: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
      cancelled: "bg-red-500/20 text-red-400 border-red-500/30",
      rescheduled: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    };
    return colors[status] || colors.scheduled;
  };

  if (loading) {
    return <div className="space-y-4">{[...Array(4)].map((_, i) => <div key={i} className="skeleton h-24 rounded-xl" />)}</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Interviews</h1>
        <p className="text-muted-foreground text-sm">{interviews.length} total · {upcoming.length} upcoming</p>
      </div>

      {/* Upcoming Section */}
      {upcoming.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Upcoming
          </h2>
          <div className="grid md:grid-cols-2 gap-4">
            {upcoming.map((interview) => (
              <Card key={interview.id} className="glass-card border-0 hover:border-purple-500/30 transition-all">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold capitalize">{interview.round_type.replace(/_/g, " ")}</h3>
                      <p className="text-sm text-muted-foreground">Round {interview.round_number}</p>
                    </div>
                    <Badge variant="outline" className={getStatusBadge(interview.status) + " text-xs"}>
                      {interview.status}
                    </Badge>
                  </div>
                  <div className="space-y-2 text-sm">
                    {interview.scheduled_at && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        {formatDate(interview.scheduled_at)} · {new Date(interview.scheduled_at).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}
                      </div>
                    )}
                    {interview.duration_minutes && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        {interview.duration_minutes} minutes
                      </div>
                    )}
                    {interview.interviewer_name && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                        {interview.interviewer_name}
                      </div>
                    )}
                    {interview.location_or_link && (
                      <div className="flex items-center gap-2 text-muted-foreground truncate">
                        <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /></svg>
                        <span className="truncate">{interview.location_or_link}</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* All Interviews */}
      <div>
        <h2 className="text-lg font-semibold mb-3">All Interviews</h2>
        {interviews.length > 0 ? (
          <div className="space-y-3">
            {interviews.map((interview) => (
              <Card key={interview.id} className="glass-card border-0">
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center shrink-0 text-purple-400 font-bold">
                    R{interview.round_number}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium capitalize truncate">{interview.round_type.replace(/_/g, " ")}</p>
                    <p className="text-xs text-muted-foreground">
                      {interview.scheduled_at ? formatDate(interview.scheduled_at) : "Not scheduled"}
                      {interview.interviewer_name && ` · ${interview.interviewer_name}`}
                    </p>
                  </div>
                  <Badge variant="outline" className={getStatusBadge(interview.status) + " text-xs"}>
                    {interview.status}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="glass-card border-0">
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">No interviews yet. They&apos;ll appear here when you schedule them.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
