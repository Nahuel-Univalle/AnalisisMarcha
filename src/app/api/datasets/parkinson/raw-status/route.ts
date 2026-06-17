import { prisma } from "@/lib/prisma";
import { requireAdmin } from "@/lib/auth/guards";

export const runtime = "nodejs";

export async function GET() {
  try {
    const result = await requireAdmin();

    if ("error" in result) return result.error;

    const [totalRawSamples, controlSamples, parkinsonSamples] =
      await Promise.all([
        prisma.parkinsonRawSample.count(),
        prisma.parkinsonRawSample.count({ where: { parkinsonBinary: 0 } }),
        prisma.parkinsonRawSample.count({ where: { parkinsonBinary: 1 } }),
      ]);

    const readyForTraining = controlSamples > 0 && parkinsonSamples > 0;

    return Response.json({
      totalRawSamples,
      controlSamples,
      parkinsonSamples,
      source: "postgresql",
      readyForTraining,
      message: readyForTraining
        ? "Los datos crudos están cargados y contienen más de una clase para preparar entrenamiento."
        : "Los datos crudos están cargados, pero todavía faltan registros Parkinson para entrenar un modelo confiable.",
    });
  } catch {
    return Response.json(
      {
        totalRawSamples: 0,
        controlSamples: 0,
        parkinsonSamples: 0,
        source: "postgresql",
        readyForTraining: false,
        message: "No se pudo consultar el estado de datos crudos.",
      },
      { status: 500 }
    );
  }
}
