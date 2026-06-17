"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import ParkinsonDatasetPage from "@/app/datasets/parkinson/page";
import { useAuth } from "@/context/AuthContext";

export default function ReferencesPage() {
  const router = useRouter();
  const { ready, isAdmin } = useAuth();

  useEffect(() => {
    if (ready && !isAdmin()) {
      router.replace("/dashboard");
    }
  }, [ready, isAdmin, router]);

  if (!ready || !isAdmin()) return null;

  return <ParkinsonDatasetPage />;
}
