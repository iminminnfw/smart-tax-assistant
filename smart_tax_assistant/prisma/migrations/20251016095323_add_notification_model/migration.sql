/*
  Warnings:

  - You are about to drop the `VerificationToken` table. If the table is not empty, all the data it contains will be lost.

*/
-- CreateEnum
CREATE TYPE "public"."IncomeType" AS ENUM ('TYPE_6', 'TYPE_8');

-- CreateEnum
CREATE TYPE "public"."ExpenseType" AS ENUM ('ACTUAL', 'LUMP_SUM');

-- CreateEnum
CREATE TYPE "public"."DeductionCategory" AS ENUM ('PERSONAL', 'SPOUSE', 'CHILD', 'PARENT', 'INSURANCE', 'HEALTH_INSURANCE', 'PROVIDENT_FUND', 'RMF', 'SSF', 'PENSION', 'DONATION', 'HOME_LOAN', 'EDUCATION', 'OTHER');

-- CreateEnum
CREATE TYPE "public"."NotificationStatus" AS ENUM ('PENDING', 'SENT', 'FAILED', 'READ');

-- CreateEnum
CREATE TYPE "public"."NotificationType" AS ENUM ('TAX_DEADLINE', 'TAX_CALCULATION_COMPLETE', 'DOCUMENT_UPLOADED', 'PROFILE_UPDATED', 'SYSTEM');

-- DropForeignKey
ALTER TABLE "public"."document_files" DROP CONSTRAINT "document_files_folderId_fkey";

-- DropForeignKey
ALTER TABLE "public"."document_folders" DROP CONSTRAINT "document_folders_parentId_fkey";

-- DropTable
DROP TABLE "public"."VerificationToken";

-- CreateTable
CREATE TABLE "public"."verification_tokens" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "token" TEXT NOT NULL,
    "expires" TIMESTAMP(3) NOT NULL,
    "type" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "verification_tokens_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."incomes" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "type" "public"."IncomeType" NOT NULL,
    "amount" DECIMAL(12,2) NOT NULL,
    "description" TEXT,
    "date" TIMESTAMP(3) NOT NULL,
    "category" VARCHAR(100),
    "fileIds" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "incomes_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."expenses" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "incomeType" "public"."IncomeType" NOT NULL,
    "amount" DECIMAL(12,2) NOT NULL,
    "description" TEXT,
    "date" TIMESTAMP(3) NOT NULL,
    "category" VARCHAR(100) NOT NULL,
    "fileIds" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "isDeductible" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "expenses_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."tax_deductions" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "category" "public"."DeductionCategory" NOT NULL,
    "amount" DECIMAL(12,2) NOT NULL,
    "description" TEXT,
    "year" INTEGER NOT NULL,
    "fileIds" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "tax_deductions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."tax_calculations" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "year" INTEGER NOT NULL,
    "totalIncome" DECIMAL(12,2) NOT NULL,
    "incomeType6" DECIMAL(12,2) NOT NULL,
    "incomeType8" DECIMAL(12,2) NOT NULL,
    "expenseMethod" "public"."ExpenseType" NOT NULL,
    "totalExpenses" DECIMAL(12,2) NOT NULL,
    "expensesType6" DECIMAL(12,2) NOT NULL,
    "expensesType8" DECIMAL(12,2) NOT NULL,
    "netIncome" DECIMAL(12,2) NOT NULL,
    "totalDeductions" DECIMAL(12,2) NOT NULL,
    "taxableIncome" DECIMAL(12,2) NOT NULL,
    "taxAmount" DECIMAL(12,2) NOT NULL,
    "withholdingTax" DECIMAL(12,2),
    "taxPayable" DECIMAL(12,2) NOT NULL,
    "comparisonData" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "tax_calculations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."tax_simulations" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "name" VARCHAR(200) NOT NULL,
    "baseYear" INTEGER NOT NULL,
    "simulatedIncome" DECIMAL(12,2) NOT NULL,
    "simulatedExpenses" DECIMAL(12,2) NOT NULL,
    "deductionsData" JSONB NOT NULL,
    "projectedTax" DECIMAL(12,2) NOT NULL,
    "taxSavings" DECIMAL(12,2) NOT NULL,
    "aiRecommendations" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "tax_simulations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."notifications" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "type" "public"."NotificationType" NOT NULL,
    "status" "public"."NotificationStatus" NOT NULL DEFAULT 'PENDING',
    "channel" "public"."NotificationChannel" NOT NULL,
    "title" VARCHAR(200) NOT NULL,
    "message" TEXT NOT NULL,
    "data" JSONB,
    "sentAt" TIMESTAMP(3),
    "readAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "notifications_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "verification_tokens_token_key" ON "public"."verification_tokens"("token");

-- CreateIndex
CREATE INDEX "incomes_userId_date_idx" ON "public"."incomes"("userId", "date");

-- CreateIndex
CREATE INDEX "incomes_userId_type_idx" ON "public"."incomes"("userId", "type");

-- CreateIndex
CREATE INDEX "expenses_userId_date_idx" ON "public"."expenses"("userId", "date");

-- CreateIndex
CREATE INDEX "expenses_userId_incomeType_idx" ON "public"."expenses"("userId", "incomeType");

-- CreateIndex
CREATE INDEX "tax_deductions_userId_year_idx" ON "public"."tax_deductions"("userId", "year");

-- CreateIndex
CREATE INDEX "tax_deductions_userId_category_idx" ON "public"."tax_deductions"("userId", "category");

-- CreateIndex
CREATE INDEX "tax_calculations_userId_idx" ON "public"."tax_calculations"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "tax_calculations_userId_year_key" ON "public"."tax_calculations"("userId", "year");

-- CreateIndex
CREATE INDEX "tax_simulations_userId_baseYear_idx" ON "public"."tax_simulations"("userId", "baseYear");

-- CreateIndex
CREATE INDEX "notifications_userId_status_idx" ON "public"."notifications"("userId", "status");

-- CreateIndex
CREATE INDEX "notifications_userId_createdAt_idx" ON "public"."notifications"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "document_files_userId_idx" ON "public"."document_files"("userId");

-- CreateIndex
CREATE INDEX "document_files_folderId_idx" ON "public"."document_files"("folderId");

-- CreateIndex
CREATE INDEX "document_folders_userId_idx" ON "public"."document_folders"("userId");

-- CreateIndex
CREATE INDEX "document_folders_parentId_idx" ON "public"."document_folders"("parentId");

-- AddForeignKey
ALTER TABLE "public"."incomes" ADD CONSTRAINT "incomes_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."expenses" ADD CONSTRAINT "expenses_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."tax_deductions" ADD CONSTRAINT "tax_deductions_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."tax_calculations" ADD CONSTRAINT "tax_calculations_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."tax_simulations" ADD CONSTRAINT "tax_simulations_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."document_folders" ADD CONSTRAINT "document_folders_parentId_fkey" FOREIGN KEY ("parentId") REFERENCES "public"."document_folders"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."document_files" ADD CONSTRAINT "document_files_folderId_fkey" FOREIGN KEY ("folderId") REFERENCES "public"."document_folders"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."notifications" ADD CONSTRAINT "notifications_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
