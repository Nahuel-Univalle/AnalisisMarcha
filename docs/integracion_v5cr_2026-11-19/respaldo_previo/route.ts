import { requireAdmin } from "@/lib/auth/guards";
import { EXPERIMENTAL_V4_OOF_METRICS, hasExperimentalV4Model } from "@/lib/ml/modelMetrics";
import { prisma } from "@/lib/prisma";
import { storedPatternOf } from "@/lib/analysis/conditionLabels";

export const runtime = "nodejs";

function fromPrismaAlert(alert: "BAJO" | "MEDIO" | "ALTO") {
  if (alert === "ALTO") return "Alto";
  if (alert === "MEDIO") return "Medio";
  return "Bajo";
}

export async function GET() {
  const result = await requireAdmin();
  if ("error" in result) return result.error;

  const [
    totalUsers,
    totalAnalyses,
    totalReports,
    totalVideos,
    storedPatterns,
    recentAnalyses,
    recentReports,
    recentUsers,
  ] = await Promise.all([
    prisma.user.count(),
    prisma.gaitAnalysis.count(),
    prisma.medicalReport.count(),
    prisma.videoMarcha.count(),
    prisma.gaitAnalysis.findMany({
      select: {
        summary: true,
        conditions: { select: { condition: true } },
        parameters: { select: { name: true, value: true, state: true } },
      },
    }),
    prisma.gaitAnalysis.findMany({
      orderBy: { createdAt: "desc" },
      take: 5,
      include: {
        user: { select: { email: true, name: true } },
        conditions: true,
        parameters: true,
      },
    }),
    prisma.medicalReport.findMany({
      orderBy: { createdAt: "desc" },
      take: 5,
      include: {
        user: { select: { email: true, name: true } },
        analysis: {
          select: { alert: true, summary: true, conditions: true, parameters: true },
        },
      },
    }),
    prisma.user.findMany({
      orderBy: { createdAt: "desc" },
      take: 5,
      select: { email: true, name: true, role: true, createdAt: true },
    }),
  ]);

  const experimentalModelAvailable = hasExperimentalV4Model();

  // Resultados guardados por patrón; "sin_clasificar" si el registro no permite saberlo.
  const patternCounts: Record<string, number> = {};
  for (const analysis of storedPatterns) {
    const key = storedPatternOf(analysis).pattern ?? "sin_clasificar";
    patternCounts[key] = (patternCounts[key] ?? 0) + 1;
  }

  return Response.json({
    totalUsers,
    totalAnalyses,
    totalReports,
    totalVideos,
    patternCounts,
    // Estado y métricas OOF del modelo que usa producción (V4, 4 clases).
    modelStatus: {
      available: experimentalModelAvailable,
      accuracy: EXPERIMENTAL_V4_OOF_METRICS.accuracy,
      macroF1: EXPERIMENTAL_V4_OOF_METRICS.macroF1,
      modelVersion: EXPERIMENTAL_V4_OOF_METRICS.modelVersion,
      trainingVideos: EXPERIMENTAL_V4_OOF_METRICS.trainingVideos,
      trainingSubjects: EXPERIMENTAL_V4_OOF_METRICS.trainingSubjects,
      message: experimentalModelAvailable
        ? "Modelo experimental de 4 clases disponible"
        : "Modelo experimental de 4 clases no disponible",
    },
    recentAnalyses: recentAnalyses.map((analysis) => ({
      id: analysis.id,
      userEmail: analysis.user.email,
      userName: analysis.user.name,
      date: analysis.createdAt.toISOString().split("T")[0],
      alertLevel: fromPrismaAlert(analysis.alert),
      ...storedPatternOf(analysis),
      summary: analysis.summary,
    })),
    recentReports: recentReports.map((report) => ({
      id: report.id,
      userEmail: report.user.email,
      userName: report.user.name,
      title: report.title,
      date: report.createdAt.toISOString().split("T")[0],
      alertLevel: fromPrismaAlert(report.analysis.alert),
      ...storedPatternOf(report.analysis),
      summary: report.analysis.summary,
    })),
    recentUsers: recentUsers.map((user) => ({
      email: user.email,
      name: user.name,
      role: user.role,
      date: user.createdAt.toISOString().split("T")[0],
    })),
  });
}
