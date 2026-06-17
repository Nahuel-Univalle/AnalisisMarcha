import { requireAdmin } from "@/lib/auth/guards";
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

  const reports = await prisma.medicalReport.findMany({
    orderBy: { createdAt: "desc" },
    include: {
      user: { select: { email: true, name: true } },
      analysis: {
        include: { video: true },
      },
    },
  });

  return Response.json({
    reports: reports.map((report) => ({
      id: report.id,
      title: report.title,
      summary: report.analysis.summary,
      date: report.createdAt.toISOString().split("T")[0],
      alertLevel: fromPrismaAlert(report.analysis.alert),
      analysisId: report.analysisId,
      userEmail: report.user.email,
      userName: report.user.name,
      videoRecordId: report.analysis.video.id,
      originalVideoUrl:
        report.analysis.video.originalVideoUrl ??
        report.analysis.video.localOriginalVideoUrl,
      processedVideoUrl:
        report.analysis.video.processedVideoUrl ??
        report.analysis.video.localProcessedVideoUrl,
      videoProvider: report.analysis.video.videoProvider,
    })),
  });
}
