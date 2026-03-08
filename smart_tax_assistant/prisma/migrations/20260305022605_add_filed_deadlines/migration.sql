-- AlterTable
ALTER TABLE "public"."users" ADD COLUMN     "filedDeadlines" TEXT[] DEFAULT ARRAY[]::TEXT[];
