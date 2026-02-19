-- CreateEnum
CREATE TYPE "GoalPriority" AS ENUM ('AGGRESSIVE', 'BALANCED', 'CONSERVATIVE');

-- CreateEnum
CREATE TYPE "GoalType" AS ENUM ('TAX_SAVING', 'CASH_FLOW', 'RETIREMENT', 'LIFE_EVENT', 'HYBRID');

-- CreateEnum
CREATE TYPE "MaritalStatus" AS ENUM ('SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED');

-- CreateEnum
CREATE TYPE "RiskTolerance" AS ENUM ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE');

-- CreateTable
CREATE TABLE "user_financial_profiles" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "monthlyExpenses" DECIMAL(12,2),
    "existingSavings" DECIMAL(12,2),
    "emergencyFund" DECIMAL(12,2),
    "riskTolerance" "RiskTolerance" NOT NULL DEFAULT 'MODERATE',
    "investmentHorizon" INTEGER,
    "maritalStatus" "MaritalStatus" NOT NULL DEFAULT 'SINGLE',
    "numChildren" INTEGER NOT NULL DEFAULT 0,
    "numParents" INTEGER NOT NULL DEFAULT 0,
    "hasDisability" BOOLEAN NOT NULL DEFAULT false,
    "usedRmf" DECIMAL(12,2) DEFAULT 0,
    "usedSsf" DECIMAL(12,2) DEFAULT 0,
    "usedThaiEsg" DECIMAL(12,2) DEFAULT 0,
    "usedLifeInsurance" DECIMAL(12,2) DEFAULT 0,
    "usedHealthInsurance" DECIMAL(12,2) DEFAULT 0,
    "usedPensionFund" DECIMAL(12,2) DEFAULT 0,
    "usedProvidentFund" DECIMAL(12,2) DEFAULT 0,
    "usedSocialSecurity" DECIMAL(12,2) DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "user_financial_profiles_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "user_goals" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "rawGoalText" TEXT NOT NULL,
    "goalType" "GoalType" NOT NULL,
    "targetAmount" DECIMAL(12,2),
    "deadline" TIMESTAMP(3),
    "priority" "GoalPriority" NOT NULL DEFAULT 'BALANCED',
    "constraints" JSONB,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "user_goals_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_scenarios" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "goalId" TEXT,
    "name" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "badge" VARCHAR(50),
    "rmfInvestment" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "ssfInvestment" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "thaiEsgInvestment" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "lifeInsurance" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "pensionFund" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "totalInvestment" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "taxSavings" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "cashRemaining" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "riskLevel" INTEGER NOT NULL DEFAULT 5,
    "riskLabel" VARCHAR(50),
    "explanation" TEXT,
    "pros" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "cons" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "suitableFor" TEXT,
    "actionSteps" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "recommendedFunds" JSONB,
    "confidenceScore" DECIMAL(5,2),
    "suitabilityScore" DECIMAL(5,2),
    "isSelected" BOOLEAN NOT NULL DEFAULT false,
    "selectedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ai_scenarios_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "user_financial_profiles_userId_key" ON "user_financial_profiles"("userId");

-- CreateIndex
CREATE INDEX "user_goals_userId_idx" ON "user_goals"("userId");

-- CreateIndex
CREATE INDEX "user_goals_userId_isActive_idx" ON "user_goals"("userId", "isActive");

-- CreateIndex
CREATE INDEX "ai_scenarios_userId_idx" ON "ai_scenarios"("userId");

-- CreateIndex
CREATE INDEX "ai_scenarios_userId_isSelected_idx" ON "ai_scenarios"("userId", "isSelected");

-- CreateIndex
CREATE INDEX "ai_scenarios_goalId_idx" ON "ai_scenarios"("goalId");

-- AddForeignKey
ALTER TABLE "user_financial_profiles" ADD CONSTRAINT "user_financial_profiles_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "user_goals" ADD CONSTRAINT "user_goals_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_scenarios" ADD CONSTRAINT "ai_scenarios_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_scenarios" ADD CONSTRAINT "ai_scenarios_goalId_fkey" FOREIGN KEY ("goalId") REFERENCES "user_goals"("id") ON DELETE SET NULL ON UPDATE CASCADE;
