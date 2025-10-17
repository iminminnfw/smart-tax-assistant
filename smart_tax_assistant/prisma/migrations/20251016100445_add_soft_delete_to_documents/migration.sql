-- AlterTable
ALTER TABLE "public"."document_files" ADD COLUMN     "deletedAt" TIMESTAMP(3),
ADD COLUMN     "isDeleted" BOOLEAN NOT NULL DEFAULT false;

-- AlterTable
ALTER TABLE "public"."document_folders" ADD COLUMN     "deletedAt" TIMESTAMP(3),
ADD COLUMN     "isDeleted" BOOLEAN NOT NULL DEFAULT false;

-- CreateIndex
CREATE INDEX "document_files_userId_isDeleted_idx" ON "public"."document_files"("userId", "isDeleted");

-- CreateIndex
CREATE INDEX "document_folders_userId_isDeleted_idx" ON "public"."document_folders"("userId", "isDeleted");
