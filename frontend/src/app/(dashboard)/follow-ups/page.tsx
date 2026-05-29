"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { followUpsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { FollowUp } from "@/types";

export default function FollowUpsPage() {
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    setLoading(true);
    followUpsApi.list().then((data) => {
      setFollowUps((data as { items: FollowUp[] }).items || []);
    }).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const handleComplete = async (id: string) => {
    await followUpsApi.complete(id);
    fetchData();
  };

  const getStatusStyle = (status: string) => {
    const styles: Record<string, string> = {
      pending: "bg-amber-500/20 text-amber-400 border-amber-500/30",
      overdue: "bg-red-500/20 text-red-400 border-red-500/30",
      completed: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
      skipped: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
    };
    return styles[status] || styles.pending;
  };

  if (loading) return <div className="space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-20 rounded-xl" />)}</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Follow-ups</h1>
      {followUps.length > 0 ? (
        <div className="space-y-3">
          {followUps.map((fu) => (
            <Card key={fu.id} className="glass-card border-0">
              <CardContent className="p-4 flex items-center gap-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${fu.status === "overdue" || fu.status === "pending" ? "bg-amber-500/10" : "bg-emerald-500/10"}`}>
                  <svg className={`w-5 h-5 ${fu.status === "overdue" || fu.status === "pending" ? "text-amber-400" : "text-emerald-400"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium capitalize">{fu.type.replace(/_/g, " ")}</p>
                  <p className="text-xs text-muted-foreground">Due: {formatDate(fu.due_date)}</p>
                </div>
                <Badge variant="outline" className={getStatusStyle(fu.status) + " text-xs"}>{fu.status}</Badge>
                {fu.status !== "completed" && (
                  <Button size="sm" variant="outline" onClick={() => handleComplete(fu.id)} className="text-xs">
                    ✓ Complete
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="glass-card border-0">
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No follow-ups scheduled.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
