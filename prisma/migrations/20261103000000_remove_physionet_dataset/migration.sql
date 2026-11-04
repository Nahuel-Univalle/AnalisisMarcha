-- Elimina el dataset antiguo PhysioNet "Gait in Parkinson's Disease" (sensores en
-- plantillas). La aplicación solo analiza video con el modelo de 4 clases; estas
-- tablas no tienen claves foráneas y no afectan a ninguna otra tabla.

-- DropTable
DROP TABLE "public"."DatasetImportLog";

-- DropTable
DROP TABLE "public"."ParkinsonDatasetRecord";

-- DropTable
DROP TABLE "public"."ParkinsonRawSample";
