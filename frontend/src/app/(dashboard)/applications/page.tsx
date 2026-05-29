"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { applicationsApi } from "@/lib/api";
import { formatDate, getStatusColor, getPriorityColor } from "@/lib/utils";
import type { Application, ApplicationListResponse } from "@/types";

export default function ApplicationsPage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // Create form state
  const [newApp, setNewApp] = useState({
    company_name: "",
    job_title: "",
    job_url: "",
    source: "",
    location: "",
    work_type: "",
    priority: "medium",
    status: "draft",
    notes: "",
  });

  const fetchApps = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { page: String(page), page_size: "15" };
      if (statusFilter !== "all") params.status = statusFilter;
      if (searchQuery) params.search = searchQuery;
      const data = (await applicationsApi.list(params)) as ApplicationListResponse;
      setApps(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApps();
  }, [page, statusFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchApps();
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await applicationsApi.create(newApp);
      setShowCreateDialog(false);
      setNewApp({ company_name: "", job_title: "", job_url: "", source: "", location: "", work_type: "", priority: "medium", status: "draft", notes: "" });
      fetchApps();
    } catch (e) {
      console.error(e);
    }
  };

  const handleStatusChange = async (id: string, newStatus: string) => {
    try {
      await applicationsApi.updateStatus(id, newStatus);
      fetchApps();
    } catch (e) {
      console.error(e);
    }
  };

  const statuses = ["all", "draft", "applied", "screening", "interview", "assessment", "offer", "rejected", "withdrawn", "accepted"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Applications</h1>
          <p className="text-muted-foreground text-sm">{total} total applications</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger
            render={
              <Button className="bg-primary hover:bg-primary/90">
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Application
              </Button>
            }
          />
          <DialogContent className="glass-card border-border max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>New Application</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground mb-1 block">Company *</label>
                  <input value={newApp.company_name} onChange={(e) => setNewApp({ ...newApp, company_name: e.target.value })} className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50" required />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground mb-1 block">Job Title *</label>
                  <input value={newApp.job_title} onChange={(e) => setNewApp({ ...newApp, job_title: e.target.value })} className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50" required />
                </div>
              </div>
              <div>
                <label className="text-sm text-muted-foreground mb-1 block">Job URL</label>
                <input value={newApp.job_url} onChange={(e) => setNewApp({ ...newApp, job_url: e.target.value })} className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground mb-1 block">Source</label>
                  <input value={newApp.source} onChange={(e) => setNewApp({ ...newApp, source: e.target.value })} placeholder="LinkedIn, Indeed..." className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50" />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground mb-1 block">Location</label>
                  <input value={newApp.location} onChange={(e) => setNewApp({ ...newApp, location: e.target.value })} className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground mb-1 block">Priority</label>
                  <select value={newApp.priority} onChange={(e) => setNewApp({ ...newApp, priority: e.target.value })} className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50">
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-muted-foreground mb-1 block">Work Type</label>
                  <select value={newApp.work_type} onChange={(e) => setNewApp({ ...newApp, work_type: e.target.value })} className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50">
                    <option value="">Select...</option>
                    <option value="remote">Remote</option>
                    <option value="hybrid">Hybrid</option>
                    <option value="onsite">Onsite</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-sm text-muted-foreground mb-1 block">Notes</label>
                <textarea value={newApp.notes} onChange={(e) => setNewApp({ ...newApp, notes: e.target.value })} rows={3} className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none" />
              </div>
              <Button type="submit" className="w-full bg-primary hover:bg-primary/90">Create Application</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <form onSubmit={handleSearch} className="flex-1">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by company, title, or location..."
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        </form>
        <div className="flex gap-2 flex-wrap">
          {statuses.map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                statusFilter === s
                  ? "bg-primary/20 text-primary border border-primary/30"
                  : "bg-muted text-muted-foreground border border-border hover:border-border/80"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Applications List */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton h-20 rounded-xl" />
          ))}
        </div>
      ) : apps.length > 0 ? (
        <div className="space-y-3">
          {apps.map((app) => (
            <Card key={app.id} className="glass-card border-0 hover:border-primary/20 transition-all group">
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center shrink-0 text-primary font-bold text-lg group-hover:bg-primary/20 transition-colors">
                    {app.company_name[0]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <h3 className="font-semibold truncate">{app.company_name}</h3>
                      {app.priority === "high" && (
                        <Badge variant="outline" className={getPriorityColor(app.priority) + " text-[10px]"}>
                          High
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground truncate">{app.job_title}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      {app.location && <span>📍 {app.location}</span>}
                      {app.work_type && <span className="capitalize">🏢 {app.work_type}</span>}
                      {app.employment_type && <span className="capitalize">⌛ {app.employment_type}</span>}
                      {app.seniority_level && <span className="capitalize">🎓 {app.seniority_level}</span>}
                      {app.experience_years && <span>🎯 {app.experience_years}</span>}
                      {app.source && <span>🔗 {app.source}</span>}
                      {app.applied_date && <span>📅 {formatDate(app.applied_date)}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select value={app.status} onValueChange={(v) => { if (app.id && v) handleStatusChange(app.id, v); }}>
                      <SelectTrigger className={`w-32 h-8 text-xs ${getStatusColor(app.status)} border`}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {statuses.filter((s) => s !== "all").map((s) => (
                          <SelectItem key={s} value={s} className="text-xs capitalize">{s}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="glass-card border-0">
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No applications found. Add your first one!</p>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Previous
          </Button>
          <span className="flex items-center text-sm text-muted-foreground px-4">
            Page {page} of {totalPages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
