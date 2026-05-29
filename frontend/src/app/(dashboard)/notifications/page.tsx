"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { notificationsApi } from "@/lib/api";
import { timeAgo } from "@/lib/utils";
import type { Notification } from "@/types";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    setLoading(true);
    notificationsApi.list().then((data) => {
      setNotifications((data as { items: Notification[] }).items || []);
    }).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const handleMarkAllRead = async () => {
    await notificationsApi.markAllRead();
    fetchData();
  };

  const handleMarkRead = async (id: string) => {
    await notificationsApi.markRead(id);
    fetchData();
  };

  const typeIcon: Record<string, string> = {
    interview: "🎯",
    assessment: "📝",
    offer: "🎉",
    rejection: "❌",
    follow_up: "⏰",
    deadline: "📅",
    system: "⚙️",
  };

  if (loading) return <div className="space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Notifications</h1>
        {notifications.some((n) => !n.is_read) && (
          <Button variant="outline" size="sm" onClick={handleMarkAllRead}>Mark all read</Button>
        )}
      </div>
      {notifications.length > 0 ? (
        <div className="space-y-2">
          {notifications.map((n) => (
            <Card key={n.id} className={`glass-card border-0 transition-all ${!n.is_read ? "border-l-2 border-l-primary" : "opacity-70"}`}>
              <CardContent className="p-4 flex items-center gap-4">
                <span className="text-xl">{typeIcon[n.type] || "🔔"}</span>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm ${!n.is_read ? "font-semibold" : "font-normal"}`}>{n.title}</p>
                  {n.message && <p className="text-xs text-muted-foreground truncate">{n.message}</p>}
                  <p className="text-xs text-muted-foreground mt-0.5">{timeAgo(n.created_at)}</p>
                </div>
                {!n.is_read && (
                  <Button size="sm" variant="ghost" onClick={() => handleMarkRead(n.id)} className="text-xs text-muted-foreground">
                    Mark read
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="glass-card border-0">
          <CardContent className="py-12 text-center">
            <p className="text-3xl mb-2">🔔</p>
            <p className="text-muted-foreground">No notifications yet. You&apos;re all caught up!</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
