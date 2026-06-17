import { NextRequest } from "next/server";
import {
  getParkinsonDatasetRecords,
  getParkinsonDatasetSummary,
} from "@/lib/datasets/parkinsonDataset";
import { requireAdmin } from "@/lib/auth/guards";

export const runtime = "nodejs";

function parsePositiveInt(value: string | null) {
  if (!value) return undefined;
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export async function GET(request: NextRequest) {
  try {
    const result = await requireAdmin();

    if ("error" in result) return result.error;

    const searchParams = request.nextUrl.searchParams;
    const page = parsePositiveInt(searchParams.get("page"));
    const limit = parsePositiveInt(searchParams.get("limit"));
    const condition = searchParams.get("condition") || undefined;

    const [summaryData, recordsData] = await Promise.all([
      getParkinsonDatasetSummary(),
      getParkinsonDatasetRecords({ page, limit, condition }),
    ]);

    return Response.json({
      ...summaryData,
      ...recordsData,
    });
  } catch (error) {
    console.error(error);

    return Response.json(
      {
        summary: {
          totalRecords: 0,
          controlCount: 0,
          parkinsonCount: 0,
          averageAge: null,
          averageSpeed: null,
          averageAsymmetry: null,
          averageCadence: null,
          averageDoubleSupport: null,
        },
        warnings: [
          "No se pudo consultar la información de referencia. Intenta nuevamente más tarde.",
        ],
        records: [],
        pagination: {
          page: 1,
          limit: 20,
          totalRecords: 0,
          totalPages: 1,
        },
      },
      { status: 500 }
    );
  }
}
