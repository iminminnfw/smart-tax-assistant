-- CreateTable
CREATE TABLE "public"."fund_amcs" (
    "id" TEXT NOT NULL,
    "nameTh" TEXT NOT NULL,
    "nameEn" TEXT NOT NULL,
    "lastUpdDate" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "fund_amcs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."funds" (
    "id" TEXT NOT NULL,
    "amcId" TEXT NOT NULL,
    "regisId" TEXT,
    "projNameTh" TEXT NOT NULL,
    "projNameEn" TEXT NOT NULL,
    "projAbbrName" TEXT NOT NULL,
    "fundStatus" TEXT NOT NULL,
    "policyDesc" TEXT,
    "investmentPolicyDesc" TEXT,
    "managementStyle" TEXT,
    "feederFundMasterFund" TEXT,
    "feederFundCountry" TEXT,
    "fxHedgingPolicy" TEXT,
    "investCountryFlag" INTEGER,
    "retailType" TEXT,
    "termFlag" TEXT,
    "termDay" INTEGER,
    "termMonth" INTEGER,
    "termYear" INTEGER,
    "initDate" TIMESTAMP(3),
    "regisDate" TIMESTAMP(3),
    "cancelDate" TIMESTAMP(3),
    "fundClassName" TEXT,
    "fundClassDetail" TEXT,
    "fundClassDescription" TEXT,
    "taxIncentiveType" TEXT,
    "isinCode" TEXT,
    "lastUpdDate" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "funds_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."fund_risk_spectrums" (
    "id" TEXT NOT NULL,
    "fundId" TEXT NOT NULL,
    "startDate" TIMESTAMP(3) NOT NULL,
    "endDate" TIMESTAMP(3) NOT NULL,
    "prospectusType" TEXT NOT NULL,
    "riskSpectrum" INTEGER NOT NULL,
    "riskSpectrumDesc" TEXT,
    "lastUpdDate" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "fund_risk_spectrums_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."fund_statistics" (
    "id" TEXT NOT NULL,
    "fundId" TEXT NOT NULL,
    "fundClassName" TEXT,
    "startDate" TIMESTAMP(3) NOT NULL,
    "endDate" TIMESTAMP(3) NOT NULL,
    "prospectusType" TEXT NOT NULL,
    "turnoverRatio" DOUBLE PRECISION,
    "recoveringPeriod" DOUBLE PRECISION,
    "portfolioDurationPeriod" DOUBLE PRECISION,
    "maxDrawdown" DOUBLE PRECISION,
    "sharpeRatio" DOUBLE PRECISION,
    "beta" DOUBLE PRECISION,
    "alpha" DOUBLE PRECISION,
    "fxHedging" DOUBLE PRECISION,
    "trackingError" DOUBLE PRECISION,
    "yieldToMaturity" DOUBLE PRECISION,
    "lastUpdDate" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "fund_statistics_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."fund_performances" (
    "id" TEXT NOT NULL,
    "fundId" TEXT NOT NULL,
    "fundClassName" TEXT,
    "startDate" TIMESTAMP(3) NOT NULL,
    "endDate" TIMESTAMP(3) NOT NULL,
    "prospectusType" TEXT NOT NULL,
    "performanceTypeDesc" TEXT NOT NULL,
    "referencePeriod" TEXT NOT NULL,
    "performanceValue" DOUBLE PRECISION,
    "lastUpdDate" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "fund_performances_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."fund_dividend_policies" (
    "id" TEXT NOT NULL,
    "fundId" TEXT NOT NULL,
    "fundClassName" TEXT,
    "startDate" TIMESTAMP(3) NOT NULL,
    "endDate" TIMESTAMP(3) NOT NULL,
    "prospectusType" TEXT NOT NULL,
    "dividendPolicy" TEXT NOT NULL,
    "lastUpdDate" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "fund_dividend_policies_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."fund_top_holdings" (
    "id" TEXT NOT NULL,
    "fundId" TEXT NOT NULL,
    "startDate" TIMESTAMP(3) NOT NULL,
    "endDate" TIMESTAMP(3) NOT NULL,
    "prospectusType" TEXT NOT NULL,
    "assetSeq" INTEGER NOT NULL,
    "assetName" TEXT NOT NULL,
    "assetRatio" DOUBLE PRECISION,
    "lastUpdDate" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "fund_top_holdings_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."fund_benchmarks" (
    "id" TEXT NOT NULL,
    "fundId" TEXT NOT NULL,
    "startDate" TIMESTAMP(3) NOT NULL,
    "endDate" TIMESTAMP(3) NOT NULL,
    "prospectusType" TEXT NOT NULL,
    "groupSeq" INTEGER NOT NULL,
    "benchmark" TEXT NOT NULL,
    "benchmarkRemark" TEXT,
    "lastUpdDate" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "fund_benchmarks_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."fund_specs" (
    "id" TEXT NOT NULL,
    "fundId" TEXT NOT NULL,
    "fundClassName" TEXT,
    "specCode" TEXT NOT NULL,
    "specDesc" TEXT,
    "lastUpdDate" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "fund_specs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."fund_factsheet_urls" (
    "id" TEXT NOT NULL,
    "fundId" TEXT NOT NULL,
    "fundClassName" TEXT,
    "prospectusType" TEXT,
    "amcUrlFactsheet" TEXT,
    "pdfFactsheet" TEXT,
    "asOfDate" TIMESTAMP(3),
    "lastUpdDate" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "fund_factsheet_urls_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "funds_fundStatus_idx" ON "public"."funds"("fundStatus");

-- CreateIndex
CREATE INDEX "funds_amcId_idx" ON "public"."funds"("amcId");

-- CreateIndex
CREATE INDEX "funds_taxIncentiveType_idx" ON "public"."funds"("taxIncentiveType");

-- CreateIndex
CREATE INDEX "funds_policyDesc_idx" ON "public"."funds"("policyDesc");

-- CreateIndex
CREATE INDEX "fund_risk_spectrums_fundId_idx" ON "public"."fund_risk_spectrums"("fundId");

-- CreateIndex
CREATE INDEX "fund_risk_spectrums_fundId_endDate_idx" ON "public"."fund_risk_spectrums"("fundId", "endDate");

-- CreateIndex
CREATE INDEX "fund_risk_spectrums_riskSpectrum_idx" ON "public"."fund_risk_spectrums"("riskSpectrum");

-- CreateIndex
CREATE INDEX "fund_statistics_fundId_idx" ON "public"."fund_statistics"("fundId");

-- CreateIndex
CREATE INDEX "fund_statistics_fundId_endDate_idx" ON "public"."fund_statistics"("fundId", "endDate");

-- CreateIndex
CREATE INDEX "fund_statistics_sharpeRatio_idx" ON "public"."fund_statistics"("sharpeRatio");

-- CreateIndex
CREATE INDEX "fund_performances_fundId_idx" ON "public"."fund_performances"("fundId");

-- CreateIndex
CREATE INDEX "fund_performances_fundId_endDate_referencePeriod_idx" ON "public"."fund_performances"("fundId", "endDate", "referencePeriod");

-- CreateIndex
CREATE INDEX "fund_dividend_policies_fundId_idx" ON "public"."fund_dividend_policies"("fundId");

-- CreateIndex
CREATE INDEX "fund_dividend_policies_fundId_endDate_idx" ON "public"."fund_dividend_policies"("fundId", "endDate");

-- CreateIndex
CREATE INDEX "fund_top_holdings_fundId_idx" ON "public"."fund_top_holdings"("fundId");

-- CreateIndex
CREATE INDEX "fund_top_holdings_fundId_endDate_idx" ON "public"."fund_top_holdings"("fundId", "endDate");

-- CreateIndex
CREATE INDEX "fund_benchmarks_fundId_idx" ON "public"."fund_benchmarks"("fundId");

-- CreateIndex
CREATE INDEX "fund_benchmarks_fundId_endDate_idx" ON "public"."fund_benchmarks"("fundId", "endDate");

-- CreateIndex
CREATE INDEX "fund_specs_fundId_idx" ON "public"."fund_specs"("fundId");

-- CreateIndex
CREATE INDEX "fund_specs_specCode_idx" ON "public"."fund_specs"("specCode");

-- CreateIndex
CREATE INDEX "fund_factsheet_urls_fundId_idx" ON "public"."fund_factsheet_urls"("fundId");

-- AddForeignKey
ALTER TABLE "public"."funds" ADD CONSTRAINT "funds_amcId_fkey" FOREIGN KEY ("amcId") REFERENCES "public"."fund_amcs"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."fund_risk_spectrums" ADD CONSTRAINT "fund_risk_spectrums_fundId_fkey" FOREIGN KEY ("fundId") REFERENCES "public"."funds"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."fund_statistics" ADD CONSTRAINT "fund_statistics_fundId_fkey" FOREIGN KEY ("fundId") REFERENCES "public"."funds"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."fund_performances" ADD CONSTRAINT "fund_performances_fundId_fkey" FOREIGN KEY ("fundId") REFERENCES "public"."funds"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."fund_dividend_policies" ADD CONSTRAINT "fund_dividend_policies_fundId_fkey" FOREIGN KEY ("fundId") REFERENCES "public"."funds"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."fund_top_holdings" ADD CONSTRAINT "fund_top_holdings_fundId_fkey" FOREIGN KEY ("fundId") REFERENCES "public"."funds"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."fund_benchmarks" ADD CONSTRAINT "fund_benchmarks_fundId_fkey" FOREIGN KEY ("fundId") REFERENCES "public"."funds"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."fund_specs" ADD CONSTRAINT "fund_specs_fundId_fkey" FOREIGN KEY ("fundId") REFERENCES "public"."funds"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."fund_factsheet_urls" ADD CONSTRAINT "fund_factsheet_urls_fundId_fkey" FOREIGN KEY ("fundId") REFERENCES "public"."funds"("id") ON DELETE CASCADE ON UPDATE CASCADE;
