"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { authApi, aiApi } from "@/lib/api";
import type { User } from "@/types";

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [aiHealth, setAiHealth] = useState<{ status: string; model: string; available: boolean } | null>(null);
  const [fullName, setFullName] = useState("");
  const [saving, setSaving] = useState(false);
  const [integrations, setIntegrations] = useState<{
    gmail: { connected: boolean; email: string };
    telegram: { connected: boolean; chat_id: string };
  } | null>(null);

  useEffect(() => {
    authApi.me().then((data) => {
      const u = data as User;
      setUser(u);
      setFullName(u.full_name);
    }).catch(console.error);

    aiApi.health().then((data) => setAiHealth(data as { status: string; model: string; available: boolean })).catch(console.error);
    
    aiApi.integrationsStatus().then((data) => setIntegrations(data as any)).catch(console.error);
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = (await authApi.updateMe({ full_name: fullName })) as User;
      setUser(updated);
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Profile */}
      <Card className="glass-card border-0">
        <CardHeader><CardTitle className="text-base">Profile</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm text-muted-foreground mb-1 block">Full Name</label>
            <input value={fullName} onChange={(e) => setFullName(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50" />
          </div>
          <div>
            <label className="text-sm text-muted-foreground mb-1 block">Email</label>
            <input value={user?.email || ""} disabled className="w-full px-4 py-2.5 rounded-lg bg-muted/50 border border-border text-sm text-muted-foreground cursor-not-allowed" />
          </div>
          <Button onClick={handleSave} disabled={saving} className="bg-primary hover:bg-primary/90">
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </CardContent>
      </Card>

      {/* Integrations */}
      <Card className="glass-card border-0">
        <CardHeader><CardTitle className="text-base">Integrations</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50 border border-border">
            <div className="flex items-center gap-3">
              <span className="text-xl">🤖</span>
              <div>
                <p className="text-sm font-medium">AI Engine (Gemini)</p>
                <p className="text-xs text-muted-foreground">{aiHealth?.model || "gemini-flash-latest"}</p>
              </div>
            </div>
            <Badge variant="outline" className={aiHealth?.available ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" : "bg-red-500/20 text-red-400 border-red-500/30"}>
              {aiHealth?.available ? "Connected" : "Disconnected"}
            </Badge>
          </div>
          <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50 border border-border">
            <div className="flex items-center gap-3">
              <span className="text-xl">📱</span>
              <div>
                <p className="text-sm font-medium">Telegram Bot</p>
                <p className="text-xs text-muted-foreground">{integrations?.telegram.connected ? `Connected (ID: ${integrations.telegram.chat_id})` : "Not connected"}</p>
              </div>
            </div>
            <Badge variant="outline" className={integrations?.telegram.connected ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" : "bg-zinc-500/20 text-zinc-400 border-zinc-500/30"}>
              {integrations?.telegram.connected ? "Active" : "Setup Required"}
            </Badge>
          </div>
          <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50 border border-border">
            <div className="flex items-center gap-3">
              <span className="text-xl">📧</span>
              <div>
                <p className="text-sm font-medium">Gmail Integration</p>
                <p className="text-xs text-muted-foreground">{integrations?.gmail.connected ? `Active monitoring for ${integrations.gmail.email}` : "Email monitoring via Gmail API"}</p>
              </div>
            </div>
            <Badge variant="outline" className={integrations?.gmail.connected ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" : "bg-zinc-500/20 text-zinc-400 border-zinc-500/30"}>
              {integrations?.gmail.connected ? "Active" : "Setup Required"}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card className="glass-card border-0">
        <CardHeader><CardTitle className="text-base">About</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            <span className="gradient-text font-bold">JobPilot</span> v1.0.0 — AI-Powered Job Application Management Platform
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
