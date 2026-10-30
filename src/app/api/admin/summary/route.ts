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
    datasetRecords,
    rawSamples,
    recentAnalyses,
    recentReports,
    recentUsers,
  ] = await Promise.all([
    prisma.user.count(),
    prisma.gaitAnalysis.count(),
    prisma.medicalReport.count(),
    prisma.videoMarcha.count(),
    prisma.parkinsonDatasetRecord.count(),
    prisma.parkinsonRawSample.count(),
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

  return Response.json({
    totalUsers,
    totalAnalyses,
    totalReports,
    totalVideos,
    datasetSummary: {
      datasetRecords,
      rawSamples,
    },
    // Estado y métricas OOF del modelo que usa producción (V4, 4 clases), no de
    // los modelos históricos que lee getModelStatusDetails().
    modelStatus: {
      available: experimentalModelAvailable,
      metricsAvailable: experimentalModelAvailable,
      accuracy: EXPERIMENTAL_V4_OOF_METRICS.accuracy,
      macroF1: EXPERIMENTAL_V4_OOF_METRICS.macroF1,
      modelVersion: EXPERIMENTAL_V4_OOF_METRICS.modelVersion,
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
