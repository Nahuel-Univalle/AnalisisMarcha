import { NextRequest, NextResponse } from "next/server";

type SessionUser = {
  email?: string;
  role?: string;
};

const protectedRoutes = [
  "/dashboard",
  "/analisis",
  "/seguimiento",
  "/informes",
  "/referencias",
  "/datasets",
  "/admin",
];
const authRoutes = ["/login", "/registro"];
const adminRoutes = ["/referencias", "/datasets", "/admin"];
const userOnlyRoutes = ["/analisis"];

function startsWithAny(pathname: string, routes: string[]) {
  return routes.some((route) => pathname === route || pathname.startsWith(`${route}/`));
}

function readSessionUser(request: NextRequest) {
  const rawUser = request.cookies.get("gait-user")?.value;

  if (!rawUser) return null;

  try {
    const user = JSON.parse(rawUser) as SessionUser;
    if (!user.email) return null;
    return {
      email: user.email,
      role: user.role === "ADMIN" ? "ADMIN" : "USER",
    };
  } catch {
    return null;
  }
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const user = readSessionUser(request);

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
    "/referencias/:path*",
    "/datasets/:path*",
    "/admin/:path*",
    "/login",
    "/registro",
  ],
};
