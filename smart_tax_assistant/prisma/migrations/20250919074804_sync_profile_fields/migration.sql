-- AlterTable
ALTER TABLE "public"."users" ADD COLUMN     "address" TEXT,
ADD COLUMN     "annualIncome" DECIMAL(12,2),
ADD COLUMN     "dateOfBirth" TIMESTAMP(3),
ADD COLUMN     "district" VARCHAR(100),
ADD COLUMN     "language" "public"."Language" NOT NULL DEFAULT 'TH',
ADD COLUMN     "notifyEmail" BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN     "notifyReports" BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN     "notifySms" BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN     "notifyTaxDeadlines" BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN     "occupation" VARCHAR(120),
ADD COLUMN     "postalCode" VARCHAR(10),
ADD COLUMN     "province" VARCHAR(100);
