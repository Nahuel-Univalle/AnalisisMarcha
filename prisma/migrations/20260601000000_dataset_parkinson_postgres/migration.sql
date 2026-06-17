-- CreateTable
CREATE TABLE "ParkinsonDatasetRecord" (
    "id" TEXT NOT NULL,
    "sourceFile" TEXT NOT NULL,
    "subjectId" TEXT NOT NULL,
    "study" TEXT,
    "subjectType" TEXT,
    "condition" TEXT NOT NULL,
    "parkinsonBinary" INTEGER NOT NULL,
    "walkNumber" TEXT,
    "walkType" TEXT,
    "genderCode" INTEGER,
    "age" DOUBLE PRECISION,
    "heightM" DOUBLE PRECISION,
    "weightKg" DOUBLE PRECISION,
    "hoehnYahr" DOUBLE PRECISION,
    "updrs" DOUBLE PRECISION,
    "updrsm" DOUBLE PRECISION,
    "tuag" DOUBLE PRECISION,
    "recordedSpeed" DOUBLE PRECISION,
    "meanLeftTotal" DOUBLE PRECISION,
    "stdLeftTotal" DOUBLE PRECISION,
    "meanRightTotal" DOUBLE PRECISION,
    "stdRightTotal" DOUBLE PRECISION,
    "meanTotalForce" DOUBLE PRECISION,
    "meanForceAsymmetryAbs" DOUBLE PRECISION,
    "meanForceAsymmetryIndex" DOUBLE PRECISION,
    "leftContactRatio" DOUBLE PRECISION,
    "rightContactRatio" DOUBLE PRECISION,
    "doubleSupportRatio" DOUBLE PRECISION,
    "leftStepEvents" INTEGER,
    "rightStepEvents" INTEGER,
    "estimatedCadence" DOUBLE PRECISION,
    "meanLeftStanceTimeSec" DOUBLE PRECISION,
    "meanRightStanceTimeSec" DOUBLE PRECISION,
    "meanLeftSwingTimeSec" DOUBLE PRECISION,
    "meanRightSwingTimeSec" DOUBLE PRECISION,
    "stdLeftCopX" DOUBLE PRECISION,
    "stdLeftCopY" DOUBLE PRECISION,
    "stdRightCopX" DOUBLE PRECISION,
    "stdRightCopY" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ParkinsonDatasetRecord_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DatasetImportLog" (
    "id" TEXT NOT NULL,
    "datasetName" TEXT NOT NULL,
    "filePath" TEXT NOT NULL,
    "rowsImported" INTEGER NOT NULL,
    "rowsSkipped" INTEGER NOT NULL DEFAULT 0,
    "status" TEXT NOT NULL,
    "message" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "DatasetImportLog_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "ParkinsonDatasetRecord_sourceFile_subjectId_walkNumber_key" ON "ParkinsonDatasetRecord"("sourceFile", "subjectId", "walkNumber");

-- CreateIndex
CREATE INDEX "ParkinsonDatasetRecord_condition_idx" ON "ParkinsonDatasetRecord"("condition");

-- CreateIndex
CREATE INDEX "ParkinsonDatasetRecord_parkinsonBinary_idx" ON "ParkinsonDatasetRecord"("parkinsonBinary");

-- CreateIndex
CREATE INDEX "ParkinsonDatasetRecord_subjectId_idx" ON "ParkinsonDatasetRecord"("subjectId");
