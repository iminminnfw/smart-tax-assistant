// Tax Advisor Types for Tax Deduction Calculator

export interface TaxCalculationResult {
  gross_income: number;
  total_deductions?: number;
  taxable_income: number;
  tax_amount: number;
  net_income?: number;
  effective_tax_rate: number;
  requires_optimization?: boolean;
}

export interface AllocationItem {
  category: string;
  investment_amount: number;
  percentage: number;
  tax_saving: number;
  risk_level: string;
  pros: string[];
  cons: string[];
}

export interface InvestmentPlan {
  plan_id: string;
  plan_name: string;
  plan_type: string;
  description: string;
  total_investment: number;
  total_tax_saving: number;
  overall_risk: string;
  allocations: AllocationItem[];
}

export interface MultiplePlansResponse {
  plans: InvestmentPlan[];
}

export interface TaxCalculationResponse {
  tax_result: TaxCalculationResult;
  investment_plans: MultiplePlansResponse;
  no_tax_required?: boolean;
}
