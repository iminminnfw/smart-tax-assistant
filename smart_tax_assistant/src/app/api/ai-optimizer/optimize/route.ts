// src/app/api/ai-optimizer/optimize/route.ts
export const runtime = 'nodejs';
export const maxDuration = 2400; // 40 minutes - Ollama local LLM is slow

import { NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import http from 'http';

const API_BASE_URL = process.env.NEXT_PUBLIC_TAX_API_URL || 'http://localhost:8000';

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
    } = body;

    if (!profile || !goal) {
      return NextResponse.json(
        { error: 'Missing profile or goal' },
        { status: 400 }
      );
    }

    // ============================================================
    // Step 1: Query Prisma DB -> filter + score + rank funds
    // (Reused scoring logic from recommend-funds/route.ts)
    // ============================================================

    const riskTolerance: string = risk_tolerance;
    const fundTypes: string[] = fund_types;
    const limit: number = Math.min(top_n_funds, 20);

    // Map risk tolerance to risk spectrum range
    const minRisk =
      riskTolerance === 'conservative' ? 1
        : riskTolerance === 'aggressive' ? 7
          : 4; // moderate
    const maxRisk =
      riskTolerance === 'conservative' ? 3
        : riskTolerance === 'aggressive' ? 8
          : 6; // moderate

    // Find fund IDs that match the requested spec codes (RMF/TESG/etc.)
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
      // Filter by active status and risk spectrum
      const fundsWithRisk = await prisma.fund.findMany({
        where: {
          id: { in: eligibleFundIds },
          fundStatus: { in: ['Registered', 'IPO'] }, // DB stores full words, not SEC abbreviated codes
          riskSpectrums: {
            some: { riskSpectrum: { gte: minRisk, lte: maxRisk } },
          },
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

      // Only keep funds whose latest risk spectrum is within range
      const filteredFunds = fundsWithRisk.filter((f) => {
        const latestRisk = f.riskSpectrums[0]?.riskSpectrum;
        return latestRisk !== undefined && latestRisk >= minRisk && latestRisk <= maxRisk;
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

          if (validSharpe) score += stats.sharpeRatio! * 4;
          if (validAlpha) score += stats.alpha! * 3;
          if (validDrawdown) score += (100 + stats.maxDrawdown!) * 0.15;
          if (perf.perf3m !== null) score += perf.perf3m * 0.05;
          if (perf.perf1y !== null) score += perf.perf1y * 0.1;
          if (perf.perf3y !== null) score += perf.perf3y * 0.03;
          if (perf.perf5y !== null) score += perf.perf5y * 0.02;

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
            riskLabel: (fund.riskSpectrums[0]?.riskSpectrum || 0) <= 3 ? 'ต่ำ' : (fund.riskSpectrums[0]?.riskSpectrum || 0) <= 6 ? 'ปานกลาง' : 'สูง',
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

        // Sort: 1) funds with performance data first, 2) Sharpe ratio desc, 3) score desc
        scoredFunds.sort((a, b) => {
          const aHasPerf = a.performance.return3m !== null || a.performance.return1y !== null;
          const bHasPerf = b.performance.return3m !== null || b.performance.return1y !== null;
          if (bHasPerf && !aHasPerf) return 1;
          if (aHasPerf && !bHasPerf) return -1;
          const aSharpe = a.statistics.sharpeRatio;
          const bSharpe = b.statistics.sharpeRatio;
          if (bSharpe !== null && aSharpe === null) return 1;
          if (aSharpe !== null && bSharpe === null) return -1;
          if (aSharpe !== null && bSharpe !== null) return bSharpe - aSharpe;
          return b.score - a.score;
        });
        preFilteredFunds = scoredFunds.slice(0, limit);
      }
    }

    // ============================================================
    // Step 2: Send to Python Backend POST /api/ai-optimizer/optimize
    // ============================================================

    const backendPayload = {
      profile: {
        age: profile.age,
        annual_income: profile.annual_income,
        monthly_expenses: profile.monthly_expenses,
        existing_savings: 0,
        emergency_fund: profile.emergency_fund || 0,
        risk_tolerance: riskTolerance,
        occupation: 'employee',
        marital_status: profile.has_spouse ? 'married' : 'single',
        dependents: (profile.num_children || 0) + (profile.num_parents || 0),
        num_children: profile.num_children || 0,
        num_parents: profile.num_parents || 0,
        existing_rmf: profile.current_deductions?.rmf || 0,
        existing_thai_esg: profile.current_deductions?.thai_esg || 0,
        existing_insurance: Math.min(profile.current_deductions?.life_insurance || 0, 100000)
          + Math.min(profile.current_deductions?.health_insurance || 0, 25000),
        life_insurance_amount: profile.current_deductions?.life_insurance || 0,
        health_insurance_amount: profile.current_deductions?.health_insurance || 0,
        // Investment budget — auto-calculated by backend from income/expenses
        available_budget: null,
        // Retirement planning
        retirement_age: profile.retirement_age || null,
        // Goal-based planning
        savings_target: body.savings_target || null,
        plan_to_marry: body.plan_to_marry || false,
        income_growth_rate: body.income_growth_rate || 0,
      },
      goal,
      risk_tolerance: riskTolerance,
      fund_types: fundTypes,
      top_n_funds: limit,
      include_ai_explanation,
      pre_filtered_funds: preFilteredFunds,
    };

    const backendResult = await httpPost(
      `${API_BASE_URL}/api/ai-optimizer/optimize`,
      JSON.stringify(backendPayload),
      2_400_000 // 40 min timeout
    );

    if (backendResult.status >= 400) {
      console.error('Backend /optimize error:', backendResult.status, backendResult.data);
      return NextResponse.json(
        { error: 'Backend optimization failed', detail: backendResult.data },
        { status: backendResult.status }
      );
    }

    const backendData = backendResult.data;

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

    return NextResponse.json({
      success: true,
      // From backend
      ai_powered: backendData.ai_powered || false,
      profile_analysis: backendData.profile_analysis || null,
      tax_info: backendData.tax_info || null,
      scenarios: backendData.scenarios || [],
      overall_recommendation: backendData.overall_recommendation || '',
      disclaimer: backendData.disclaimer || '',
      // From Prisma DB (enriched)
      recommended_funds: enrichedFunds,
      meta: {
        total_eligible: eligibleFundIds.length,
        risk_tolerance: riskTolerance,
        max_risk_spectrum: maxRisk,
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
