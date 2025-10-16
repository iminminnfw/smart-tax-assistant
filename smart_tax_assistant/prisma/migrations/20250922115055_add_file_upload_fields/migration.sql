-- AlterTable
ALTER TABLE "public"."document_files" ADD COLUMN     "fileName" VARCHAR(255),
ADD COLUMN     "fileSize" INTEGER,
ADD COLUMN     "isUploaded" BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN     "mimeType" VARCHAR(100);
