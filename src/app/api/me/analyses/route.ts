import { requireUser } from "@/lib/auth/guards";
import { prisma } from "@/lib/prisma";
import { storedPatternOf } from "@/lib/analysis/conditionLabels";

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

  const analyses = await prisma.gaitAnalysis.findMany({
    where: { userId: user.id },
    orderBy: { createdAt: "desc" },
    include: {
      video: true,
      report: true,
      signals: true,
      parameters: true,
      conditions: true,
    },
  });

  return Response.json({
    analyses: analyses.map((analysis) => ({
      id: analysis.id,
      date: analysis.createdAt.toISOString().split("T")[0],
      alertLevel: fromPrismaAlert(analysis.alert),
      ...storedPatternOf(analysis),
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
      signals: analysis.signals,
      parameters: analysis.parameters,
      conditions: analysis.conditions,
    })),
  });
}
