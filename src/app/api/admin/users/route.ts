import { requireAdmin } from "@/lib/auth/guards";
import { prisma } from "@/lib/prisma";

export const runtime = "nodejs";

export async function GET() {
  const result = await requireAdmin();
  if ("error" in result) return result.error;

  const users = await prisma.user.findMany({
    orderBy: { createdAt: "desc" },
    select: {
      id: true,
      email: true,
      name: true,
      role: true,
      createdAt: true,
      _count: {
        select: {
          analyses: true,
          reports: true,
          videos: true,
        },
      },
    },
  });

  return Response.json({
    users: users.map((user) => ({
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      date: user.createdAt.toISOString().split("T")[0],
      totalAnalyses: user._count.analyses,
      totalReports: user._count.reports,
      totalVideos: user._count.videos,
    })),
  });
}
