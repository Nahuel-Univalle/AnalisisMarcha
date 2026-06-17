-- CreateEnum
CREATE TYPE "AlertLevel" AS ENUM ('BAJO', 'MEDIO', 'ALTO');

-- CreateEnum
CREATE TYPE "VideoStatus" AS ENUM ('CARGADO', 'VALIDANDO', 'VALIDO', 'INVALIDO', 'PROCESANDO', 'FINALIZADO');

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "age" INTEGER,
    "email" TEXT NOT NULL,
    "passwordHash" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "VideoMarcha" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "originalName" TEXT NOT NULL,
    "storedName" TEXT,
    "url" TEXT,
    "mimeType" TEXT NOT NULL,
    "sizeBytes" INTEGER NOT NULL,
    "validationStatus" "VideoStatus" NOT NULL DEFAULT 'CARGADO',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "VideoMarcha_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PosePoint" (
    "id" TEXT NOT NULL,
    "videoId" TEXT NOT NULL,
    "frameNumber" INTEGER NOT NULL,
    "bodyPoint" TEXT NOT NULL,
    "x" DOUBLE PRECISION NOT NULL,
    "y" DOUBLE PRECISION NOT NULL,
    "z" DOUBLE PRECISION,

    CONSTRAINT "PosePoint_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "GaitAnalysis" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "videoId" TEXT NOT NULL,
    "alert" "AlertLevel" NOT NULL,
    "summary" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "GaitAnalysis_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "GaitParameter" (
    "id" TEXT NOT NULL,
    "analysisId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "value" TEXT NOT NULL,
    "state" TEXT NOT NULL,
    "description" TEXT,

    CONSTRAINT "GaitParameter_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DetectedSignal" (
    "id" TEXT NOT NULL,
    "analysisId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "relevance" "AlertLevel" NOT NULL,
    "description" TEXT NOT NULL,

    CONSTRAINT "DetectedSignal_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AssociatedCondition" (
    "id" TEXT NOT NULL,
    "analysisId" TEXT NOT NULL,
    "condition" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "description" TEXT NOT NULL,

    CONSTRAINT "AssociatedCondition_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MedicalReport" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "analysisId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "pdfUrl" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "MedicalReport_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SystemLog" (
    "id" TEXT NOT NULL,
    "userId" TEXT,
    "action" TEXT NOT NULL,
    "detail" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "SystemLog_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "MedicalReport_analysisId_key" ON "MedicalReport"("analysisId");

-- AddForeignKey
ALTER TABLE "VideoMarcha" ADD CONSTRAINT "VideoMarcha_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PosePoint" ADD CONSTRAINT "PosePoint_videoId_fkey" FOREIGN KEY ("videoId") REFERENCES "VideoMarcha"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GaitAnalysis" ADD CONSTRAINT "GaitAnalysis_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GaitAnalysis" ADD CONSTRAINT "GaitAnalysis_videoId_fkey" FOREIGN KEY ("videoId") REFERENCES "VideoMarcha"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GaitParameter" ADD CONSTRAINT "GaitParameter_analysisId_fkey" FOREIGN KEY ("analysisId") REFERENCES "GaitAnalysis"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DetectedSignal" ADD CONSTRAINT "DetectedSignal_analysisId_fkey" FOREIGN KEY ("analysisId") REFERENCES "GaitAnalysis"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AssociatedCondition" ADD CONSTRAINT "AssociatedCondition_analysisId_fkey" FOREIGN KEY ("analysisId") REFERENCES "GaitAnalysis"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MedicalReport" ADD CONSTRAINT "MedicalReport_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MedicalReport" ADD CONSTRAINT "MedicalReport_analysisId_fkey" FOREIGN KEY ("analysisId") REFERENCES "GaitAnalysis"("id") ON DELETE CASCADE ON UPDATE CASCADE;
