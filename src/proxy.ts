import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE, verifySession } from "@/lib/auth/sessionToken";

const protectedRoutes = [
  "/dashboard",
  "/analisis",
  "/seguimiento",
  "/informes",
  "/admin",
];
const authRoutes = ["/login", "/registro"];
const adminRoutes = ["/admin"];
const userOnlyRoutes = ["/analisis"];

function startsWithAny(pathname: string, routes: string[]) {
  return routes.some((route) => pathname === route || pathname.startsWith(`${route}/`));
}

async function readSessionUser(request: NextRequest) {
  const session = await verifySession(request.cookies.get(SESSION_COOKIE)?.value);

  if (!session) return null;

  return { email: session.email, role: session.role };
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const user = await readSessionUser(request);

  if (startsWithAny(pathname, authRoutes) && user) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  if (startsWithAny(pathname, protectedRoutes) && !user) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (user?.role !== "ADMIN" && startsWithAny(pathname, adminRoutes)) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  if (user?.role === "ADMIN" && startsWithAny(pathname, userOnlyRoutes)) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/analisis/:path*",
    "/seguimiento/:path*",
    "/informes/:path*",
    "/admin/:path*",
    "/login",
    "/registro",
  ],
};
