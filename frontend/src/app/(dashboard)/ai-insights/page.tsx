"use client";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { aiApi } from "@/lib/api";

export default function AIInsightsPage() {
  const [insights, setInsights] = useState<Record<string, any> | null>(null);
  const [jobResult, setJobResult] = useState<Record<string, any> | null>(null);
  const [jobText, setJobText] = useState("");
  const [loading, setLoading] = useState(false);
  const [parseLoading, setParseLoading] = useState(false);

  const [insightsError, setInsightsError] = useState<string | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  const handleGenerateInsights = async () => {
    setLoading(true);
    setInsightsError(null);
    setInsights(null);
    try {
      const data = (await aiApi.generateInsights(30)) as { success: boolean; data?: Record<string, unknown>; error?: string };
      if (data.success && data.data) {
        setInsights(data.data);
      } else {
        setInsightsError(data.error || "Failed to generate AI insights.");
      }
    } catch (e: any) {
      console.error(e);
      setInsightsError(e.detail || e.message || "Failed to connect to the backend AI insights endpoint.");
    } finally {
      setLoading(false);
    }
  };

  const handleParseJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobText.trim()) return;
    setParseLoading(true);
    setParseError(null);
    setJobResult(null);
    try {
      const data = (await aiApi.parseJob(jobText)) as { success: boolean; data?: Record<string, unknown>; error?: string };
      if (data.success && data.data) {
        setJobResult(data.data);
      } else {
        setParseError(data.error || "AI failed to parse the job description. Ensure GEMINI_API_KEY is configured on the backend.");
      }
    } catch (e: any) {
      console.error(e);
      setParseError(e.detail || e.message || "Failed to connect to the backend AI parser endpoint.");
    } finally {
      setParseLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">AI Insights</h1>

      {/* Generate Insights */}
      <Card className="glass-card border-0">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <span className="text-xl">🧠</span>
            AI-Powered Strategy Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4 font-normal leading-relaxed">
            Analyze your application patterns and get AI-powered recommendations to improve your job search strategy.
          </p>
          <Button onClick={handleGenerateInsights} disabled={loading} className="bg-primary hover:bg-primary/90">
            {loading ? "Analyzing Applications..." : "Generate Insights"}
          </Button>

          {/* Loader */}
          {loading && (
            <div className="mt-6 p-6 rounded-lg bg-muted/30 border border-border/50 flex flex-col items-center justify-center space-y-2 animate-pulse">
              <div className="w-6 h-6 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              <p className="text-xs text-muted-foreground">Generating application strategy insights using Gemini...</p>
            </div>
          )}

          {/* Error Alert */}
          {insightsError && (
            <div className="mt-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs space-y-1">
              <p className="font-semibold">⚠️ Insights Generation Failed</p>
              <p className="text-muted-foreground leading-relaxed">{insightsError}</p>
            </div>
          )}

          {insights && (
            <div className="mt-6 space-y-4">
              {insights.summary && (
                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                  <h4 className="text-sm font-semibold mb-1">Summary</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">{String(insights.summary)}</p>
                </div>
              )}
              {Array.isArray(insights.recommendations) && insights.recommendations.length > 0 && (
                <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                  <h4 className="text-sm font-semibold mb-2 text-primary">Recommendations</h4>
                  <ul className="space-y-1.5">
                    {(insights.recommendations as string[]).map((r, i) => (
                      <li key={i} className="text-sm text-muted-foreground flex gap-2">
                        <span className="text-primary font-bold">→</span> {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {Array.isArray(insights.strengths) && insights.strengths.length > 0 && (
                <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                  <h4 className="text-sm font-semibold mb-2 text-emerald-400">Strengths</h4>
                  <ul className="space-y-1">
                    {(insights.strengths as string[]).map((s, i) => (
                      <li key={i} className="text-sm text-muted-foreground">✅ {s}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Job Description Parser */}
      <Card className="glass-card border-0">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <span className="text-xl">📋</span>
            Job Description Parser
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleParseJob} className="space-y-4">
            <textarea
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
              rows={6}
              placeholder="Paste a job description here to extract structured data..."
              className="w-full px-4 py-3 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none placeholder:text-muted-foreground/60"
            />
            <Button type="submit" disabled={parseLoading || !jobText.trim()} className="bg-primary hover:bg-primary/90">
              {parseLoading ? "Parsing with AI..." : "Parse with AI"}
            </Button>
          </form>

          {/* Loader */}
          {parseLoading && (
            <div className="mt-6 p-6 rounded-lg bg-muted/30 border border-border/50 flex flex-col items-center justify-center space-y-2 animate-pulse">
              <div className="w-6 h-6 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              <p className="text-xs text-muted-foreground">Extracting job details using Gemini...</p>
            </div>
          )}

          {/* Error Alert */}
          {parseError && (
            <div className="mt-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs space-y-1">
              <p className="font-semibold">⚠️ AI Parsing Failed</p>
              <p className="text-muted-foreground leading-relaxed">{parseError}</p>
            </div>
          )}

          {jobResult && (
            <div className="mt-6 p-4 rounded-lg bg-muted/50 border border-border">
              <h4 className="text-sm font-semibold mb-3">Parsed Result</h4>
              <pre className="text-xs text-muted-foreground overflow-x-auto whitespace-pre-wrap font-mono leading-relaxed p-3.5 bg-background rounded-lg border border-border/80">
                {JSON.stringify(jobResult, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
