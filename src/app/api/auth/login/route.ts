import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/prisma";
import { validateEmailFormat } from "@/lib/validations/auth";
import {
  SESSION_COOKIE,
  sessionCookieOptions,
  signSession,
} from "@/lib/auth/sessionToken";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const email = String(body.email || "").trim().toLowerCase();
    const password = String(body.password || "");

    const emailError = validateEmailFormat(email);

    if (emailError) {
      return NextResponse.json(
        {
          message: emailError,
          errors: {
            email: emailError,
          },
        },
        { status: 400 }
      );
    }

    if (!password) {
      return NextResponse.json(
        {
          message: "La contraseña es obligatoria.",
          errors: {
            password: "La contraseña es obligatoria.",
          },
        },
        { status: 400 }
      );
    }

    const user = await prisma.user.findUnique({
      where: { email },
    });

    if (!user) {
      return NextResponse.json(
        {
          message: "Correo o contraseña incorrectos.",
        },
        { status: 401 }
      );
    }

    const validPassword = await bcrypt.compare(password, user.passwordHash);

    if (!validPassword) {
      return NextResponse.json(
        {
          message: "Correo o contraseña incorrectos.",
        },
        { status: 401 }
      );
    }

    await prisma.systemLog.create({
      data: {
        userId: user.email,
        action: "LOGIN_USER",
        detail: "Inicio de sesión correcto.",
      },
    });

    const response = NextResponse.json({
      message: "Inicio de sesión correcto.",
      user: {
        name: user.name,
        age: user.age,
        email: user.email,
        role: user.role,
      },
    });

    response.cookies.set(
      SESSION_COOKIE,
      await signSession({ email: user.email, name: user.name, role: user.role }),
      sessionCookieOptions()
    );

    return response;
  } catch (error) {
    console.error("LOGIN_ERROR", error);

    return NextResponse.json(
      {
        message: "Error interno al iniciar sesión.",
      },
      { status: 500 }
    );
  }
}
