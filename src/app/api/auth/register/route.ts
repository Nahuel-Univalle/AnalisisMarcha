import { randomUUID } from "node:crypto";
import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/prisma";
import { validateRegisterInput } from "@/lib/validations/auth";
import { validateEmailDomain } from "@/lib/validations/emailServer";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const name = String(body.name || "").trim().replace(/\s+/g, " ");
    const email = String(body.email || "").trim().toLowerCase();
    const password = String(body.password || "");
    const confirmPassword = String(body.confirmPassword || "");
    const age = body.age ? Number(body.age) : null;
    const accepted = Boolean(body.accepted);

    const validation = validateRegisterInput({
      name,
      age,
      email,
      password,
      confirmPassword,
      accepted,
    });

    if (!validation.valid) {
      return NextResponse.json(
        {
          message: "Existen errores en el formulario.",
          errors: validation.errors,
        },
        { status: 400 }
      );
    }

    const emailDomainError = await validateEmailDomain(email);

    if (emailDomainError) {
      return NextResponse.json(
        {
          message: emailDomainError,
          errors: {
            email: emailDomainError,
          },
        },
        { status: 400 }
      );
    }

    const existingUser = await prisma.user.findUnique({
      where: { email },
    });

    if (existingUser) {
      return NextResponse.json(
        {
          message: "Ya existe una cuenta registrada con este correo electrónico.",
          errors: {
            email: "Este correo ya está registrado.",
          },
        },
        { status: 409 }
      );
    }

    const passwordHash = await bcrypt.hash(password, 10);

    const [user] = await prisma.$queryRawUnsafe<
      Array<{
        name: string;
        age: number | null;
        email: string;
        role: "USER" | "ADMIN";
        createdAt: Date;
      }>
    >(
      `
        INSERT INTO "User" ("id", "name", "age", "email", "passwordHash", "role")
        VALUES ($1, $2, $3, $4, $5, 'USER')
        RETURNING "name", "age", "email", "role"::text AS "role", "createdAt"
      `,
      randomUUID(),
      name,
      age,
      email,
      passwordHash
    );

    await prisma.systemLog.create({
      data: {
        userId: user.email,
        action: "REGISTER_USER",
        detail: "Usuario registrado correctamente.",
      },
    });

    return NextResponse.json(
      {
        message: "Cuenta creada correctamente.",
        user,
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("REGISTER_ERROR", error);

    return NextResponse.json(
      {
        message: "Error interno al crear la cuenta.",
      },
      { status: 500 }
    );
  }
}
