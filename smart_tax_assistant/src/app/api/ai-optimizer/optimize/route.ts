// src/app/api/ai-optimizer/optimize/route.ts
export const runtime = 'nodejs';
export const maxDuration = 2400; // 40 minutes - Ollama local LLM is slow

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import prisma from '@/lib/prisma';
import http from 'http';
import fs from 'fs';
import path from 'path';

// ─── Dev Logger (เฉพาะ local dev เท่านั้น) ────────────────────────────────────
const DEV_LOGGING = process.env.NODE_ENV === 'development' && process.env.DEV_LOG === 'true';
const LOG_DIR = path.join(process.cwd(), 'dev-logs');
function devLog(label: string, data: any) {
  if (!DEV_LOGGING) return;
  try {
    if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });
    const date = new Date().toISOString().slice(0, 10);
    const time = new Date().toISOString().slice(11, 19);
    const logFile = path.join(LOG_DIR, `ai-optimizer-${date}.log`);
    const line = `\n${'='.repeat(80)}\n[${time}] ${label}\n${'='.repeat(80)}\n${JSON.stringify(data, null, 2)}\n`;
    fs.appendFileSync(logFile, line, 'utf-8');
    console.log(`[DEV-LOG] ${label} → ${logFile}`);
  } catch (e) {
    console.warn('[DEV-LOG] เขียน log ไม่ได้:', e);
  }
}
// ──────────────────────────────────────────────────────────────────────────────

const API_BASE_URL = process.env.TAX_API_URL || 'http://localhost:8000';

// ── คำนวณภาษีจาก tax_form_data โดยตรง (ไม่ต้อง call LLM) ──────────────────
function calcTaxFromFormData(f: Record<string, any>): { taxable_income: number; tax_amount: number; gross_income: number } | null {
  const g = Number(f.gross_income || 0);
  if (g <= 0) return null;

  // คำนวณค่าใช้จ่าย
  let exp = 0;
  if (f.expense_method === 'actual') {
    exp = Number(f.actual_expenses || 0);
  } else if (f.income_type === '40(6)') {
    exp = (f.profession_type === 'medical' || f.profession_type === 'fine_arts') ? g * 0.60 : g * 0.30;
  } else if (f.income_type === '40(8)') {
    if (f.business_type === 'entertainment') {
      exp = g <= 300000 ? g * 0.60 : Math.min(300000 * 0.60 + (g - 300000) * 0.40, 600000);
    } else {
      exp = g * 0.60;
    }
  }

  // caps ลดหย่อน
  const lifeHealthUsed = Math.min((Number(f.life_insurance||0) + Number(f.health_insurance||0)), 100000);
  const maxPen = Math.min(g * 0.15, 200000 + Math.max(0, 100000 - Math.min(Number(f.life_insurance||0), 100000)));
  const ssCap = f.social_security_type === '33' ? 9000 : f.social_security_type === '39' ? 5184 : f.social_security_type === '40' ? 3600 : 0;
  const maxEsg = Math.min(g * 0.30, 300000);
  const penUsed = Math.min(Number(f.pension_insurance||0), maxPen);
  const rmfUsed = Math.min(Number(f.rmf||0), Math.min(g * 0.30, 500000));
  const nsfUsed = Math.min(Number(f.nsf||0), 30000);
  const retScale = (penUsed + rmfUsed + nsfUsed) > 500000 ? 500000 / (penUsed + rmfUsed + nsfUsed) : 1;

  const family =
    (f.has_spouse ? 60000 : 0) +
    (Number(f.number_of_children_30k||0) * 30000) +
    (Number(f.number_of_children_60k||0) * 60000) +
    Math.min(Number(f.number_of_parents||0), 4) * 30000 +
    (Number(f.number_of_disabled_family||0) * 60000) +
    (f.has_disabled_other ? 60000 : 0) +
    Math.min(Number(f.maternity_expense||0), 60000);

  const deductSum =
    Math.round(rmfUsed * retScale) +
    Math.min(Number(f.thai_esg||0), maxEsg) +
    Math.min(Number(f.thai_esgx_new||0), maxEsg) +
    Math.min(Number(f.thai_esgx_ltf||0), maxEsg) +
    lifeHealthUsed +
    Math.round(penUsed * retScale) +
    Math.min(Number(f.health_insurance_parents_own||0) + Number(f.health_insurance_parents_spouse||0), 30000) +
    Math.min(Number(f.social_security||0), ssCap) +
    Math.round(nsfUsed * retScale) +
    Math.min(Number(f.easy_e_receipt||0), 50000) +
    Math.min(Number(f.home_loan_interest||0), 100000) +
    Math.min(Number(f.new_house_construction||0), 100000) +
    Math.min(Number(f.social_enterprise_investment||0), 100000);

  const baseForDonation = Math.max(0, g - exp - 60000 - family - deductSum);
  const maxDonation = Math.floor(baseForDonation * 0.10);
  const totalDonation =
    Math.min(Number(f.donation_general||0), maxDonation) +
    Math.min(Number(f.donation_education||0) * 2, maxDonation) +
    Math.min(Number(f.donation_political||0), 10000);

  const taxableIncome = Math.max(0, g - exp - 60000 - family - deductSum - totalDonation);

  // Progressive tax brackets
  const bs = [150000, 300000, 500000, 750000, 1000000, 2000000, 5000000];
  const rs = [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35];
  let taxProg = 0, prev = 0;
  for (let i = 0; i <= bs.length; i++) {
    const lim = bs[i] ?? Infinity;
    if (taxableIncome <= prev) break;
    taxProg += (Math.min(taxableIncome, lim) - prev) * rs[i];
    prev = lim;
  }
  taxProg = Math.round(taxProg);

  // มาตรา 48(2): 0.5% ของรายได้รวม
  const tax05 = Math.round(g * 0.005);
  const tax_amount = (tax05 > 5000 && tax05 > taxProg) ? tax05 : taxProg;

  return { taxable_income: taxableIncome, tax_amount, gross_income: g };
}

/**
 * HTTP POST with long timeout using Node.js http module.
 * Built-in fetch has a hardcoded 300s headers timeout (undici).
 */
function httpPost(url: string, body: string, timeoutMs: number): Promise<{ status: number; data: any }> {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const req = http.request(
      {
        hostname: parsed.hostname,
        port: parsed.port || 80,
        path: parsed.pathname + parsed.search,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
        },
        timeout: timeoutMs,
      },
      (res) => {
        let raw = '';
        res.on('data', (chunk) => (raw += chunk));
        res.on('end', () => {
          try {
            resolve({ status: res.statusCode || 500, data: JSON.parse(raw) });
          } catch {
            resolve({ status: res.statusCode || 500, data: raw });
          }
        });
      }
    );
    req.on('timeout', () => { req.destroy(); reject(new Error('Backend request timeout')); });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

/**
 * POST /api/ai-optimizer/optimize
 *
 * Unified AI Optimizer endpoint (Next.js middleware).
 *
 * Flow:
 *   1. Query Prisma DB -> filter + score + rank funds (reuse logic from recommend-funds)
 *   2. Send profile + goal + pre-filtered funds -> Python Backend POST /api/ai-optimizer/optimize
 *   3. Return combined response to frontend
 */
export async function POST(req: Request) {
  try {
    const body = await req.json();

    const {
      profile,
      goal,
      risk_tolerance = 'moderate',
      fund_types = ['RMF', 'TESG', 'TESGX'],
      top_n_funds = 5,
      include_ai_explanation = true,
      money_goal = 'mid_term',
      monthly_investment_budget = null,
      income_growth_rate = 0,
    } = body;

    if (!profile || !goal) {
      return NextResponse.json(
        { error: 'Missing profile or goal' },
        { status: 400 }
      );
    }

    // ============================================================
    // Step 0: ดึง tax_form_data จาก DB โดยตรง → POST ไป FastAPI คำนวณภาษี
    // ============================================================
    let pre_calculated_tax: { taxable_income: number; tax_amount: number; gross_income: number } | null = null;

    try {
      const session = await getServerSession(authOptions);
      if (session?.user?.email) {
        const user = await prisma.user.findUnique({
          where: { email: session.user.email },
          select: { financialProfile: { select: { taxFormData: true } } },
        });
        const taxFormData = user?.financialProfile?.taxFormData as Record<string, any> | null;
        if (taxFormData) {
          pre_calculated_tax = calcTaxFromFormData(taxFormData);
          if (pre_calculated_tax) {
            console.log('[Optimizer] ✅ pre_calculated_tax:', pre_calculated_tax);
          }
        }
      }
    } catch (e) {
      console.warn('[Optimizer] ไม่สามารถดึง tax_form_data:', e);
    }

    // ============================================================
    // Step 1: Query Prisma DB -> filter + score + rank funds
    // (Reused scoring logic from recommend-funds/route.ts)
    // ============================================================

    const riskTolerance: string = risk_tolerance;
    const fundTypes: string[] = fund_types;

    // Find fund IDs that match the requested spec codes (RMF/TESG/TESGX)
    const matchingSpecs = await prisma.fundSpec.findMany({
      where: { specCode: { in: fundTypes } },
      select: { fundId: true, specCode: true },
    });

    const fundIdToSpecMap = new Map<string, string>();
    for (const spec of matchingSpecs) {
      fundIdToSpecMap.set(spec.fundId, spec.specCode);
    }
    const eligibleFundIds = [...fundIdToSpecMap.keys()];

    let preFilteredFunds: any[] = [];

    if (eligibleFundIds.length > 0) {
      // Fetch ALL active funds (no risk filter) — we rank top 3 per type separately
      const allActiveFunds = await prisma.fund.findMany({
        where: {
          id: { in: eligibleFundIds },
          fundStatus: { in: ['Registered', 'IPO'] },
        },
        select: {
          id: true,
          projNameTh: true,
          projNameEn: true,
          projAbbrName: true,
          fundStatus: true,
          policyDesc: true,
          riskSpectrums: {
            orderBy: { endDate: 'desc' },
            take: 1,
            select: { riskSpectrum: true, riskSpectrumDesc: true },
          },
          amc: {
            select: { nameTh: true, nameEn: true },
          },
        },
      });

      // Hard filter ตาม risk_tolerance + fund type
      // Conservative: risk 1-3, Moderate: risk 4-6
      // Aggressive: RMF risk 7-8, TESG/TESGX risk 6 (สูงสุดที่มีในฐานข้อมูล)
      const filteredFunds = allActiveFunds.filter(f => {
        const specCode = fundIdToSpecMap.get(f.id) || '';
        const risk = f.riskSpectrums[0]?.riskSpectrum;
        if (!risk) return false;
        if (riskTolerance === 'conservative') return risk >= 1 && risk <= 3;
        if (riskTolerance === 'moderate') return risk >= 4 && risk <= 6;
        // aggressive
        if (specCode === 'RMF') return risk >= 7 && risk <= 8;
        return risk === 6; // TESG/TESGX: เฉพาะ risk 6 (สูงสุดที่มี)
      });

      if (filteredFunds.length > 0) {
        const filteredFundIds = filteredFunds.map((f) => f.id);

        // Get latest performance data (ไม่ filter performanceTypeDesc เพื่อให้ครอบคลุมมากขึ้น)
        const performances = await prisma.fundPerformance.findMany({
          where: {
            fundId: { in: filteredFundIds },
            referencePeriod: { in: ['3 months', '1 year', '3 years', '5 years'] },
          },
          orderBy: { endDate: 'desc' },
          select: {
            fundId: true,
            referencePeriod: true,
            performanceValue: true,
            endDate: true,
          },
        });

        // Group performance by fund
        const fundPerfMap = new Map<
          string,
          { perf3m: number | null; perf1y: number | null; perf3y: number | null; perf5y: number | null }
        >();
        for (const perf of performances) {
          if (!fundPerfMap.has(perf.fundId)) {
            fundPerfMap.set(perf.fundId, { perf3m: null, perf1y: null, perf3y: null, perf5y: null });
          }
          const entry = fundPerfMap.get(perf.fundId)!;
          const period = perf.referencePeriod.toLowerCase().trim();
          if (period === '3 months' && entry.perf3m === null) entry.perf3m = perf.performanceValue;
          else if (period === '1 year' && entry.perf1y === null) entry.perf1y = perf.performanceValue;
          else if (period === '3 years' && entry.perf3y === null) entry.perf3y = perf.performanceValue;
          else if (period === '5 years' && entry.perf5y === null) entry.perf5y = perf.performanceValue;
        }

        // Get latest statistics
        const statistics = await prisma.fundStatistics.findMany({
          where: { fundId: { in: filteredFundIds } },
          orderBy: { endDate: 'desc' },
          distinct: ['fundId'],
          select: {
            fundId: true,
            sharpeRatio: true,
            maxDrawdown: true,
            alpha: true,
            beta: true,
          },
        });

        const fundStatsMap = new Map<
          string,
          { sharpeRatio: number | null; maxDrawdown: number | null; alpha: number | null; beta: number | null }
        >();
        for (const stat of statistics) {
          fundStatsMap.set(stat.fundId, {
            sharpeRatio: stat.sharpeRatio,
            maxDrawdown: stat.maxDrawdown,
            alpha: stat.alpha,
            beta: stat.beta,
          });
        }

        // Target risk range ตาม risk_tolerance
        const targetMinRisk = riskTolerance === 'conservative' ? 1
          : riskTolerance === 'aggressive' ? 7 : 4;
        const targetMaxRisk = riskTolerance === 'conservative' ? 3
          : riskTolerance === 'aggressive' ? 8 : 6;

        // Score and rank funds
        const scoredFunds = filteredFunds.map((fund) => {
          const perf = fundPerfMap.get(fund.id) || { perf3m: null, perf1y: null, perf3y: null, perf5y: null };
          const stats = fundStatsMap.get(fund.id) || {
            sharpeRatio: null, maxDrawdown: null, alpha: null, beta: null,
          };

          let score = 0;
          const validSharpe = stats.sharpeRatio !== null && Math.abs(stats.sharpeRatio) < 100;
          const validAlpha = stats.alpha !== null && Math.abs(stats.alpha) < 100;
          const validDrawdown = stats.maxDrawdown !== null && Math.abs(stats.maxDrawdown) < 999;

          // Layer 1: Quant metrics
          if (validSharpe) score += stats.sharpeRatio! * 4;
          if (validAlpha) score += stats.alpha! * 3;
          if (validDrawdown) score += (100 + stats.maxDrawdown!) * 0.15;
          if (perf.perf3m !== null) score += perf.perf3m * 0.05;
          if (perf.perf1y !== null) score += perf.perf1y * 0.1;
          if (perf.perf3y !== null) score += perf.perf3y * 0.03;
          if (perf.perf5y !== null) score += perf.perf5y * 0.02;

          // Layer 2: Risk tolerance match bonus (สำคัญที่สุด — กำหนดว่า risk ระดับใดมาก่อน)
          const risk = fund.riskSpectrums[0]?.riskSpectrum || 0;
          if (risk >= targetMinRisk) {
            score += 20; // อยู่ใน target range
          } else if (risk >= targetMinRisk - 2) {
            score += 10 + (risk - (targetMinRisk - 2)) * 5; // ใกล้เคียง target
          } else {
            score += Math.max(0, risk * 0.5); // ต่ำกว่า target มาก
          }

          return {
            fundId: fund.id,
            abbr: fund.projAbbrName,
            nameTh: fund.projNameTh,
            nameEn: fund.projNameEn,
            amcNameTh: fund.amc.nameTh,
            amcNameEn: fund.amc.nameEn,
            fundType: fundIdToSpecMap.get(fund.id) || '',
            policyDesc: fund.policyDesc,
            riskSpectrum: fund.riskSpectrums[0]?.riskSpectrum || 0,
            riskLabel: (() => {
              const r = fund.riskSpectrums[0]?.riskSpectrum || 0;
              if (riskTolerance === 'aggressive' && r >= 6) return 'สูง';
              return r <= 3 ? 'ต่ำ' : r <= 6 ? 'ปานกลาง' : 'สูง';
            })(),
            performance: {
              return3m: perf.perf3m,
              return1y: perf.perf1y,
              return3y: perf.perf3y,
              return5y: perf.perf5y,
            },
            statistics: {
              sharpeRatio: stats.sharpeRatio,
              maxDrawdown: stats.maxDrawdown,
              alpha: stats.alpha,
              beta: stats.beta,
            },
            score: Math.round(score * 100) / 100,
          };
        });

        // Sort: score desc (รวม risk bonus แล้ว ทำให้ risk ที่เหมาะสมมาก่อนเสมอ)
        scoredFunds.sort((a, b) => b.score - a.score);
        // Take top 3 per fund type (RMF / TESG / TESGX) — แยกอิสระ ไม่ขึ้นกับ risk tolerance
        const rmfTop3 = scoredFunds.filter(f => f.fundType === 'RMF').slice(0, 3);
        const tesgTop3 = scoredFunds.filter(f => f.fundType === 'TESG').slice(0, 3);
        const tesgxTop3 = scoredFunds.filter(f => f.fundType === 'TESGX').slice(0, 3);
        preFilteredFunds = [...rmfTop3, ...tesgTop3, ...tesgxTop3];
      }
    }

    // ============================================================
    // Step 2: Send to Python Backend POST /api/ai-optimizer/optimize
    // ============================================================

    const backendPayload = {
      profile: {
        age: profile.age,
        annual_income: pre_calculated_tax?.gross_income || profile.annual_income,
        monthly_expenses: 0,
        existing_savings: 0,
        emergency_fund: 0,
        risk_tolerance: riskTolerance,
        occupation: profile.occupation || 'employee',
        marital_status: profile.has_spouse ? 'married' : 'single',
        dependents: profile.num_children || 0,
        num_children: profile.num_children || 0,
        num_parents: profile.num_parents || 0,
        existing_rmf: profile.existing_rmf || 0,
        existing_thai_esg: profile.existing_thai_esg || 0,
        existing_insurance: 0,
        life_insurance_amount: profile.current_deductions?.life_insurance || 0,
        health_insurance_amount: profile.current_deductions?.health_insurance || 0,
        monthly_budget: monthly_investment_budget || null,
        income_growth_rate: income_growth_rate || 0,
        money_goal: money_goal || 'mid_term',
      },
      goal,
      risk_tolerance: riskTolerance,
      fund_types: fundTypes,
      top_n_funds: preFilteredFunds.length,
      include_ai_explanation,
      pre_filtered_funds: preFilteredFunds,
      // ภาษีที่คำนวณถูกต้องจากหน้าการเงิน (ถ้ามี)
      pre_calculated_tax: pre_calculated_tax || null,
    };

    devLog('REQUEST → backend payload', backendPayload);

    const backendResult = await httpPost(
      `${API_BASE_URL}/api/ai-optimizer/optimize`,
      JSON.stringify(backendPayload),
      2_400_000 // 40 min timeout
    );

    if (backendResult.status >= 400) {
      console.error('Backend /optimize error:', backendResult.status, backendResult.data);
      const detail = typeof backendResult.data?.detail === 'string'
        ? backendResult.data.detail
        : typeof backendResult.data === 'string'
          ? backendResult.data
          : 'เกิดข้อผิดพลาดจาก backend';
      return NextResponse.json({ error: detail }, { status: backendResult.status });
    }

    const backendData = backendResult.data;

    devLog('RESPONSE ← backend raw', {
      status: backendResult.status,
      ai_powered: backendData.ai_powered,
      recommended_plan_keys: backendData.recommended_plan ? Object.keys(backendData.recommended_plan) : null,
      allocation: backendData.recommended_plan?.allocation,
      tax_saved: backendData.recommended_plan?.tax_saved,
      judge_result: backendData.recommended_plan?.judge_result,
    });

    // log full recommended_plan เพื่อหา key ที่ถูก
    devLog('RECOMMENDED_PLAN full', backendData.recommended_plan);

    const explanationData =
      backendData.recommended_plan?.explanation ||
      backendData.recommended_plan?.ai_explanation ||
      backendData.recommended_plan?.llm_explanation ||
      null;
    if (explanationData) {
      devLog('AI EXPLANATION (LLM output)', explanationData);
    }

    // ============================================================
    // Step 3: Combine and return response
    // ============================================================

    // Merge pre-filtered fund details (with top holdings) into response
    // Get top holdings for the returned funds
    const topFundIds = preFilteredFunds.map((f: any) => f.fundId);
    let fundHoldingsMap = new Map<string, { assetName: string; assetRatio: number | null }[]>();
    let fundFactsheetMap = new Map<string, { amcUrl: string | null; pdfUrl: string | null }>();

    if (topFundIds.length > 0) {
      const holdings = await prisma.fundTopHolding.findMany({
        where: { fundId: { in: topFundIds } },
        orderBy: [{ endDate: 'desc' }, { assetSeq: 'asc' }],
        select: {
          fundId: true,
          assetName: true,
          assetRatio: true,
          assetSeq: true,
          endDate: true,
        },
      });

      for (const h of holdings) {
        if (!fundHoldingsMap.has(h.fundId)) {
          fundHoldingsMap.set(h.fundId, []);
        }
        const list = fundHoldingsMap.get(h.fundId)!;
        if (list.length < 5) {
          list.push({ assetName: h.assetName, assetRatio: h.assetRatio });
        }
      }

      // Query factsheet URLs (latest per fund)
      const factsheets = await prisma.fundFactsheetUrl.findMany({
        where: { fundId: { in: topFundIds } },
        orderBy: { asOfDate: 'desc' },
        distinct: ['fundId'],
        select: {
          fundId: true,
          amcUrlFactsheet: true,
          pdfFactsheet: true,
        },
      });

      for (const fs of factsheets) {
        fundFactsheetMap.set(fs.fundId, {
          amcUrl: fs.amcUrlFactsheet,
          pdfUrl: fs.pdfFactsheet,
        });
      }
    }

    // Enrich funds with top holdings, factsheet URLs, and rank
    const enrichedFunds = preFilteredFunds.map((f: any, index: number) => ({
      rank: index + 1,
      ...f,
      riskLabelEn: f.riskSpectrum <= 3 ? 'Low' : f.riskSpectrum <= 6 ? 'Medium' : 'High',
      topHoldings: fundHoldingsMap.get(f.fundId) || [],
      factsheet: fundFactsheetMap.get(f.fundId) || { amcUrl: null, pdfUrl: null },
    }));

    // Enrich recommended_funds inside recommended_plan with topHoldings + factsheet
    const rawPlan = backendData.recommended_plan || null;
    let enrichedPlanFunds: any[] = [];
    if (rawPlan?.recommended_funds) {
      enrichedPlanFunds = (rawPlan.recommended_funds as any[]).map((f: any) => {
        const matched = enrichedFunds.find((ef: any) => ef.fundId === f.fundId);
        return matched ?? f;
      });
    }

    return NextResponse.json({
      success: true,
      // From backend
      ai_powered: backendData.ai_powered || false,
      profile_analysis: backendData.profile_analysis || null,
      tax_info: backendData.tax_info || null,
      recommended_plan: rawPlan
        ? { ...rawPlan, recommended_funds: enrichedPlanFunds }
        : null,
      disclaimer: backendData.disclaimer || '',
      // From Prisma DB (enriched) — full list for display
      recommended_funds: enrichedFunds,
      meta: {
        total_eligible: eligibleFundIds.length,
        risk_tolerance: riskTolerance,
        fund_types: fundTypes,
        funds_returned: enrichedFunds.length,
      },
    });
  } catch (err: any) {
    console.error('Optimize route error:', err);
    return NextResponse.json(
      { error: 'Optimization failed', detail: err.message },
      { status: 500 }
    );
  }
}
