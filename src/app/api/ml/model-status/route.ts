import { prisma } from "@/lib/prisma";
import { requireAdmin } from "@/lib/auth/guards";
import { getModelStatusDetails } from "@/lib/ml/modelMetrics";

export const runtime = "nodejs";

export async function GET() {
  try {
    const result = await requireAdmin();

    if ("error" in result) return result.error;

    const [controlRecords, parkinsonRecords, rawSamples, modelStatus] =
      await Promise.all([
        prisma.parkinsonDatasetRecord.count({ where: { parkinsonBinary: 0 } }),
        prisma.parkinsonDatasetRecord.count({ where: { parkinsonBinary: 1 } }),
        prisma.parkinsonRawSample.count(),
        getModelStatusDetails(),
      ]);
    const trainingReady = controlRecords > 0 && parkinsonRecords > 0;

    return Response.json({
      modelAvailable: modelStatus.modelAvailable,
      trainingReady,
      metricsAvailable: modelStatus.metricsAvailable,
      accuracy: modelStatus.accuracy,
      precision: modelStatus.precision,
      recall: modelStatus.recall,
      f1Score: modelStatus.f1Score,
      confusionMatrix: modelStatus.confusionMatrix ?? null,
      samples: modelStatus.samples,
      controlSamples: modelStatus.controlSamples,
      parkinsonSamples: modelStatus.parkinsonSamples,
      validationMethod: modelStatus.validationMethod,
      trainSize: modelStatus.trainSize,
      testSize: modelStatus.testSize,
      controlTrain: modelStatus.controlTrain,
      parkinsonTrain: modelStatus.parkinsonTrain,
      controlTest: modelStatus.controlTest,
      parkinsonTest: modelStatus.parkinsonTest,
      warning: modelStatus.warning,
      controlRecords,
      parkinsonRecords,
      rawSamples,
      status: modelStatus.modelAvailable
        ? "modelo inicial / pendiente de validación"
        : "pendiente de entrenamiento",
      message: modelStatus.modelAvailable
        ? modelStatus.metricsAvailable
          ? "Modelo inicial entrenado con datos de referencia."
          : "El modelo aún no tiene métricas de entrenamiento disponibles."
        : "Aún no existe modelo entrenado disponible.",
    });
  } catch {
    return Response.json(
      {
        modelAvailable: false,
        trainingReady: false,
        metricsAvailable: false,
        accuracy: null,
        precision: null,
        recall: null,
        f1Score: null,
        confusionMatrix: null,
        samples: null,
        controlSamples: null,
        parkinsonSamples: null,
        validationMethod: null,
        trainSize: null,
        testSize: null,
        controlTrain: null,
        parkinsonTrain: null,
        controlTest: null,
        parkinsonTest: null,
        warning: null,
        controlRecords: 0,
        parkinsonRecords: 0,
        rawSamples: 0,
        status: "no disponible",
        message: "No se pudo consultar el estado del entrenamiento.",
      },
      { status: 500 }
    );
  }
}
