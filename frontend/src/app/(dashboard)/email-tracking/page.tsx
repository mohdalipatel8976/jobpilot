"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { emailEventsApi } from "@/lib/api";
import { formatDate, timeAgo } from "@/lib/utils";

interface EmailEvent {
  id: string; subject: string | null; from_address: string | null;
  classification: string | null; body_snippet: string | null;
  is_processed: boolean; received_at: string | null; created_at: string;
}

export default function EmailTrackingPage() {
  const [events, setEvents] = useState<EmailEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    emailEventsApi.list().then((data) => {
      setEvents((data as { items: EmailEvent[] }).items || []);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const classificationColors: Record<string, string> = {
    interview_invite: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    rejection: "bg-red-500/20 text-red-400 border-red-500/30",
    offer: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    assessment: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    confirmation: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    general: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
  };

  if (loading) return <div className="space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-20 rounded-xl" />)}</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Email Tracking</h1>
      {events.length > 0 ? (
        <div className="space-y-3">
          {events.map((e) => (
            <Card key={e.id} className="glass-card border-0">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center shrink-0">
                    <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{e.subject || "No subject"}</p>
                    <p className="text-xs text-muted-foreground">{e.from_address || "Unknown sender"}</p>
                    {e.body_snippet && <p className="text-xs text-muted-foreground mt-1 truncate">{e.body_snippet}</p>}
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    {e.classification && (
                      <Badge variant="outline" className={`text-xs ${classificationColors[e.classification] || classificationColors.general}`}>
                        {e.classification.replace(/_/g, " ")}
                      </Badge>
                    )}
                    <span className="text-[10px] text-muted-foreground">{e.received_at ? timeAgo(e.received_at) : ""}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="glass-card border-0">
          <CardContent className="py-12 text-center">
            <p className="text-3xl mb-2">📧</p>
            <p className="text-muted-foreground">No email events tracked yet. Connect your Gmail to start monitoring.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
