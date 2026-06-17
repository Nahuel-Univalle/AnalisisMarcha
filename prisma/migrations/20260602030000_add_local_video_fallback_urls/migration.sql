ALTER TABLE "VideoMarcha"
  ADD COLUMN IF NOT EXISTS "localOriginalVideoUrl" TEXT,
  ADD COLUMN IF NOT EXISTS "localProcessedVideoUrl" TEXT;
