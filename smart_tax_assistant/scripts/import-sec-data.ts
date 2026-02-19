/**
 * Import SEC Thailand Fund Data from XLSX files into PostgreSQL
 *
 * วิธีใช้:
 * npx tsx scripts/import-sec-data.ts
 *
 * ไฟล์ xlsx ต้องอยู่ใน C:\Users\mean1\SEC_API_Output\
 * Script นี้ idempotent - รันซ้ำได้ไม่พัง (ใช้ deleteMany + createMany pattern)
 */

import { PrismaClient } from '@prisma/client';
import * as XLSX from 'xlsx';
import * as path from 'path';
import * as fs from 'fs';

const prisma = new PrismaClient();

const DATA_DIR = 'C:/Users/mean1/SEC_API_Output';

// ============================================================
// Utility Functions
// ============================================================

function readXlsx(filename: string): any[] {
  const filePath = path.join(DATA_DIR, filename);
  if (!fs.existsSync(filePath)) {
    console.error(`  [SKIP] File not found: ${filePath}`);
    return [];
  }
  const workbook = XLSX.readFile(filePath);
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  return XLSX.utils.sheet_to_json(sheet);
}

function parseDate(value: any): Date | null {
  if (!value) return null;
  if (value instanceof Date) return value;
  // XLSX serial date number
  if (typeof value === 'number') {
    const d = XLSX.SSF.parse_date_code(value);
    return new Date(d.y, d.m - 1, d.d);
  }
  const d = new Date(value);
  return isNaN(d.getTime()) ? null : d;
}

function parseFloat2(value: any): number | null {
  if (value === null || value === undefined || value === '') return null;
  const n = parseFloat(value);
  return isNaN(n) ? null : n;
}

function parseInt2(value: any): number | null {
  if (value === null || value === undefined || value === '') return null;
  const n = parseInt(value, 10);
  return isNaN(n) ? null : n;
}

function str(value: any): string {
  if (value === null || value === undefined) return '';
  return String(value).trim();
}

function strOrNull(value: any): string | null {
  if (value === null || value === undefined || String(value).trim() === '') return null;
  return String(value).trim();
}

function parseRiskSpectrum(value: any): number | null {
  if (!value) return null;
  const s = String(value).trim();
  // Handle special cases: "RS8+" and "RS81" both mean risk level 8
  if (/^RS8\+$/i.test(s) || /^RS81$/i.test(s)) return 8;
  // Strip "RS" prefix: "RS4" → 4
  const match = s.match(/^RS(\d)$/i);
  if (match) return parseInt(match[1], 10);
  const n = parseInt(s, 10);
  return isNaN(n) && n >= 0 && n <= 8 ? n : (isNaN(n) ? null : Math.min(n, 8));
}

// ============================================================
// Import Functions
// ============================================================

async function importAmcs() {
  console.log('\n📦 Importing AMC List...');
  const rows = readXlsx('1_AMC_List.xlsx');
  if (!rows.length) return;

  let count = 0;
  for (const row of rows) {
    const id = str(row['unique_id']);
    if (!id) continue;

    await prisma.fundAmc.upsert({
      where: { id },
      create: {
        id,
        nameTh: str(row['comp_name_th']),
        nameEn: str(row['comp_name_en']),
        lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
      },
      update: {
        nameTh: str(row['comp_name_th']),
        nameEn: str(row['comp_name_en']),
        lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
      },
    });
    count++;
  }
  console.log(`  ✅ AMCs: ${count} upserted`);
}

async function importFunds() {
  console.log('\n📦 Importing Fund Profiles...');
  const rows = readXlsx('2_Fund_Profiles_Full.xlsx');
  if (!rows.length) return;

  // First, collect all unique AMC IDs from fund data
  const amcIds = new Set<string>();
  for (const row of rows) {
    const amcId = str(row['unique_id']);
    if (amcId) amcIds.add(amcId);
  }

  // Verify AMCs exist
  const existingAmcs = await prisma.fundAmc.findMany({ select: { id: true } });
  const existingAmcIds = new Set(existingAmcs.map(a => a.id));
  const missingAmcs = [...amcIds].filter(id => !existingAmcIds.has(id));
  if (missingAmcs.length > 0) {
    console.log(`  ⚠️ Warning: ${missingAmcs.length} AMC IDs in fund data not found in AMC table`);
  }

  let count = 0;
  let skipped = 0;
  for (const row of rows) {
    const id = str(row['proj_id']);
    const amcId = str(row['unique_id']);
    if (!id || !amcId || !existingAmcIds.has(amcId)) {
      skipped++;
      continue;
    }

    await prisma.fund.upsert({
      where: { id },
      create: {
        id,
        amcId,
        regisId: strOrNull(row['regis_id']),
        projNameTh: str(row['proj_name_th']),
        projNameEn: str(row['proj_name_en']),
        projAbbrName: str(row['proj_abbr_name']),
        fundStatus: str(row['fund_status']),
        policyDesc: strOrNull(row['policy_desc']),
        investmentPolicyDesc: strOrNull(row['investment_policy_desc']),
        managementStyle: strOrNull(row['management_style']),
        feederFundMasterFund: strOrNull(row['feederfund_master_fund']),
        feederFundCountry: strOrNull(row['feederfund_country']),
        fxHedgingPolicy: strOrNull(row['exchange_rate_protection_policy']),
        investCountryFlag: parseInt2(row['invest_country_flag']),
        retailType: strOrNull(row['proj_retail_type']),
        termFlag: strOrNull(row['proj_term_flag']),
        termDay: parseInt2(row['proj_term_day']),
        termMonth: parseInt2(row['proj_term_month']),
        termYear: parseInt2(row['proj_term_year']),
        initDate: parseDate(row['init_date']),
        regisDate: parseDate(row['regis_date']),
        cancelDate: parseDate(row['cancel_date']),
        fundClassName: strOrNull(row['fund_class_name']),
        fundClassDetail: strOrNull(row['fund_class_detail']),
        fundClassDescription: strOrNull(row['fund_class_description']),
        taxIncentiveType: strOrNull(row['fund_class_tax_incentive_type']),
        isinCode: strOrNull(row['fund_class_isin_code']),
        lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
      },
      update: {
        amcId,
        regisId: strOrNull(row['regis_id']),
        projNameTh: str(row['proj_name_th']),
        projNameEn: str(row['proj_name_en']),
        projAbbrName: str(row['proj_abbr_name']),
        fundStatus: str(row['fund_status']),
        policyDesc: strOrNull(row['policy_desc']),
        investmentPolicyDesc: strOrNull(row['investment_policy_desc']),
        managementStyle: strOrNull(row['management_style']),
        feederFundMasterFund: strOrNull(row['feederfund_master_fund']),
        feederFundCountry: strOrNull(row['feederfund_country']),
        fxHedgingPolicy: strOrNull(row['exchange_rate_protection_policy']),
        investCountryFlag: parseInt2(row['invest_country_flag']),
        retailType: strOrNull(row['proj_retail_type']),
        termFlag: strOrNull(row['proj_term_flag']),
        termDay: parseInt2(row['proj_term_day']),
        termMonth: parseInt2(row['proj_term_month']),
        termYear: parseInt2(row['proj_term_year']),
        initDate: parseDate(row['init_date']),
        regisDate: parseDate(row['regis_date']),
        cancelDate: parseDate(row['cancel_date']),
        fundClassName: strOrNull(row['fund_class_name']),
        fundClassDetail: strOrNull(row['fund_class_detail']),
        fundClassDescription: strOrNull(row['fund_class_description']),
        taxIncentiveType: strOrNull(row['fund_class_tax_incentive_type']),
        isinCode: strOrNull(row['fund_class_isin_code']),
        lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
      },
    });
    count++;

    if (count % 1000 === 0) {
      console.log(`  ... ${count} funds processed`);
    }
  }
  console.log(`  ✅ Funds: ${count} upserted, ${skipped} skipped`);
}

async function importChildTable<T>(
  tableName: string,
  filename: string,
  mapRow: (row: any) => T | null,
  deleteAll: () => Promise<any>,
  createMany: (data: T[]) => Promise<any>,
  batchSize: number = 5000
) {
  console.log(`\n📦 Importing ${tableName}...`);
  const rows = readXlsx(filename);
  if (!rows.length) return;

  // Get valid fund IDs
  const funds = await prisma.fund.findMany({ select: { id: true } });
  const validFundIds = new Set(funds.map(f => f.id));

  const mapped: T[] = [];
  let skipped = 0;
  for (const row of rows) {
    const fundId = str(row['proj_id']);
    if (!fundId || !validFundIds.has(fundId)) {
      skipped++;
      continue;
    }
    const item = mapRow(row);
    if (item) mapped.push(item);
    else skipped++;
  }

  // Delete all existing and re-create (idempotent)
  await deleteAll();

  // Insert in batches
  for (let i = 0; i < mapped.length; i += batchSize) {
    const batch = mapped.slice(i, i + batchSize);
    await createMany(batch);
    if (i + batchSize < mapped.length) {
      console.log(`  ... ${i + batchSize} / ${mapped.length}`);
    }
  }

  console.log(`  ✅ ${tableName}: ${mapped.length} created, ${skipped} skipped`);
}

async function importRiskSpectrums() {
  await importChildTable(
    'Risk Spectrums',
    '11_Risk_Spectrum.xlsx',
    (row) => {
      const risk = parseRiskSpectrum(row['risk_spectrum']);
      if (risk === null) return null;
      return {
        fundId: str(row['proj_id']),
        startDate: parseDate(row['start_date']) || new Date(),
        endDate: parseDate(row['end_date']) || new Date(),
        prospectusType: str(row['prospectus_type']),
        riskSpectrum: risk,
        riskSpectrumDesc: strOrNull(row['risk_spectrum_desc']),
        lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
      };
    },
    () => prisma.fundRiskSpectrum.deleteMany(),
    (data: any[]) => prisma.fundRiskSpectrum.createMany({ data }),
  );
}

async function importStatistics() {
  await importChildTable(
    'Statistics',
    '12_Statistics.xlsx',
    (row) => ({
      fundId: str(row['proj_id']),
      fundClassName: strOrNull(row['fund_class_name']),
      startDate: parseDate(row['start_date']) || new Date(),
      endDate: parseDate(row['end_date']) || new Date(),
      prospectusType: str(row['prospectus_type']),
      turnoverRatio: parseFloat2(row['portfolio_turnover_ratio']),
      recoveringPeriod: parseFloat2(row['recovering_period']),
      portfolioDurationPeriod: parseFloat2(row['portfolio_duration_period']),
      maxDrawdown: parseFloat2(row['maximum_drawdown']),
      sharpeRatio: parseFloat2(row['sharpe_ratio']),
      beta: parseFloat2(row['beta']),
      alpha: parseFloat2(row['alpha']),
      fxHedging: parseFloat2(row['fx_hedging']),
      trackingError: parseFloat2(row['tracking_error']),
      yieldToMaturity: parseFloat2(row['yield_to_maturity']),
      lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
    }),
    () => prisma.fundStatistics.deleteMany(),
    (data: any[]) => prisma.fundStatistics.createMany({ data }),
  );
}

async function importPerformances() {
  await importChildTable(
    'Performances',
    '15_Performance.xlsx',
    (row) => ({
      fundId: str(row['proj_id']),
      fundClassName: strOrNull(row['fund_class_name']),
      startDate: parseDate(row['start_date']) || new Date(),
      endDate: parseDate(row['end_date']) || new Date(),
      prospectusType: str(row['prospectus_type']),
      performanceTypeDesc: str(row['performance_type_desc']),
      referencePeriod: str(row['reference_period']),
      performanceValue: parseFloat2(row['performance_value']),
      lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
    }),
    () => prisma.fundPerformance.deleteMany(),
    (data: any[]) => prisma.fundPerformance.createMany({ data }),
  );
}

async function importDividendPolicies() {
  await importChildTable(
    'Dividend Policies',
    '13_Dividend_Policy.xlsx',
    (row) => ({
      fundId: str(row['proj_id']),
      fundClassName: strOrNull(row['fund_class_name']),
      startDate: parseDate(row['start_date']) || new Date(),
      endDate: parseDate(row['end_date']) || new Date(),
      prospectusType: str(row['prospectus_type']),
      dividendPolicy: str(row['dividend_policy']),
      lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
    }),
    () => prisma.fundDividendPolicy.deleteMany(),
    (data: any[]) => prisma.fundDividendPolicy.createMany({ data }),
  );
}

async function importTopHoldings() {
  await importChildTable(
    'Top Holdings',
    '17_Top5_Holdings.xlsx',
    (row) => ({
      fundId: str(row['proj_id']),
      startDate: parseDate(row['start_date']) || new Date(),
      endDate: parseDate(row['end_date']) || new Date(),
      prospectusType: str(row['prospectus_type']),
      assetSeq: parseInt2(row['asset_seq']) || 0,
      assetName: str(row['asset_name']),
      assetRatio: parseFloat2(row['asset_ratio']),
      lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
    }),
    () => prisma.fundTopHolding.deleteMany(),
    (data: any[]) => prisma.fundTopHolding.createMany({ data }),
  );
}

async function importBenchmarks() {
  await importChildTable(
    'Benchmarks',
    '8_Benchmarks.xlsx',
    (row) => ({
      fundId: str(row['proj_id']),
      startDate: parseDate(row['start_date']) || new Date(),
      endDate: parseDate(row['end_date']) || new Date(),
      prospectusType: str(row['prospectus_type']),
      groupSeq: parseInt2(row['group_seq']) || 0,
      benchmark: str(row['benchmark']),
      benchmarkRemark: strOrNull(row['benchmark_remark']),
      lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
    }),
    () => prisma.fundBenchmark.deleteMany(),
    (data: any[]) => prisma.fundBenchmark.createMany({ data }),
  );
}

async function importSpecs() {
  await importChildTable(
    'Fund Specs',
    '3_Fund_Specs.xlsx',
    (row) => ({
      fundId: str(row['proj_id']),
      fundClassName: strOrNull(row['fund_class_name']),
      specCode: str(row['spec_code']),
      specDesc: strOrNull(row['spec_desc']),
      lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
    }),
    () => prisma.fundSpec.deleteMany(),
    (data: any[]) => prisma.fundSpec.createMany({ data }),
  );
}

async function importFactsheetUrls() {
  await importChildTable(
    'Factsheet URLs',
    '6_FactSheet_URLs.xlsx',
    (row) => ({
      fundId: str(row['proj_id']),
      fundClassName: strOrNull(row['fund_class_name']),
      prospectusType: strOrNull(row['prospectus_type']),
      amcUrlFactsheet: strOrNull(row['amc_url_factsheet']),
      pdfFactsheet: strOrNull(row['pdf_factsheet']),
      asOfDate: parseDate(row['as_of_date']),
      lastUpdDate: parseDate(row['last_upd_date']) || new Date(),
    }),
    () => prisma.fundFactsheetUrl.deleteMany(),
    (data: any[]) => prisma.fundFactsheetUrl.createMany({ data }),
  );
}

// ============================================================
// Main
// ============================================================

async function main() {
  console.log('🚀 SEC Fund Data Import');
  console.log(`📁 Data directory: ${DATA_DIR}`);
  console.log(`📅 Started at: ${new Date().toISOString()}\n`);

  const start = Date.now();

  // Import in dependency order
  await importAmcs();
  await importFunds();
  await importRiskSpectrums();
  await importStatistics();
  await importPerformances();
  await importDividendPolicies();
  await importTopHoldings();
  await importBenchmarks();
  await importSpecs();
  await importFactsheetUrls();

  // Print summary
  console.log('\n📊 Final counts:');
  const counts = await Promise.all([
    prisma.fundAmc.count().then(c => ({ table: 'FundAmc', count: c })),
    prisma.fund.count().then(c => ({ table: 'Fund', count: c })),
    prisma.fundRiskSpectrum.count().then(c => ({ table: 'FundRiskSpectrum', count: c })),
    prisma.fundStatistics.count().then(c => ({ table: 'FundStatistics', count: c })),
    prisma.fundPerformance.count().then(c => ({ table: 'FundPerformance', count: c })),
    prisma.fundDividendPolicy.count().then(c => ({ table: 'FundDividendPolicy', count: c })),
    prisma.fundTopHolding.count().then(c => ({ table: 'FundTopHolding', count: c })),
    prisma.fundBenchmark.count().then(c => ({ table: 'FundBenchmark', count: c })),
    prisma.fundSpec.count().then(c => ({ table: 'FundSpec', count: c })),
    prisma.fundFactsheetUrl.count().then(c => ({ table: 'FundFactsheetUrl', count: c })),
  ]);

  for (const { table, count } of counts) {
    console.log(`  ${table}: ${count.toLocaleString()} rows`);
  }

  const elapsed = ((Date.now() - start) / 1000).toFixed(1);
  console.log(`\n✅ Import completed in ${elapsed}s`);
}

main()
  .catch((e) => {
    console.error('❌ Import failed:', e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
