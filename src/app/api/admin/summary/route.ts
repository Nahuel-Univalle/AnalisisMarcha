import { requireAdmin } from "@/lib/auth/guards";
import { getModelStatusDetails } from "@/lib/ml/modelMetrics";
import { prisma } from "@/lib/prisma";

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
    modelStatus,
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
      include: { user: { select: { email: true, name: true } } },
    }),
    prisma.medicalReport.findMany({
      orderBy: { createdAt: "desc" },
      take: 5,
      include: {
        user: { select: { email: true, name: true } },
        analysis: { select: { alert: true, summary: true } },
      },
    }),
    prisma.user.findMany({
      orderBy: { createdAt: "desc" },
      take: 5,
      select: { email: true, name: true, role: true, createdAt: true },
    }),
    getModelStatusDetails(),
  ]);

  return Response.json({
    totalUsers,
    totalAnalyses,
    totalReports,
    totalVideos,
    datasetSummary: {
      datasetRecords,
      rawSamples,
    },
    modelStatus: {
      available: modelStatus.modelAvailable,
      metricsAvailable: modelStatus.metricsAvailable,
      accuracy: modelStatus.accuracy,
      message: modelStatus.modelAvailable
        ? "Modelo disponible"
        : "Modelo no disponible",
    },
    recentAnalyses: recentAnalyses.map((analysis) => ({
      id: analysis.id,
      userEmail: analysis.user.email,
      userName: analysis.user.name,
      date: analysis.createdAt.toISOString().split("T")[0],
      alertLevel: fromPrismaAlert(analysis.alert),
      summary: analysis.summary,
    })),
    recentReports: recentReports.map((report) => ({
      id: report.id,
      userEmail: report.user.email,
      userName: report.user.name,
      title: report.title,
      date: report.createdAt.toISOString().split("T")[0],
      alertLevel: fromPrismaAlert(report.analysis.alert),
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
