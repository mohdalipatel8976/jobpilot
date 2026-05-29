"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ensureSilentAuth } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();

  useEffect(() => {
    const performAutoLogin = async () => {
      await ensureSilentAuth();
      router.replace("/dashboard");
    };
    performAutoLogin();
  }, [router]);

  return (
    <main className="min-h-screen flex items-center justify-center bg-background p-4">
      {/* Background decoration */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-gradient-end/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md animate-slide-up flex flex-col items-center">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 mb-4">
            <svg className="w-7 h-7 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold gradient-text">JobPilot</h1>
          <p className="text-muted-foreground mt-1">Connecting your dashboard...</p>
        </div>

        {/* Loading Spinner */}
        <div className="flex items-center gap-3 bg-muted/50 border border-border px-6 py-3 rounded-full backdrop-blur-sm">
          <svg className="animate-spin h-5 w-5 text-primary" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          <span className="text-sm font-medium text-muted-foreground">Redirecting to Dashboard...</span>
        </div>
      </div>
    </main>
  );
}

