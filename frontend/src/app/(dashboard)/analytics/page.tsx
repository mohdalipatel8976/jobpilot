"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { analyticsApi } from "@/lib/api";
import type { AnalyticsOverview, StatusBreakdown, TrendDataPoint } from "@/types";

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [breakdown, setBreakdown] = useState<StatusBreakdown[]>([]);
  const [trends, setTrends] = useState<TrendDataPoint[]>([]);
  const [platforms, setPlatforms] = useState<Array<{ platform: string; applications: number; responses: number; response_rate: number }>>([]);
  const [heatmap, setHeatmap] = useState<Array<{ date: string; count: number }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsApi.overview(),
      analyticsApi.statusBreakdown(),
      analyticsApi.trends(90),
      analyticsApi.platformPerformance(),
      analyticsApi.heatmap(),
    ]).then(([o, b, t, p, h]) => {
      setOverview(o as AnalyticsOverview);
      setBreakdown(b as StatusBreakdown[]);
      setTrends(t as TrendDataPoint[]);
      setPlatforms(p as Array<{ platform: string; applications: number; responses: number; response_rate: number }>);
      setHeatmap(h as Array<{ date: string; count: number }>);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const maxTrend = Math.max(...trends.map((t) => t.count), 1);

  if (loading) {
    return <div className="space-y-6">{[...Array(4)].map((_, i) => <div key={i} className="skeleton h-64 rounded-xl" />)}</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics</h1>

      {/* Metric Cards */}
      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Response Rate", value: `${overview.response_rate}%`, icon: "📊", color: "text-cyan-400" },
            { label: "Interview Rate", value: `${overview.interview_conversion_rate}%`, icon: "🎯", color: "text-purple-400" },
            { label: "Offer Rate", value: overview.total_applications > 0 ? `${((overview.total_offers / overview.total_applications) * 100).toFixed(1)}%` : "0%", icon: "🏆", color: "text-emerald-400" },
            { label: "Rejection Rate", value: overview.total_applications > 0 ? `${((overview.total_rejections / overview.total_applications) * 100).toFixed(1)}%` : "0%", icon: "📉", color: "text-red-400" },
          ].map((m) => (
            <Card key={m.label} className="glass-card border-0">
              <CardContent className="p-5 text-center">
                <span className="text-2xl">{m.icon}</span>
                <p className={`text-3xl font-bold mt-2 ${m.color}`}>{m.value}</p>
                <p className="text-xs text-muted-foreground mt-1">{m.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Application Trends (Bar Chart) */}
        <Card className="glass-card border-0">
          <CardHeader>
            <CardTitle className="text-base">Application Trends (90 days)</CardTitle>
          </CardHeader>
          <CardContent>
            {trends.length > 0 ? (
              <div className="flex items-end gap-1 h-48">
                {trends.slice(-30).map((t, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center justify-end h-full group">
                    <div
                      className="w-full bg-primary/60 rounded-t-sm group-hover:bg-primary transition-colors min-h-[2px]"
                      style={{ height: `${(t.count / maxTrend) * 100}%` }}
                    />
                    <span className="text-[8px] text-muted-foreground mt-1 hidden group-hover:block">
                      {t.count}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm text-center py-12">No data yet</p>
            )}
          </CardContent>
        </Card>

        {/* Status Distribution */}
        <Card className="glass-card border-0">
          <CardHeader>
            <CardTitle className="text-base">Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {breakdown.length > 0 ? (
              <div className="space-y-4">
                {breakdown.map((item) => {
                  const colors: Record<string, string> = {
                    draft: "bg-gray-500", applied: "bg-blue-500", screening: "bg-cyan-500",
                    interview: "bg-purple-500", assessment: "bg-amber-500", offer: "bg-emerald-500",
                    rejected: "bg-red-500", withdrawn: "bg-zinc-500", accepted: "bg-green-500",
                  };
                  return (
                    <div key={item.status}>
                      <div className="flex justify-between text-sm mb-1.5">
                        <span className="capitalize font-medium">{item.status}</span>
                        <span className="text-muted-foreground">{item.count} ({item.percentage}%)</span>
                      </div>
                      <div className="h-3 rounded-full bg-muted overflow-hidden">
                        <div
                          className={`h-full rounded-full ${colors[item.status] || "bg-primary"} transition-all duration-1000`}
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm text-center py-12">No data yet</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Platform Performance */}
      <Card className="glass-card border-0">
        <CardHeader>
          <CardTitle className="text-base">Platform Performance</CardTitle>
        </CardHeader>
        <CardContent>
          {platforms.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-muted-foreground font-medium">Platform</th>
                    <th className="text-right py-3 px-4 text-muted-foreground font-medium">Applications</th>
                    <th className="text-right py-3 px-4 text-muted-foreground font-medium">Responses</th>
                    <th className="text-right py-3 px-4 text-muted-foreground font-medium">Response Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {platforms.map((p) => (
                    <tr key={p.platform} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-4 font-medium">{p.platform}</td>
                      <td className="py-3 px-4 text-right">{p.applications}</td>
                      <td className="py-3 px-4 text-right">{p.responses}</td>
                      <td className="py-3 px-4 text-right">
                        <span className={p.response_rate > 20 ? "text-emerald-400" : p.response_rate > 10 ? "text-amber-400" : "text-red-400"}>
                          {p.response_rate}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-muted-foreground text-sm text-center py-8">Track your application sources to see platform performance</p>
          )}
        </CardContent>
      </Card>

      {/* Activity Heatmap */}
      <Card className="glass-card border-0">
        <CardHeader>
          <CardTitle className="text-base">Application Activity (365 days)</CardTitle>
        </CardHeader>
        <CardContent>
          {heatmap.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {heatmap.map((day, i) => {
                const intensity = day.count === 0 ? "bg-muted" : day.count <= 1 ? "bg-emerald-900/50" : day.count <= 3 ? "bg-emerald-700/50" : "bg-emerald-500/70";
                return (
                  <div
                    key={i}
                    className={`w-3 h-3 rounded-sm ${intensity} transition-colors`}
                    title={`${day.date}: ${day.count} applications`}
                  />
                );
              })}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm text-center py-8">Activity data will appear as you add applications</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
