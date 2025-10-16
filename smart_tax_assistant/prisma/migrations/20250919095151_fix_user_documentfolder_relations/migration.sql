-- AlterTable
ALTER TABLE "public"."document_files" ADD COLUMN     "tags" TEXT[] DEFAULT ARRAY[]::TEXT[];

-- AlterTable
ALTER TABLE "public"."document_folders" ADD COLUMN     "color" TEXT NOT NULL DEFAULT '#3B82F6';
