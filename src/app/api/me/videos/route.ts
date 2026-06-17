import { requireUser } from "@/lib/auth/guards";
import { prisma } from "@/lib/prisma";

export const runtime = "nodejs";

export async function GET() {
  const result = await requireUser();
  if ("error" in result) return result.error;
  const { user } = result;

  const videos = await prisma.videoMarcha.findMany({
    where: { userId: user.id },
    orderBy: { createdAt: "desc" },
    include: {
      analyses: {
        select: { id: true, alert: true, createdAt: true },
      },
    },
  });

  return Response.json({
    videos: videos.map((video) => ({
      id: video.id,
      name: video.originalName,
      mimeType: video.mimeType,
      sizeBytes: video.sizeBytes,
      status: video.validationStatus,
      createdAt: video.createdAt,
      originalVideoUrl: video.originalVideoUrl ?? video.localOriginalVideoUrl,
      processedVideoUrl: video.processedVideoUrl ?? video.localProcessedVideoUrl,
      analyses: video.analyses,
    })),
  });
}
