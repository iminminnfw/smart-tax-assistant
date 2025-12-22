'use client';

import React, { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { InvestmentPlan } from '@/lib/tax-advisor/types';

interface MultiplePlansViewProps {
  plans: InvestmentPlan[];
}

const COLORS = [
  '#3B82F6', // Blue
  '#10B981', // Green
  '#F59E0B', // Amber
  '#EF4444', // Red
  '#8B5CF6', // Purple
  '#EC4899', // Pink
  '#14B8A6', // Teal
];

const getPlanColor = (planType: string): string => {
  const colorMap: Record<string, string> = {
    conservative: 'border-green-300 bg-green-50',
    moderate: 'border-blue-300 bg-blue-50',
    aggressive: 'border-red-300 bg-red-50',
  };
  return colorMap[planType] || 'border-gray-300 bg-gray-50';
};

const getRiskColor = (level: string): string => {
  const colorMap: Record<string, string> = {
    low: 'text-green-600 bg-green-100',
    medium: 'text-yellow-600 bg-yellow-100',
    high: 'text-red-600 bg-red-100',
  };
  return colorMap[level] || 'text-gray-600 bg-gray-100';
};

const getRiskText = (level: string): string => {
  const textMap: Record<string, string> = {
    low: 'ต่ำ',
    medium: 'กลาง',
    high: 'สูง',
  };
  return textMap[level] || level;
};

const MultiplePlansView: React.FC<MultiplePlansViewProps> = ({ plans }) => {
  const [selectedPlan, setSelectedPlan] = useState(0);

  const currentPlan = plans[selectedPlan];

  // เตรียมข้อมูลสำหรับ Pie Chart
  const chartData = currentPlan.allocations.map((item) => ({
    name: item.category,
    value: item.percentage,
    amount: item.investment_amount,
  }));

  const renderCustomizedLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
  }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="text-sm font-bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div className="space-y-8">
      {/* Tab Selector */}
      <div className="bg-white rounded-2xl shadow-xl p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">
          เลือกแผนการลงทุนที่เหมาะกับคุณ
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {plans.map((plan, index) => (
            <button
              key={plan.plan_id}
              onClick={() => setSelectedPlan(index)}
              className={`p-6 rounded-xl border-4 transition-all ${
                selectedPlan === index
                  ? `${getPlanColor(plan.plan_type)} border-opacity-100 shadow-lg`
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="text-left">
                <h3 className="text-xl font-bold text-gray-800 mb-2">
                  {plan.plan_name}
                </h3>
                <p className="text-sm text-gray-600 mb-4">{plan.description}</p>

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">เงินลงทุน:</span>
                    <span className="font-bold text-blue-600">
                      {plan.total_investment.toLocaleString()} ฿
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">ประหยัดภาษี:</span>
                    <span className="font-bold text-green-600">
                      {plan.total_tax_saving.toLocaleString()} ฿
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">ความเสี่ยง:</span>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${getRiskColor(
                        plan.overall_risk
                      )}`}
                    >
                      {getRiskText(plan.overall_risk)}
                    </span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Selected Plan Details */}
      <div className="bg-white rounded-2xl shadow-xl p-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            {currentPlan.plan_name}
          </h2>
          <p className="text-gray-600 mt-2">{currentPlan.description}</p>
        </div>

        {/* Summary */}
        <div className={`rounded-xl p-6 border-4 ${getPlanColor(currentPlan.plan_type)} mb-8`}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-600 mb-1">เงินลงทุนรวม</p>
              <p className="text-3xl font-bold text-blue-600">
                {currentPlan.total_investment.toLocaleString()} ฿
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">ประหยัดภาษีรวม</p>
              <p className="text-3xl font-bold text-green-600">
                {currentPlan.total_tax_saving.toLocaleString()} ฿
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">ความเสี่ยงโดยรวม</p>
              <p
                className={`inline-block px-4 py-2 rounded-full text-lg font-bold ${getRiskColor(
                  currentPlan.overall_risk
                )}`}
              >
                {getRiskText(currentPlan.overall_risk)}
              </p>
            </div>
          </div>
        </div>

        {/* Pie Chart */}
        <div className="mb-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4">
            การกระจายการลงทุน
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderCustomizedLabel}
                outerRadius={150}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number, name: string, props: any) => [
                  `${value.toFixed(1)}% (${props.payload.amount.toLocaleString()} บาท)`,
                  name,
                ]}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Allocations Details */}
        <div className="space-y-4">
          <h3 className="text-xl font-bold text-gray-800">
            รายละเอียดแต่ละประเภท
          </h3>
          {currentPlan.allocations.map((item, index) => (
            <div
              key={index}
              className="border-2 rounded-lg p-6 hover:shadow-lg transition-shadow"
              style={{ borderColor: COLORS[index % COLORS.length] }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <div>
                    <h4 className="text-lg font-bold">{item.category}</h4>
                  </div>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${getRiskColor(
                    item.risk_level
                  )}`}
                >
                  ความเสี่ยง: {getRiskText(item.risk_level)}
                </span>
              </div>

              {/* จำนวนเงิน */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="bg-gray-50 rounded p-3">
                  <p className="text-xs text-gray-600">จำนวนเงิน</p>
                  <p className="text-xl font-bold text-gray-800">
                    {item.investment_amount.toLocaleString()} ฿
                  </p>
                </div>
                <div className="bg-gray-50 rounded p-3">
                  <p className="text-xs text-gray-600">สัดส่วน</p>
                  <p className="text-xl font-bold text-gray-800">
                    {item.percentage.toFixed(1)}%
                  </p>
                </div>
                <div className="bg-green-50 rounded p-3">
                  <p className="text-xs text-gray-600">ประหยัดภาษี</p>
                  <p className="text-xl font-bold text-green-600">
                    {item.tax_saving.toLocaleString()} ฿
                  </p>
                </div>
              </div>

              {/* ข้อดีข้อเสีย */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 className="font-semibold text-green-700 mb-2">ข้อดี</h5>
                  <ul className="space-y-1">
                    {item.pros.map((pro, i) => (
                      <li key={i} className="text-sm text-gray-700 flex items-start">
                        <span className="text-green-500 mr-2">•</span>
                        {pro}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h5 className="font-semibold text-red-700 mb-2">ข้อเสีย</h5>
                  <ul className="space-y-1">
                    {item.cons.map((con, i) => (
                      <li key={i} className="text-sm text-gray-700 flex items-start">
                        <span className="text-red-500 mr-2">•</span>
                        {con}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Comparison Button */}
        <div className="mt-8 text-center">
          <p className="text-gray-600 mb-4">
            เลือกแผนด้านบนเพื่อเปรียบเทียบแผนอื่นๆ
          </p>
        </div>
      </div>
    </div>
  );
};

export default MultiplePlansView;
