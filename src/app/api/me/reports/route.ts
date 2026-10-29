import { NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/guards";
import { prisma } from "@/lib/prisma";

export const runtime = "nodejs";

function fromPrismaAlert(alert: "BAJO" | "MEDIO" | "ALTO") {
  if (alert === "ALTO") return "Alto";
  if (alert === "MEDIO") return "Medio";
  return "Bajo";
}

function reportPayload(report: {
  id: string;
  title: string;
  createdAt: Date;
  analysisId: string;
  analysis: {
    alert: "BAJO" | "MEDIO" | "ALTO";
    summary: string;
    conditions: { condition: string; status: string }[];
    video: {
      originalVideoUrl: string | null;
      processedVideoUrl: string | null;
      localOriginalVideoUrl: string | null;
      localProcessedVideoUrl: string | null;
      videoProvider: string;
      id: string;
    };
  };
}) {
  const primaryCondition = report.analysis.conditions[0] ?? null;
  return {
    id: report.id,
    title: report.title,
    summary: report.analysis.summary,
    analysisType: "Análisis de marcha",
    pattern: primaryCondition?.condition ?? null,
    patternStatus: primaryCondition?.status ?? null,
    date: report.createdAt.toISOString().split("T")[0],
    alertLevel: fromPrismaAlert(report.analysis.alert),
    analysisId: report.analysisId,
    videoRecordId: report.analysis.video.id,
    originalVideoUrl: report.analysis.video.originalVideoUrl ?? undefined,
    processedVideoUrl: report.analysis.video.processedVideoUrl ?? undefined,
    localOriginalVideoUrl: report.analysis.video.localOriginalVideoUrl,
    localProcessedVideoUrl: report.analysis.video.localProcessedVideoUrl,
    videoProvider: report.analysis.video.videoProvider,
  };
}

export async function GET() {
  const result = await requireUser();
  if ("error" in result) return result.error;
  const { user } = result;

  const reports = await prisma.medicalReport.findMany({
    where: { userId: user.id },
    orderBy: { createdAt: "desc" },
    include: {
      analysis: {
        include: {
          video: true,
          conditions: true,
        },
      },
    },
  });

  return NextResponse.json({
    reports: reports.map(reportPayload),
  });
}

export async function POST(request: Request) {
  const result = await requireUser();
  if ("error" in result) return result.error;
  const { user } = result;

  const body = await request.json();
  const analysisId = String(body.analysisId || "");
  const title = String(body.title || "Informe de análisis de marcha").trim();

  if (!analysisId) {
    return NextResponse.json(
      { message: "No hay análisis para guardar como informe." },
      { status: 400 }
    );
  }

  const analysis = await prisma.gaitAnalysis.findFirst({
    where: {
      id: analysisId,
      userId: user.id,
    },
  });

  if (!analysis) {
    return NextResponse.json(
      { message: "El análisis no pertenece al usuario autenticado." },
      { status: 403 }
    );
  }

  const report = await prisma.medicalReport.upsert({
    where: { analysisId },
    update: { title },
    create: {
      userId: user.id,
      analysisId,
      title,
    },
    include: {
      analysis: {
        include: {
          video: true,
          conditions: true,
        },
      },
    },
  });

  return NextResponse.json({ report: reportPayload(report) }, { status: 201 });
}
