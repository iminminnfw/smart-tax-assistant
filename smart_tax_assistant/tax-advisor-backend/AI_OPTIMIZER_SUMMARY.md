# AI Optimizer - สรุปฟีเจอร์หลัก

## วิสัยทัศน์
**"Generative Dashboard ที่วิเคราะห์และสร้างแผนภาษีให้คุณในคลิกเดียว"**

> **หมายเหตุ:** โปรเจกต์นี้เป็น **Generative Dashboard** (One-click Analysis) ไม่ใช่ Chatbot หรือ Conversational AI

---

## 4 เสาหลัก (4 Pillars)

### 1. Profile-Based Analysis
วิเคราะห์สถานะการเงินของผู้ใช้แบบ Dynamic

| ข้อมูลที่วิเคราะห์ | รายละเอียด |
|------------------|-----------|
| ข้อมูลพื้นฐาน | อายุ, อาชีพ, สถานะสมรส, จำนวนบุตร |
| ข้อมูลการเงิน | รายได้, ค่าใช้จ่าย, เงินออม, กองทุนฉุกเฉิน |
| สิทธิลดหย่อน | RMF, ThaiESG, ประกัน, ดอกเบี้ยบ้าน |
| ความเสี่ยง | Risk Tolerance, Investment Horizon |

---

### 2. Goal-Based Planning
รับเป้าหมายจากภาษาธรรมชาติ แปลงเป็น Structured Goal

| ประเภทเป้าหมาย | ตัวอย่าง |
|--------------|---------|
| Tax Saving | "อยากประหยัดภาษี 80,000 บาท" |
| Cash Flow | "ต้องมีเงินเหลือ 300,000/ปี" |
| Life Event | "จะซื้อบ้าน 5 ล้าน ใน 3 ปี" |
| Retirement | "อยากเกษียณอายุ 55" |
| Hybrid | "ประหยัดภาษีสูงสุด + ซื้อบ้านใน 2 ปี" |

---

### 3. SEC API Integration
ดึงข้อมูลกองทุนจาก ก.ล.ต. แบบ Real-time

| API | ข้อมูล |
|-----|-------|
| API 3 | Specifications (ตรวจจับ Feeder Fund) |
| API 6 | Factsheet URLs (PDF ทางการ) |
| API 8 | Benchmark (ดัชนีอ้างอิง) |
| API 12 | Statistics (Alpha, Beta, Sharpe) |
| API 13 | Dividend Policy (Y/N) |
| API 15 | Performance (1Y/3Y/5Y returns) |
| API 20 | Daily NAV (มูลค่าล่าสุด) |

---

### 4. AI Engine
สร้างคำแนะนำเฉพาะบุคคลพร้อมอธิบายเหตุผล

**ความสามารถหลัก:**
- Goal Parser: แปลงภาษาพูดเป็น Structured Data
- Dynamic Scenario Generator: สร้าง 3 สถานการณ์ที่ปรับตามผู้ใช้
- Reasoning Transparency: แสดงเหตุผลว่าทำไมถึงแนะนำแบบนี้

---

## 4 Intelligence Layers (ใหม่)

### Layer 1: True Exposure Intelligence
ตรวจจับ Feeder Fund และความเสี่ยงที่ซ่อนอยู่

| ตรวจจับ | รายละเอียด |
|--------|-----------|
| CIV | กองทุนรวมที่ลงทุนในกองทุนอื่น |
| FIF | ลงทุนในต่างประเทศ (FX Risk) |
| FOF | Fund of Funds (ค่าธรรมเนียม 2 ชั้น) |
| Master Fund | ARK, BlackRock, Vanguard ฯลฯ |

---

### Layer 2: Relative Performance Intelligence
วิเคราะห์ Alpha/Beta พร้อม Benchmark Context

| ค่า | ความหมาย |
|-----|---------|
| Alpha > 0 | ชนะ Benchmark |
| Alpha < 0 | แพ้ Benchmark |
| Beta < 1 | ผันผวนน้อยกว่าตลาด |
| Beta > 1 | ผันผวนมากกว่าตลาด |
| Sharpe > 1 | Risk-adjusted return ดี |

---

### Layer 3: Tax Trap Intelligence
วิเคราะห์นโยบายเงินปันผลเพื่อประสิทธิภาพภาษี

| นโยบาย | คำแนะนำ |
|--------|--------|
| N (Accumulating) | แนะนำสำหรับผู้มีรายได้สูง - ไม่เสียภาษีปันผล 10% |
| Y (Distributing) | ระวัง Tax Leakage สำหรับฐานภาษี 25%+ |

---

### Layer 4: Trust & Compliance Intelligence
แนบหลักฐานทางการจาก ก.ล.ต.

| หลักฐาน | รายละเอียด |
|---------|-----------|
| PDF Factsheet | ลิงก์เอกสารทางการ |
| Data Freshness | ความสดของข้อมูล (<45 วัน) |
| Disclaimers | คำเตือนตามกฎหมาย |

---

## ฟีเจอร์เด่น

| ฟีเจอร์ | สถานะ |
|--------|-------|
| One-Click Analysis Dashboard | ✅ พร้อมใช้ |
| Dynamic Scenario Generation | ✅ พร้อมใช้ |
| What-If Simulator | ✅ พร้อมใช้ |
| Fund Recommendation with Scoring | ✅ พร้อมใช้ |
| 4 Intelligence Layers | ✅ พร้อมใช้ |
| Smart Calendar & Reminders | ❌ ยังไม่พัฒนา |
| Tax Projection Timeline (5 ปี) | ❌ ยังไม่พัฒนา |
| Portfolio Health Check | ❌ ยังไม่พัฒนา |

---

## กฎภาษีไทย 2568

| ประเภท | เพดาน | หมายเหตุ |
|--------|-------|---------|
| RMF | 30% ของรายได้ (สูงสุด 500,000) | รวมกับกองทุนสำรองเลี้ยงชีพ |
| ThaiESG | 30% ของรายได้ (สูงสุด 300,000) | แยกจาก RMF |
| SSF | ❌ หมดสิทธิ์ | สิ้นสุด 31 ธ.ค. 2567 |

---

## Competitive Advantage

| ด้าน | คู่แข่ง | Smart Tax AI |
|------|--------|-------------|
| คำแนะนำ | เหมือนกันทุกคน | Personalized ตาม Profile |
| Data Source | Static/Manual | SEC API Real-time |
| Goal Setting | Dropdown | ภาษาธรรมชาติ |
| Scenarios | Fixed 3-5 แบบ | Dynamic ตามเงื่อนไขจริง |
| Analysis | Manual | One-Click Dashboard |
| Explanation | ไม่มี | Full Transparency |

---

*สรุปจาก AI_OPTIMIZER_VISION.md*
*Version: 1.0 | January 2568*
