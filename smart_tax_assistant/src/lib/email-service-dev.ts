/**
 * Development Email Service - สำหรับทดสอบโดยไม่ต้องใช้ AWS
 * แสดง OTP ใน console แทนการส่งอีเมลจริง
 */

import { OTPPurpose } from './otp';

export interface SendOTPEmailOptions {
  to: string;
  otpCode: string;
  purpose: OTPPurpose;
  expiresInMinutes?: number;
}

/**
 * ส่ง OTP แบบ Development Mode (แสดงใน console)
 */
export async function sendOTPEmailDev(options: SendOTPEmailOptions) {
  const { to, otpCode, purpose, expiresInMinutes = 10 } = options;

  // สร้าง box สวยๆ ใน console
  const boxWidth = 60;
  const border = '═'.repeat(boxWidth);
  const space = ' '.repeat(boxWidth);

  console.log('\n');
  console.log('╔' + border + '╗');
  console.log('║' + ' '.repeat(boxWidth) + '║');
  console.log('║' + centerText('📧 OTP EMAIL (DEV MODE)', boxWidth) + '║');
  console.log('║' + ' '.repeat(boxWidth) + '║');
  console.log('╠' + border + '╣');
  console.log('║' + ' '.repeat(boxWidth) + '║');
  console.log('║  ' + padText(`To: ${to}`, boxWidth - 3) + '║');
  console.log('║  ' + padText(`Purpose: ${purpose}`, boxWidth - 3) + '║');
  console.log('║' + ' '.repeat(boxWidth) + '║');
  console.log('╠' + border + '╣');
  console.log('║' + ' '.repeat(boxWidth) + '║');
  console.log('║' + centerText('🔐 YOUR OTP CODE', boxWidth) + '║');
  console.log('║' + ' '.repeat(boxWidth) + '║');
  console.log('║' + centerText(`>>> ${otpCode} <<<`, boxWidth) + '║');
  console.log('║' + ' '.repeat(boxWidth) + '║');
  console.log('╠' + border + '╣');
  console.log('║' + ' '.repeat(boxWidth) + '║');
  console.log('║  ' + padText(`⏰ Expires in ${expiresInMinutes} minutes`, boxWidth - 3) + '║');
  console.log('║  ' + padText(`🕐 Time: ${new Date().toLocaleString('th-TH')}`, boxWidth - 3) + '║');
  console.log('║' + ' '.repeat(boxWidth) + '║');
  console.log('╚' + border + '╝');
  console.log('\n');

  // Return success (mock)
  return {
    success: true,
    messageId: `dev-mock-${Date.now()}`,
  };
}

function centerText(text: string, width: number): string {
  const padding = Math.max(0, width - text.length);
  const leftPad = Math.floor(padding / 2);
  const rightPad = padding - leftPad;
  return ' '.repeat(leftPad) + text + ' '.repeat(rightPad);
}

function padText(text: string, width: number): string {
  return text + ' '.repeat(Math.max(0, width - text.length));
}

/**
 * ส่งอีเมลต้อนรับแบบ Development Mode
 */
export async function sendWelcomeEmailDev(to: string, name: string) {
  console.log('\n╔═════════════════════════════════════════════════╗');
  console.log('║     📧 WELCOME EMAIL (DEV MODE)                ║');
  console.log('╠═════════════════════════════════════════════════╣');
  console.log(`║  To: ${to.padEnd(41)}║`);
  console.log(`║  Name: ${name.padEnd(39)}║`);
  console.log('║                                                 ║');
  console.log('║  ✅ Account verified successfully!             ║');
  console.log('║  🎉 Welcome to Smart Tax Assistant!            ║');
  console.log('╚═════════════════════════════════════════════════╝\n');

  return {
    success: true,
    messageId: `dev-welcome-${Date.now()}`,
  };
}
