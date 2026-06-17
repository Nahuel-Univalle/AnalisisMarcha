import { NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/guards";
import { prisma } from "@/lib/prisma";

export const runtime = "nodejs";

function fromPrismaAlert(alert: "BAJO" | "MEDIO" | "ALTO") {
  if (alert === "ALTO") return "Alto";
  if (alert === "MEDIO") return "Medio";
  return "Bajo";
}

export async function GET() {
  const result = await requireUser();
  if ("error" in result) return result.error;
  const { user } = result;

  const [analysisCount, reportCount, latestAnalysis, recentAnalyses] = await Promise.all([
    prisma.gaitAnalysis.count({ where: { userId: user.id } }),
    prisma.medicalReport.count({ where: { userId: user.id } }),
    prisma.gaitAnalysis.findFirst({
      where: { userId: user.id },
      orderBy: { createdAt: "desc" },
      select: { alert: true, createdAt: true },
    }),
    prisma.gaitAnalysis.findMany({
      where: { userId: user.id },
      orderBy: { createdAt: "desc" },
      take: 5,
      select: {
        id: true,
        alert: true,
        summary: true,
        createdAt: true,
        video: {
          select: {
            originalName: true,
            originalVideoUrl: true,
            localOriginalVideoUrl: true,
          },
        },
      },
    }),
  ]);

  return NextResponse.json({
    totalAnalyses: analysisCount,
    totalReports: reportCount,
    lastAlertLevel: latestAnalysis ? fromPrismaAlert(latestAnalysis.alert) : "Sin datos",
    privacyStatus: "Activa",
    recentAnalyses: recentAnalyses.map((analysis) => ({
      id: analysis.id,
      alertLevel: fromPrismaAlert(analysis.alert),
      summary: analysis.summary,
      date: analysis.createdAt.toISOString().split("T")[0],
      videoName: analysis.video.originalName,
      originalVideoUrl:
        analysis.video.originalVideoUrl ?? analysis.video.localOriginalVideoUrl,
    })),
    analysisCount,
    reportCount,
    latestAlert: latestAnalysis ? fromPrismaAlert(latestAnalysis.alert) : "Sin datos",
    latestAnalysisDate: latestAnalysis?.createdAt ?? null,
  });
}
