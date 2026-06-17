import { AnalysisResult, SavedReport } from "@/types";

export const mockAnalysisResult: AnalysisResult = {
  alertLevel: "Bajo",
  title: "Resultado orientativo sin alerta principal",
  summary:
    "No se detectaron señales relevantes en este análisis inicial. Cargue un video para obtener una evaluación orientativa.",
  signalEmptyMessage: "No se detectaron señales relevantes en este análisis.",
  signals: [],
  parameters: [
    {
      name: "Cuerpo detectado en el video",
      value: "Sin dato",
      state: "Seguimiento visual del cuerpo durante el video",
    },
    {
      name: "Momentos analizados",
      value: "0",
      state: "0 momentos con seguimiento correcto",
    },
    {
      name: "Velocidad de marcha",
      value: "Sin dato",
      state: "Medición orientativa del desplazamiento observado",
    },
    {
      name: "Asimetría",
      value: "Sin dato",
      state: "Diferencia lateral observada",
    },
    {
      name: "Ritmo de la marcha",
      value: "Sin dato",
      state: "Medición usada solo como apoyo si el movimiento fue estable",
    },
  ],
  conditions: [
    {
      condition: "Sin alerta principal asociada a Parkinson",
      status: "Sin alerta principal",
      description:
        "Cargue un video para obtener un análisis asistido por IA. El sistema no emite diagnósticos definitivos.",
    },
  ],
  recommendations: [
    "Revisar el resultado con un profesional de salud.",
    "No tomar decisiones médicas solo con este informe.",
    "Repetir el análisis si el video no fue claro.",
  ],
  datasetWarnings: [
    "El análisis se basa en patrones de referencia disponibles. Para una valoración más precisa, el resultado debe ser revisado por un profesional de salud.",
  ],
};

export const mockReports: SavedReport[] = [
  {
    id: "1",
    date: "2026-05-20",
    alertLevel: "Medio",
    title: "Informe de análisis de marcha",
  },
  {
    id: "2",
    date: "2026-05-10",
    alertLevel: "Bajo",
    title: "Informe de control de marcha",
  },
];
