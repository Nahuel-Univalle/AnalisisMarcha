ALTER TABLE "VideoMarcha"
  ADD COLUMN IF NOT EXISTS "originalVideoUrl" TEXT,
  ADD COLUMN IF NOT EXISTS "originalVideoPublicId" TEXT,
  ADD COLUMN IF NOT EXISTS "processedVideoUrl" TEXT,
  ADD COLUMN IF NOT EXISTS "processedVideoPublicId" TEXT,
  ADD COLUMN IF NOT EXISTS "videoProvider" TEXT NOT NULL DEFAULT 'local',
  ADD COLUMN IF NOT EXISTS "originalFileName" TEXT,
  ADD COLUMN IF NOT EXISTS "processedFileName" TEXT,
  ADD COLUMN IF NOT EXISTS "cloudinaryOriginalBytes" INTEGER,
  ADD COLUMN IF NOT EXISTS "cloudinaryProcessedBytes" INTEGER,
  ADD COLUMN IF NOT EXISTS "cloudinaryOriginalFormat" TEXT,
  ADD COLUMN IF NOT EXISTS "cloudinaryProcessedFormat" TEXT;
