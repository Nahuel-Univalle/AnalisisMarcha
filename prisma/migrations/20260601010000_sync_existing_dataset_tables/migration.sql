-- Synchronize dataset tables that already existed in the Docker database.
ALTER TABLE "DatasetImportLog"
ADD COLUMN IF NOT EXISTS "rowsSkipped" INTEGER NOT NULL DEFAULT 0;

ALTER TABLE "ParkinsonDatasetRecord"
ADD COLUMN IF NOT EXISTS "stdLeftTotal" DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS "stdRightTotal" DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS "leftStepEvents" INTEGER,
ADD COLUMN IF NOT EXISTS "rightStepEvents" INTEGER;

CREATE INDEX IF NOT EXISTS "ParkinsonDatasetRecord_condition_idx"
ON "ParkinsonDatasetRecord"("condition");

CREATE INDEX IF NOT EXISTS "ParkinsonDatasetRecord_parkinsonBinary_idx"
ON "ParkinsonDatasetRecord"("parkinsonBinary");

CREATE INDEX IF NOT EXISTS "ParkinsonDatasetRecord_subjectId_idx"
ON "ParkinsonDatasetRecord"("subjectId");
