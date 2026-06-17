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

  const analyses = await prisma.gaitAnalysis.findMany({
    orderBy: { createdAt: "desc" },
    include: {
      user: { select: { email: true, name: true } },
      video: true,
      report: true,
    },
  });

  return Response.json({
    analyses: analyses.map((analysis) => ({
      id: analysis.id,
      userId: analysis.userId,
      userEmail: analysis.user.email,
      userName: analysis.user.name,
      date: analysis.createdAt.toISOString().split("T")[0],
      alertLevel: fromPrismaAlert(analysis.alert),
      summary: analysis.summary,
      reportId: analysis.report?.id ?? null,
      video: {
        id: analysis.video.id,
        name: analysis.video.originalName,
        originalVideoUrl:
          analysis.video.originalVideoUrl ?? analysis.video.localOriginalVideoUrl,
        processedVideoUrl:
          analysis.video.processedVideoUrl ?? analysis.video.localProcessedVideoUrl,
      },
    })),
  });
}
