// src/app/api/user/financial-profile/route.ts
export const runtime = 'nodejs';

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import prisma from '@/lib/prisma';

// ---------- GET: ดึง Financial Profile สำหรับ AI Optimizer ----------
export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // ดึงข้อมูล User พร้อม Financial Profile
  const user = await prisma.user.findUnique({
    where: { email: session.user.email },
    select: {
      id: true,
      annualIncome: true,
      dateOfBirth: true,
      occupation: true,
      financialProfile: true,
    },
  });

  if (!user) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 });
  }

  // คำนวณอายุจาก dateOfBirth
  let age = 30; // default
  if (user.dateOfBirth) {
    const today = new Date();
    const birth = new Date(user.dateOfBirth);
    age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
  }

  const fp = user.financialProfile;

  return NextResponse.json({
    // ข้อมูลจาก User table
    annual_income: user.annualIncome ? Number(user.annualIncome) : 0,
    age: age,
    occupation: user.occupation || 'employee',

    // ข้อมูลจาก Financial Profile (ถ้ามี)
    monthly_expenses: fp?.monthlyExpenses ? Number(fp.monthlyExpenses) : 40000,
    existing_savings: fp?.existingSavings ? Number(fp.existingSavings) : 0,
    emergency_fund: fp?.emergencyFund ? Number(fp.emergencyFund) : 0,

    risk_tolerance: fp?.riskTolerance?.toLowerCase() || 'moderate',
    investment_horizon: fp?.investmentHorizon || 10,

    marital_status: fp?.maritalStatus?.toLowerCase() || 'single',
    has_spouse: fp?.maritalStatus === 'MARRIED',
    num_children: fp?.numChildren || 0,
    num_parents: fp?.numParents || 0,
    has_disability: fp?.hasDisability || false,

    // สิทธิลดหย่อนที่ใช้แล้ว
    current_deductions: {
      rmf: fp?.usedRmf ? Number(fp.usedRmf) : 0,
      ssf: fp?.usedSsf ? Number(fp.usedSsf) : 0,
      thai_esg: fp?.usedThaiEsg ? Number(fp.usedThaiEsg) : 0,
      life_insurance: fp?.usedLifeInsurance ? Number(fp.usedLifeInsurance) : 0,
      health_insurance: fp?.usedHealthInsurance ? Number(fp.usedHealthInsurance) : 0,
      pension_fund: fp?.usedPensionFund ? Number(fp.usedPensionFund) : 0,
      provident_fund: fp?.usedProvidentFund ? Number(fp.usedProvidentFund) : 0,
      social_security: fp?.usedSocialSecurity ? Number(fp.usedSocialSecurity) : 0,
    },

    // ข้อมูลฟอร์มลดหย่อนภาษีทั้งหมด
    tax_form_data: fp?.taxFormData || null,

    // Meta
    has_profile: !!fp,
    financial_goals: [],
  });
}

// ---------- POST: สร้างหรืออัพเดท Financial Profile ----------
export async function POST(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await req.json().catch(() => ({}));

  // ดึง User ID
  const user = await prisma.user.findUnique({
    where: { email: session.user.email },
    select: { id: true },
  });

  if (!user) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 });
  }

  // Map risk_tolerance string to enum
  const riskMap: Record<string, 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE'> = {
    conservative: 'CONSERVATIVE',
    moderate: 'MODERATE',
    aggressive: 'AGGRESSIVE',
  };

  // Map marital_status string to enum
  const maritalMap: Record<string, 'SINGLE' | 'MARRIED' | 'DIVORCED' | 'WIDOWED'> = {
    single: 'SINGLE',
    married: 'MARRIED',
    divorced: 'DIVORCED',
    widowed: 'WIDOWED',
  };

  // Upsert Financial Profile
  const fp = await prisma.userFinancialProfile.upsert({
    where: { userId: user.id },
    create: {
      userId: user.id,
      monthlyExpenses: body.monthly_expenses || null,
      existingSavings: body.existing_savings || null,
      emergencyFund: body.emergency_fund || null,
      riskTolerance: riskMap[body.risk_tolerance] || 'MODERATE',
      investmentHorizon: body.investment_horizon || null,
      maritalStatus: maritalMap[body.marital_status] || 'SINGLE',
      numChildren: body.num_children || 0,
      numParents: body.num_parents || 0,
      hasDisability: body.has_disability || false,
      usedRmf: body.current_deductions?.rmf || 0,
      usedSsf: body.current_deductions?.ssf || 0,
      usedThaiEsg: body.current_deductions?.thai_esg || 0,
      usedLifeInsurance: body.current_deductions?.life_insurance || 0,
      usedHealthInsurance: body.current_deductions?.health_insurance || 0,
      usedPensionFund: body.current_deductions?.pension_fund || 0,
      usedProvidentFund: body.current_deductions?.provident_fund || 0,
      usedSocialSecurity: body.current_deductions?.social_security || 0,
      taxFormData: body.tax_form_data ?? undefined,
    },
    update: {
      monthlyExpenses: body.monthly_expenses || null,
      existingSavings: body.existing_savings || null,
      emergencyFund: body.emergency_fund || null,
      riskTolerance: riskMap[body.risk_tolerance] || undefined,
      investmentHorizon: body.investment_horizon || null,
      maritalStatus: maritalMap[body.marital_status] || undefined,
      numChildren: body.num_children ?? undefined,
      numParents: body.num_parents ?? undefined,
      hasDisability: body.has_disability ?? undefined,
      usedRmf: body.current_deductions?.rmf ?? undefined,
      usedSsf: body.current_deductions?.ssf ?? undefined,
      usedThaiEsg: body.current_deductions?.thai_esg ?? undefined,
      usedLifeInsurance: body.current_deductions?.life_insurance ?? undefined,
      usedHealthInsurance: body.current_deductions?.health_insurance ?? undefined,
      usedPensionFund: body.current_deductions?.pension_fund ?? undefined,
      usedProvidentFund: body.current_deductions?.provident_fund ?? undefined,
      usedSocialSecurity: body.current_deductions?.social_security ?? undefined,
      taxFormData: body.tax_form_data ?? undefined,
    },
  });

  // อัพเดท annualIncome ใน User table ด้วย (ถ้าส่งมา)
  if (body.annual_income !== undefined) {
    await prisma.user.update({
      where: { id: user.id },
      data: { annualIncome: body.annual_income },
    });
  }

  return NextResponse.json({ ok: true, id: fp.id });
}
