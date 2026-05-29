"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ensureSilentAuth } from "@/lib/api";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const init = async () => {
      await ensureSilentAuth();
      router.replace("/dashboard");
    };
    init();
  }, [router]);

  return (
    <main className="min-h-screen flex items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <div className="h-12 w-12 rounded-xl bg-primary/20 animate-pulse-glow flex items-center justify-center">
          <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <p className="text-muted-foreground text-sm">Loading JobPilot...</p>
      </div>
    </main>
  );
}
