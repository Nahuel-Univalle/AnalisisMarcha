import { NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/guards";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const result = await requireUser();

  if ("error" in result) {
    return NextResponse.json({ message: "No autenticado." }, { status: 401 });
  }

  const user = await prisma.user.findUnique({
    where: { email: result.user.email },
    select: { name: true, age: true, email: true, role: true },
  });

  if (!user) {
    return NextResponse.json({ message: "No autenticado." }, { status: 401 });
  }

  return NextResponse.json({ user });
}
