CREATE TABLE IF NOT EXISTS "ParkinsonRawSample" (
  "id" TEXT NOT NULL,
  "sourceFile" TEXT NOT NULL,
  "sourceDataset" TEXT,
  "subjectId" TEXT NOT NULL,
  "study" TEXT,
  "subjectType" TEXT,
  "subjectNumber" INTEGER,
  "condition" TEXT NOT NULL,
  "parkinsonBinary" INTEGER NOT NULL,
  "walkNumber" TEXT,
  "walkType" TEXT,
  "sampleIndex" INTEGER NOT NULL,
  "time" DOUBLE PRECISION,
  "left1" DOUBLE PRECISION,
  "left2" DOUBLE PRECISION,
  "left3" DOUBLE PRECISION,
  "left4" DOUBLE PRECISION,
  "left5" DOUBLE PRECISION,
  "left6" DOUBLE PRECISION,
  "left7" DOUBLE PRECISION,
  "left8" DOUBLE PRECISION,
  "right1" DOUBLE PRECISION,
  "right2" DOUBLE PRECISION,
  "right3" DOUBLE PRECISION,
  "right4" DOUBLE PRECISION,
  "right5" DOUBLE PRECISION,
  "right6" DOUBLE PRECISION,
  "right7" DOUBLE PRECISION,
  "right8" DOUBLE PRECISION,
  "leftTotal" DOUBLE PRECISION,
  "rightTotal" DOUBLE PRECISION,
  "totalForce" DOUBLE PRECISION,
  "forceDifference" DOUBLE PRECISION,
  "forceAsymmetryAbs" DOUBLE PRECISION,
  "forceAsymmetryIndex" DOUBLE PRECISION,
  "leftContact" BOOLEAN,
  "rightContact" BOOLEAN,
  "doubleSupport" BOOLEAN,
  "noSupport" BOOLEAN,
  "leftCopX" DOUBLE PRECISION,
  "leftCopY" DOUBLE PRECISION,
  "rightCopX" DOUBLE PRECISION,
  "rightCopY" DOUBLE PRECISION,
  "overallCopX" DOUBLE PRECISION,
  "overallCopY" DOUBLE PRECISION,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT "ParkinsonRawSample_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "ParkinsonRawSample_sourceFile_subjectId_walkNumber_sampleIndex_key"
  ON "ParkinsonRawSample"("sourceFile", "subjectId", "walkNumber", "sampleIndex");

CREATE INDEX IF NOT EXISTS "ParkinsonRawSample_sourceFile_idx"
  ON "ParkinsonRawSample"("sourceFile");

CREATE INDEX IF NOT EXISTS "ParkinsonRawSample_subjectId_idx"
  ON "ParkinsonRawSample"("subjectId");

CREATE INDEX IF NOT EXISTS "ParkinsonRawSample_condition_idx"
  ON "ParkinsonRawSample"("condition");

CREATE INDEX IF NOT EXISTS "ParkinsonRawSample_parkinsonBinary_idx"
  ON "ParkinsonRawSample"("parkinsonBinary");
