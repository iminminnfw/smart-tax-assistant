// src/app/api/ai-optimizer/recommend-funds/route.ts
export const runtime = 'nodejs';

import { NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

/**
 * POST /api/ai-optimizer/recommend-funds
 *
 * Query SEC fund data from PostgreSQL and return top 5 recommended funds.
 * Filters by: fund type (RMF/ThaiESG/ThaiESGX), risk level, active status
 * Sorts by: best historical performance (latest period)
 *
 * Risk mapping:
 *   conservative → risk spectrum 1-3
 *   moderate     → risk spectrum 1-6
 *   aggressive   → risk spectrum 1-8
 */
export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));

    const riskTolerance: string = body.risk_tolerance || 'moderate';
    const fundTypes: string[] = body.fund_types || ['RMF', 'TESG', 'TESGX'];
    const limit: number = Math.min(body.limit || 5, 20);

    // Map risk tolerance to max risk spectrum
    const maxRisk = riskTolerance === 'conservative' ? 3
      : riskTolerance === 'aggressive' ? 8
      : 6; // moderate

    // Step 1: Find fund IDs that match the requested spec codes (RMF/TESG/etc.)
    const matchingSpecs = await prisma.fundSpec.findMany({
      where: {
        specCode: { in: fundTypes },
      },
      select: { fundId: true, specCode: true },
    });

    const fundIdToSpecMap = new Map<string, string>();
    for (const spec of matchingSpecs) {
      fundIdToSpecMap.set(spec.fundId, spec.specCode);
    }
    const eligibleFundIds = [...fundIdToSpecMap.keys()];

    if (eligibleFundIds.length === 0) {
      return NextResponse.json({ funds: [], message: 'No funds found for the given types' });
    }

    // Step 2: Filter by active status and get latest risk spectrum within max risk
    const fundsWithRisk = await prisma.fund.findMany({
      where: {
        id: { in: eligibleFundIds },
        fundStatus: { in: ['Registered', 'IPO'] }, // active funds only (DB uses full words)
        riskSpectrums: {
          some: {
            riskSpectrum: { lte: maxRisk },
          },
        },
      },
      select: {
        id: true,
        projNameTh: true,
        projNameEn: true,
        projAbbrName: true,
        fundStatus: true,
        policyDesc: true,
        investmentPolicyDesc: true,
        taxIncentiveType: true,
        riskSpectrums: {
          orderBy: { endDate: 'desc' },
          take: 1,
          select: {
            riskSpectrum: true,
            riskSpectrumDesc: true,
          },
        },
        amc: {
          select: {
            nameTh: true,
            nameEn: true,
          },
        },
      },
    });

    // Filter: only keep funds whose latest risk spectrum is within max
    const filteredFunds = fundsWithRisk.filter(f => {
      const latestRisk = f.riskSpectrums[0]?.riskSpectrum;
      return latestRisk !== undefined && latestRisk <= maxRisk;
    });

    if (filteredFunds.length === 0) {
      return NextResponse.json({ funds: [], message: 'No funds match the risk criteria' });
    }

    const filteredFundIds = filteredFunds.map(f => f.id);

    // Step 3: Get latest performance data for each fund
    // We want the best performing funds, using latest period performance values
    const performances = await prisma.fundPerformance.findMany({
      where: {
        fundId: { in: filteredFundIds },
        performanceTypeDesc: 'ผลตอบแทนกองทุนรวม', // fund return, not volatility or benchmark
      },
      orderBy: { endDate: 'desc' },
      select: {
        fundId: true,
        referencePeriod: true,
        performanceValue: true,
        endDate: true,
      },
    });

    // Group by fund, get latest end date per fund, then score
    const fundPerfMap = new Map<string, { perf1y: number | null; perf3y: number | null; perf5y: number | null; latestDate: Date | null }>();

    for (const perf of performances) {
      if (!fundPerfMap.has(perf.fundId)) {
        fundPerfMap.set(perf.fundId, { perf1y: null, perf3y: null, perf5y: null, latestDate: null });
      }
      const entry = fundPerfMap.get(perf.fundId)!;

      // Track latest date
      if (!entry.latestDate || perf.endDate > entry.latestDate) {
        entry.latestDate = perf.endDate;
      }

      // Map reference periods (values: "1 year", "3 years", "5 years")
      const period = perf.referencePeriod.toLowerCase().trim();
      if (period === '1 year') {
        if (entry.perf1y === null) entry.perf1y = perf.performanceValue;
      } else if (period === '3 years') {
        if (entry.perf3y === null) entry.perf3y = perf.performanceValue;
      } else if (period === '5 years') {
        if (entry.perf5y === null) entry.perf5y = perf.performanceValue;
      }
    }

    // Step 4: Get latest statistics (sharpe ratio) for ranking
    const statistics = await prisma.fundStatistics.findMany({
      where: {
        fundId: { in: filteredFundIds },
      },
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

    const fundStatsMap = new Map<string, { sharpeRatio: number | null; maxDrawdown: number | null; alpha: number | null; beta: number | null }>();
    for (const stat of statistics) {
      fundStatsMap.set(stat.fundId, {
        sharpeRatio: stat.sharpeRatio,
        maxDrawdown: stat.maxDrawdown,
        alpha: stat.alpha,
        beta: stat.beta,
      });
    }

    // Step 5: Score and rank funds
    // Score = weighted combination of performance and risk-adjusted metrics
    type ScoredFund = {
      id: string;
      score: number;
      fund: typeof filteredFunds[0];
      specCode: string;
      perf: { perf1y: number | null; perf3y: number | null; perf5y: number | null };
      stats: { sharpeRatio: number | null; maxDrawdown: number | null; alpha: number | null; beta: number | null };
    };

    const scoredFunds: ScoredFund[] = filteredFunds.map(fund => {
      const perf = fundPerfMap.get(fund.id) || { perf1y: null, perf3y: null, perf5y: null, latestDate: null };
      const stats = fundStatsMap.get(fund.id) || { sharpeRatio: null, maxDrawdown: null, alpha: null, beta: null };

      // Scoring: use statistics as primary (most RMF/TESG funds lack performance data)
      // Filter out sentinel values (999.99) from SEC data
      let score = 0;
      const validSharpe = stats.sharpeRatio !== null && Math.abs(stats.sharpeRatio) < 100;
      const validAlpha = stats.alpha !== null && Math.abs(stats.alpha) < 100;
      const validDrawdown = stats.maxDrawdown !== null && Math.abs(stats.maxDrawdown) < 999;

      // Primary: Sharpe Ratio (risk-adjusted return) - weight 40%
      if (validSharpe) score += stats.sharpeRatio! * 4;
      // Secondary: Alpha (excess return over benchmark) - weight 30%
      if (validAlpha) score += stats.alpha! * 3;
      // Tertiary: Max Drawdown (less negative is better) - weight 15%
      if (validDrawdown) score += (100 + stats.maxDrawdown!) * 0.15; // convert to positive metric
      // If performance data exists, use it - weight 15%
      if (perf.perf1y !== null) score += perf.perf1y * 0.1;
      if (perf.perf3y !== null) score += perf.perf3y * 0.03;
      if (perf.perf5y !== null) score += perf.perf5y * 0.02;

      return {
        id: fund.id,
        score,
        fund,
        specCode: fundIdToSpecMap.get(fund.id) || '',
        perf: { perf1y: perf.perf1y, perf3y: perf.perf3y, perf5y: perf.perf5y },
        stats,
      };
    });

    // Sort by score descending, take top N
    scoredFunds.sort((a, b) => b.score - a.score);
    const topFunds = scoredFunds.slice(0, limit);

    // Step 6: Get top holdings for the selected funds
    const topFundIds = topFunds.map(f => f.id);
    const holdings = await prisma.fundTopHolding.findMany({
      where: {
        fundId: { in: topFundIds },
      },
      orderBy: [{ endDate: 'desc' }, { assetSeq: 'asc' }],
      select: {
        fundId: true,
        assetName: true,
        assetRatio: true,
        assetSeq: true,
        endDate: true,
      },
    });

    // Get latest holdings per fund
    const fundHoldingsMap = new Map<string, { assetName: string; assetRatio: number | null }[]>();
    for (const h of holdings) {
      if (!fundHoldingsMap.has(h.fundId)) {
        fundHoldingsMap.set(h.fundId, []);
      }
      const list = fundHoldingsMap.get(h.fundId)!;
      if (list.length < 5) { // only keep top 5
        list.push({ assetName: h.assetName, assetRatio: h.assetRatio });
      }
    }

    // Step 7: Format response
    const riskLabel = (level: number) =>
      level <= 3 ? 'ต่ำ' : level <= 6 ? 'ปานกลาง' : 'สูง';

    const riskLabelEn = (level: number) =>
      level <= 3 ? 'Low' : level <= 6 ? 'Medium' : 'High';

    const result = topFunds.map((sf, index) => {
      const risk = sf.fund.riskSpectrums[0]?.riskSpectrum || 0;
      return {
        rank: index + 1,
        fundId: sf.id,
        abbr: sf.fund.projAbbrName,
        nameTh: sf.fund.projNameTh,
        nameEn: sf.fund.projNameEn,
        amcNameTh: sf.fund.amc.nameTh,
        amcNameEn: sf.fund.amc.nameEn,
        fundType: sf.specCode, // RMF, TESG, TESGX
        policyDesc: sf.fund.policyDesc,
        riskSpectrum: risk,
        riskLabel: riskLabel(risk),
        riskLabelEn: riskLabelEn(risk),
        performance: {
          return1y: sf.perf.perf1y,
          return3y: sf.perf.perf3y,
          return5y: sf.perf.perf5y,
        },
        statistics: {
          sharpeRatio: sf.stats.sharpeRatio,
          maxDrawdown: sf.stats.maxDrawdown,
          alpha: sf.stats.alpha,
          beta: sf.stats.beta,
        },
        topHoldings: fundHoldingsMap.get(sf.id) || [],
        score: Math.round(sf.score * 100) / 100,
      };
    });

    return NextResponse.json({
      funds: result,
      meta: {
        total_eligible: filteredFunds.length,
        risk_tolerance: riskTolerance,
        max_risk_spectrum: maxRisk,
        fund_types: fundTypes,
      },
    });
  } catch (err: any) {
    console.error('Fund recommendation error:', err);
    return NextResponse.json(
      { error: 'Failed to get fund recommendations', detail: err.message },
      { status: 500 }
    );
  }
}
