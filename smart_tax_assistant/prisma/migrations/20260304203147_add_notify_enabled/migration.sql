-- AlterTable
ALTER TABLE "public"."users" ADD COLUMN     "notifyEnabled" BOOLEAN NOT NULL DEFAULT false,
ALTER COLUMN "notifyEmail" SET DEFAULT false;
