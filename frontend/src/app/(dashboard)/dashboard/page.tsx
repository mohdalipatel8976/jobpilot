"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { applicationsApi, aiApi } from "@/lib/api";
import { formatDate, getStatusColor } from "@/lib/utils";
import type { Application } from "@/types";

type ParsedJob = {
  company_name?: string | null;
  job_title?: string | null;
  location?: string | null;
  work_type?: string | null;
  employment_type?: string | null;
  salary_range?: string | null;
  seniority_level?: string | null;
  experience_years?: string | null;
  experience_summary?: string | null;
  technologies?: string[];
  requirements?: string[];
  responsibilities?: string[];
  benefits?: string[];
  job_description?: string | null;
  summary?: string | null;
};

type IntegrationStatus = {
  ai?: { connected: boolean; provider: string; model: string };
  gmail?: { connected: boolean; email: string };
  telegram?: { connected: boolean; chat_id: string };
};

export default function DashboardPage() {
  const [recentApps, setRecentApps] = useState<Application[]>([]);
  const [totalApplications, setTotalApplications] = useState(0);
  const [integrations, setIntegrations] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const [jobText, setJobText] = useState("");
  const [parseLoading, setParseLoading] = useState(false);
  const [jobResult, setJobResult] = useState<ParsedJob | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleParseJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobText.trim()) return;
    setParseLoading(true);
    setParseError(null);
    setJobResult(null);
    setSaveSuccess(false);
    
    try {
      const data = await aiApi.parseJob(jobText) as { success: boolean; data?: any; error?: string };
      if (data.success && data.data) {
        setJobResult(data.data as ParsedJob);
      } else {
        setParseError(data.error || "The AI parser could not extract the posting. Try a fuller job description or email body.");
      }
    } catch (err: any) {
      console.error(err);
      setParseError(err.detail || err.message || "Failed to connect to the backend parser.");
    } finally {
      setParseLoading(false);
    }
  };

  const handleSaveApplication = async () => {
    if (!jobResult) return;
    setSaveLoading(true);
    try {
      const payload = {
        company_name: jobResult.company_name || "Unknown Company",
        job_title: jobResult.job_title || "Parsed Job Posting",
        job_url: "",
        job_description_raw: jobText,
        job_description_parsed: jobResult,
        source: "AI Parser",
        location: jobResult.location || "",
        work_type: jobResult.work_type || "",
        employment_type: jobResult.employment_type || "",
        seniority_level: jobResult.seniority_level || "",
        experience_years: jobResult.experience_years || "",
        experience_summary: jobResult.experience_summary || "",
        technologies: jobResult.technologies || [],
        priority: "medium",
        status: "applied",
        notes: jobResult.summary || "",
      };
      await applicationsApi.create(payload);
      setSaveSuccess(true);
      
      const appsData = await applicationsApi.list({ page: "1", page_size: "5" });
      const result = appsData as { items: Application[]; total?: number };
      setRecentApps(result.items || []);
      setTotalApplications(result.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setSaveLoading(false);
    }
  };

  useEffect(() => {
    Promise.all([
      applicationsApi.list({ page: "1", page_size: "5" }),
      aiApi.integrationsStatus(),
    ])
      .then(([appsData, integrationsData]) => {
        const result = appsData as { items: Application[]; total?: number };
        setRecentApps(result.items || []);
        setTotalApplications(result.total || 0);
        setIntegrations(integrationsData as IntegrationStatus);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const connectionCards = [
    {
      label: "AI Parser",
      value: integrations?.ai?.connected ? `${integrations.ai.provider} · ${integrations.ai.model}` : "Not configured",
      tone: integrations?.ai?.connected ? "text-emerald-400" : "text-muted-foreground",
    },
    {
      label: "Gmail Sync",
      value: integrations?.gmail?.connected ? integrations.gmail.email : "Not connected",
      tone: integrations?.gmail?.connected ? "text-cyan-400" : "text-muted-foreground",
    },
    {
      label: "Telegram",
      value: integrations?.telegram?.connected ? "Connected" : "Not linked",
      tone: integrations?.telegram?.connected ? "text-amber-400" : "text-muted-foreground",
    },
    {
      label: "Tracked Jobs",
      value: totalApplications,
      tone: "text-blue-400",
    },
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton h-28 rounded-xl" />
          ))}
        </div>
        <div className="skeleton h-96 rounded-xl" />
        <div className="skeleton h-72 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="border-0 bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 text-white shadow-2xl shadow-black/20 overflow-hidden">
        <CardContent className="p-6 lg:p-8 relative">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(59,130,246,0.22),_transparent_35%),radial-gradient(circle_at_bottom_left,_rgba(16,185,129,0.18),_transparent_30%)]" />
          <div className="relative grid gap-6 lg:grid-cols-[1.3fr_0.9fr] items-start">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/70">
                Job capture and application tracking
              </div>
              <div>
                <h1 className="text-3xl lg:text-4xl font-semibold tracking-tight">Track every job you apply to.</h1>
                <p className="mt-3 max-w-2xl text-sm lg:text-base text-white/70">
                  Paste a job posting or a recruiter email, extract the company, title, location, experience, and description, then save it into your application log.
                </p>
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {connectionCards.map((card) => (
                  <div key={card.label} className="rounded-xl border border-white/10 bg-white/5 p-3 backdrop-blur">
                    <p className="text-[11px] uppercase tracking-[0.16em] text-white/50">{card.label}</p>
                    <p className={`mt-1 text-sm font-medium ${card.tone}`}>{card.value}</p>
                  </div>
                ))}
              </div>
            </div>

            <Card className="border-white/10 bg-white/5 backdrop-blur-xl text-white">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Quick Capture</CardTitle>
                <p className="text-xs text-white/60">The parser understands job ads and confirmation emails.</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <form onSubmit={handleParseJob} className="space-y-3">
                  <textarea
                    value={jobText}
                    onChange={(e) => setJobText(e.target.value)}
                    rows={5}
                    placeholder='Paste text like "Analyst - Data Science ..." or a confirmation email here.'
                    className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-white/20 resize-none"
                  />
                  <Button
                    type="submit"
                    disabled={parseLoading || !jobText.trim()}
                    className="w-full bg-white text-black hover:bg-white/90"
                  >
                    {parseLoading ? "Parsing..." : "Parse job details"}
                  </Button>
                </form>
                {parseError && (
                  <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200">
                    {parseError}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {jobResult && (
        <Card className="glass-card border-0 animate-fade-in">
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <CardTitle className="text-lg">Parsed Job</CardTitle>
                <p className="text-sm text-muted-foreground">Review the extracted fields, then save it as a tracked application.</p>
              </div>
              {saveSuccess ? (
                <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">Saved</Badge>
              ) : (
                <Button onClick={handleSaveApplication} disabled={saveLoading} className="bg-emerald-500 hover:bg-emerald-600 text-white">
                  {saveLoading ? "Saving..." : "Save as application"}
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3 text-sm">
              <div className="rounded-xl border border-border/60 bg-muted/30 p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Company</p>
                <p className="mt-1 font-medium">{jobResult.company_name || "Not detected"}</p>
              </div>
              <div className="rounded-xl border border-border/60 bg-muted/30 p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Job title</p>
                <p className="mt-1 font-medium">{jobResult.job_title || "Not detected"}</p>
              </div>
              <div className="rounded-xl border border-border/60 bg-muted/30 p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Experience</p>
                <p className="mt-1 font-medium">{jobResult.experience_years || jobResult.experience_summary || "Not specified"}</p>
              </div>
              <div className="rounded-xl border border-border/60 bg-muted/30 p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Location</p>
                <p className="mt-1 font-medium">{jobResult.location || "Not specified"}</p>
              </div>
              <div className="rounded-xl border border-border/60 bg-muted/30 p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Work type</p>
                <p className="mt-1 font-medium capitalize">{jobResult.work_type || "Not specified"}</p>
              </div>
              <div className="rounded-xl border border-border/60 bg-muted/30 p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Employment type</p>
                <p className="mt-1 font-medium capitalize">{jobResult.employment_type || "Not specified"}</p>
              </div>
              <div className="rounded-xl border border-border/60 bg-muted/30 p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Seniority</p>
                <p className="mt-1 font-medium capitalize">{jobResult.seniority_level || "Not specified"}</p>
              </div>
            </div>

            {jobResult.summary && (
              <div className="rounded-xl border border-border/60 bg-muted/30 p-4 text-sm leading-relaxed">
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Summary</p>
                <p>{jobResult.summary}</p>
              </div>
            )}

            {jobResult.job_description && (
              <div className="rounded-xl border border-border/60 bg-muted/30 p-4 text-sm leading-relaxed">
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Job description</p>
                <p>{jobResult.job_description}</p>
              </div>
            )}

            <div className="grid gap-4 lg:grid-cols-3">
              {Array.isArray(jobResult.requirements) && jobResult.requirements.length > 0 && (
                <div>
                  <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Requirements</p>
                  <div className="flex flex-wrap gap-2">
                    {jobResult.requirements.map((item) => (
                      <span key={item} className="rounded-full border border-border px-2.5 py-1 text-xs">{item}</span>
                    ))}
                  </div>
                </div>
              )}
              {Array.isArray(jobResult.responsibilities) && jobResult.responsibilities.length > 0 && (
                <div>
                  <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Responsibilities</p>
                  <div className="flex flex-wrap gap-2">
                    {jobResult.responsibilities.map((item) => (
                      <span key={item} className="rounded-full border border-border px-2.5 py-1 text-xs">{item}</span>
                    ))}
                  </div>
                </div>
              )}
              {Array.isArray(jobResult.technologies) && jobResult.technologies.length > 0 && (
                <div>
                  <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Technologies</p>
                  <div className="flex flex-wrap gap-2">
                    {jobResult.technologies.map((item) => (
                      <span key={item} className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-xs text-primary">{item}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="glass-card border-0">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Recent Applications</CardTitle>
            <p className="text-xs text-muted-foreground">{totalApplications} total tracked jobs</p>
          </CardHeader>
          <CardContent>
            {recentApps.length > 0 ? (
              <div className="space-y-3">
                {recentApps.map((app) => (
                  <div key={app.id} className="flex items-start gap-3 rounded-xl border border-border/60 bg-muted/30 p-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-sm font-bold text-primary">
                      {app.company_name?.[0] || "#"}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-medium truncate">{app.company_name}</p>
                        <Badge variant="outline" className={`${getStatusColor(app.status)} text-[10px]`}>
                          {app.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground truncate">{app.job_title}</p>
                      <div className="mt-1 flex flex-wrap gap-3 text-xs text-muted-foreground">
                        {app.location && <span>📍 {app.location}</span>}
                        {app.work_type && <span className="capitalize">🏢 {app.work_type}</span>}
                        {app.applied_date && <span>📅 {formatDate(app.applied_date)}</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No applications yet. Parse a posting to get started.</p>
            )}
          </CardContent>
        </Card>

        <Card className="glass-card border-0">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Sync Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-muted/30 p-3">
              <span>AI parser</span>
              <span className={integrations?.ai?.connected ? "text-emerald-400" : "text-muted-foreground"}>
                {integrations?.ai?.connected ? `${integrations.ai.provider} · ${integrations.ai.model}` : "Not configured"}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-muted/30 p-3">
              <span>Gmail auto-update</span>
              <span className={integrations?.gmail?.connected ? "text-cyan-400" : "text-muted-foreground"}>
                {integrations?.gmail?.connected ? integrations.gmail.email : "Disconnected"}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-muted/30 p-3">
              <span>Telegram alerts</span>
              <span className={integrations?.telegram?.connected ? "text-amber-400" : "text-muted-foreground"}>
                {integrations?.telegram?.connected ? "Linked" : "Not linked"}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Telegram remains active for alerts, while Gmail can auto-capture recruiter messages into tracked applications.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
