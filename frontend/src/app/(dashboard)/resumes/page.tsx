"use client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ResumesPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Resumes</h1>
          <p className="text-muted-foreground text-sm">Manage and track your resume versions</p>
        </div>
      </div>

      {/* Upload Zone */}
      <Card className="glass-card border-0 border-dashed border-2 border-border hover:border-primary/30 transition-colors cursor-pointer">
        <CardContent className="py-12 flex flex-col items-center gap-3">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
            <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium">Drop your resume here or click to upload</p>
            <p className="text-xs text-muted-foreground mt-1">PDF or DOCX · Max 10MB</p>
          </div>
        </CardContent>
      </Card>

      <Card className="glass-card border-0">
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">No resumes uploaded yet. Upload your first resume to start tracking.</p>
        </CardContent>
      </Card>
    </div>
  );
}
