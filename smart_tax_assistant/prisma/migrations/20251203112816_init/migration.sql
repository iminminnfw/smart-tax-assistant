-- CreateEnum
CREATE TYPE "public"."TaxType" AS ENUM ('INDIVIDUAL');

-- CreateEnum
CREATE TYPE "public"."NotificationChannel" AS ENUM ('EMAIL', 'SMS', 'NONE');

-- CreateEnum
CREATE TYPE "public"."Language" AS ENUM ('TH', 'EN');

-- CreateEnum
CREATE TYPE "public"."UserTokenType" AS ENUM ('PASSWORD_RESET', 'PASSWORD_CHANGE', 'NEW_DEVICE_CONFIRM', 'EMAIL_VERIFY');

-- CreateEnum
CREATE TYPE "public"."OTPPurpose" AS ENUM ('EMAIL_VERIFICATION', 'LOGIN_MFA', 'PASSWORD_RESET');

-- CreateEnum
CREATE TYPE "public"."TaxFilingStatus" AS ENUM ('DRAFT', 'SUBMITTED');

-- CreateEnum
CREATE TYPE "public"."TaxFormType" AS ENUM ('PND90', 'PND91', 'PND94');

-- CreateEnum
CREATE TYPE "public"."IncomeType" AS ENUM ('SALARY', 'FREELANCE', 'BUSINESS', 'INVESTMENT', 'RENTAL', 'OTHER');

-- CreateEnum
CREATE TYPE "public"."DeductionType" AS ENUM ('PERSONAL', 'SPOUSE', 'CHILD', 'PARENT', 'LIFE_INSURANCE', 'HEALTH_INSURANCE', 'PROVIDENT_FUND', 'RMF', 'SSF', 'DONATION', 'HOME_LOAN', 'OTHER');

-- CreateTable
CREATE TABLE "public"."users" (
    "id" TEXT NOT NULL,
    "name" TEXT,
    "firstName" VARCHAR(120),
    "lastName" VARCHAR(160),
    "email" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "phone" VARCHAR(20),
    "dateOfBirth" TIMESTAMP(3),
    "address" TEXT,
    "district" VARCHAR(100),
    "province" VARCHAR(100),
    "postalCode" VARCHAR(10),
    "occupation" VARCHAR(120),
    "annualIncome" DECIMAL(12,2),
    "language" "public"."Language" NOT NULL DEFAULT 'TH',
    "taxType" "public"."TaxType" NOT NULL DEFAULT 'INDIVIDUAL',
    "emailVerified" TIMESTAMP(3),
    "image" TEXT,
    "notifyOnPasswordChange" "public"."NotificationChannel" NOT NULL DEFAULT 'EMAIL',
    "notifyEmail" BOOLEAN NOT NULL DEFAULT true,
    "notifySms" BOOLEAN NOT NULL DEFAULT false,
    "notifyTaxDeadlines" BOOLEAN NOT NULL DEFAULT true,
    "notifyReports" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."accounts" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "providerAccountId" TEXT NOT NULL,
    "refresh_token" TEXT,
    "access_token" TEXT,
    "expires_at" INTEGER,
    "token_type" TEXT,
    "scope" TEXT,
    "id_token" TEXT,
    "session_state" TEXT,

    CONSTRAINT "accounts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."sessions" (
    "id" TEXT NOT NULL,
    "sessionToken" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "expires" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "sessions_pkey" PRIMARY KEY ("id")
);

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

-- CreateTable
CREATE TABLE "public"."otps" (
    "id" TEXT NOT NULL,
    "userId" TEXT,
    "email" TEXT NOT NULL,
    "otpCode" VARCHAR(6) NOT NULL,
    "purpose" "public"."OTPPurpose" NOT NULL,
    "expiresAt" TIMESTAMP(3) NOT NULL,
    "verified" BOOLEAN NOT NULL DEFAULT false,
    "verifiedAt" TIMESTAMP(3),
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "maxAttempts" INTEGER NOT NULL DEFAULT 5,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "otps_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."document_folders" (
    "id" TEXT NOT NULL,
    "name" VARCHAR(200) NOT NULL,
    "color" TEXT NOT NULL DEFAULT '#3B82F6',
    "userId" TEXT NOT NULL,
    "parentId" TEXT,
    "isDeleted" BOOLEAN NOT NULL DEFAULT false,
    "deletedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "document_folders_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."document_files" (
    "id" TEXT NOT NULL,
    "name" VARCHAR(200) NOT NULL,
    "content" TEXT,
    "fileUrl" TEXT,
    "fileName" VARCHAR(255),
    "fileSize" INTEGER,
    "mimeType" VARCHAR(100),
    "isUploaded" BOOLEAN NOT NULL DEFAULT false,
    "type" TEXT,
    "tags" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "isDeleted" BOOLEAN NOT NULL DEFAULT false,
    "deletedAt" TIMESTAMP(3),
    "folderId" TEXT,
    "userId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "document_files_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."tax_filings" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "taxYear" INTEGER NOT NULL,
    "formType" "public"."TaxFormType" NOT NULL,
    "status" "public"."TaxFilingStatus" NOT NULL DEFAULT 'DRAFT',
    "totalIncome" DECIMAL(12,2),
    "totalDeduction" DECIMAL(12,2),
    "taxAmount" DECIMAL(12,2),
    "submittedAt" TIMESTAMP(3),
    "notes" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "tax_filings_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."income_records" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "type" "public"."IncomeType" NOT NULL,
    "amount" DECIMAL(12,2) NOT NULL,
    "description" TEXT,
    "date" TIMESTAMP(3) NOT NULL,
    "taxYear" INTEGER NOT NULL,
    "documentId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "income_records_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."deduction_records" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "type" "public"."DeductionType" NOT NULL,
    "amount" DECIMAL(12,2) NOT NULL,
    "description" TEXT,
    "date" TIMESTAMP(3) NOT NULL,
    "taxYear" INTEGER NOT NULL,
    "documentId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "deduction_records_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "public"."users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "users_phone_key" ON "public"."users"("phone");

-- CreateIndex
CREATE UNIQUE INDEX "accounts_provider_providerAccountId_key" ON "public"."accounts"("provider", "providerAccountId");

-- CreateIndex
CREATE UNIQUE INDEX "sessions_sessionToken_key" ON "public"."sessions"("sessionToken");

-- CreateIndex
CREATE UNIQUE INDEX "user_tokens_tokenHash_key" ON "public"."user_tokens"("tokenHash");

-- CreateIndex
CREATE INDEX "user_tokens_userId_type_idx" ON "public"."user_tokens"("userId", "type");

-- CreateIndex
CREATE INDEX "user_tokens_expires_idx" ON "public"."user_tokens"("expires");

-- CreateIndex
CREATE INDEX "otps_email_purpose_idx" ON "public"."otps"("email", "purpose");

-- CreateIndex
CREATE INDEX "otps_expiresAt_idx" ON "public"."otps"("expiresAt");

-- CreateIndex
CREATE INDEX "otps_userId_idx" ON "public"."otps"("userId");

-- CreateIndex
CREATE INDEX "document_folders_userId_idx" ON "public"."document_folders"("userId");

-- CreateIndex
CREATE INDEX "document_folders_parentId_idx" ON "public"."document_folders"("parentId");

-- CreateIndex
CREATE INDEX "document_folders_userId_isDeleted_idx" ON "public"."document_folders"("userId", "isDeleted");

-- CreateIndex
CREATE INDEX "document_files_userId_idx" ON "public"."document_files"("userId");

-- CreateIndex
CREATE INDEX "document_files_folderId_idx" ON "public"."document_files"("folderId");

-- CreateIndex
CREATE INDEX "document_files_userId_isDeleted_idx" ON "public"."document_files"("userId", "isDeleted");

-- CreateIndex
CREATE INDEX "tax_filings_userId_taxYear_idx" ON "public"."tax_filings"("userId", "taxYear");

-- CreateIndex
CREATE INDEX "income_records_userId_taxYear_idx" ON "public"."income_records"("userId", "taxYear");

-- CreateIndex
CREATE INDEX "deduction_records_userId_taxYear_idx" ON "public"."deduction_records"("userId", "taxYear");

-- AddForeignKey
ALTER TABLE "public"."accounts" ADD CONSTRAINT "accounts_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."sessions" ADD CONSTRAINT "sessions_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."user_tokens" ADD CONSTRAINT "user_tokens_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."document_folders" ADD CONSTRAINT "document_folders_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."document_folders" ADD CONSTRAINT "document_folders_parentId_fkey" FOREIGN KEY ("parentId") REFERENCES "public"."document_folders"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."document_files" ADD CONSTRAINT "document_files_folderId_fkey" FOREIGN KEY ("folderId") REFERENCES "public"."document_folders"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."document_files" ADD CONSTRAINT "document_files_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."tax_filings" ADD CONSTRAINT "tax_filings_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."income_records" ADD CONSTRAINT "income_records_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."income_records" ADD CONSTRAINT "income_records_documentId_fkey" FOREIGN KEY ("documentId") REFERENCES "public"."document_files"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."deduction_records" ADD CONSTRAINT "deduction_records_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."deduction_records" ADD CONSTRAINT "deduction_records_documentId_fkey" FOREIGN KEY ("documentId") REFERENCES "public"."document_files"("id") ON DELETE SET NULL ON UPDATE CASCADE;
