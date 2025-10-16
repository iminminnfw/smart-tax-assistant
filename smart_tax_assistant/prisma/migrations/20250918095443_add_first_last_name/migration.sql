-- CreateEnum
CREATE TYPE "public"."TaxType" AS ENUM ('INDIVIDUAL');

-- CreateEnum
CREATE TYPE "public"."Language" AS ENUM ('TH', 'EN');

-- CreateEnum
CREATE TYPE "public"."UserTokenType" AS ENUM ('PASSWORD_RESET', 'PASSWORD_CHANGE', 'NEW_DEVICE_CONFIRM', 'EMAIL_VERIFY');

-- AlterTable
ALTER TABLE "public"."users" ADD COLUMN     "firstName" VARCHAR(120),
ADD COLUMN     "lastName" VARCHAR(160);

-- CreateTable
CREATE TABLE "public"."user_tokens" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "type" "public"."UserTokenType" NOT NULL,
    "tokenHash" TEXT NOT NULL,
    "expires" TIMESTAMP(3) NOT NULL,
    "usedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "user_tokens_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "user_tokens_tokenHash_key" ON "public"."user_tokens"("tokenHash");

-- CreateIndex
CREATE INDEX "user_tokens_userId_type_idx" ON "public"."user_tokens"("userId", "type");

-- CreateIndex
CREATE INDEX "user_tokens_expires_idx" ON "public"."user_tokens"("expires");

-- AddForeignKey
ALTER TABLE "public"."user_tokens" ADD CONSTRAINT "user_tokens_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
