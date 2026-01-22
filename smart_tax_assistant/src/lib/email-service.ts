/**
 * Email Service - สำหรับส่งอีเมล OTP และ notifications
 * ใช้ AWS SES ในการส่งอีเมล (เปลี่ยนจาก SNS/SQS)
 */

import { sendEmailViaSES, isSESConfigured } from './aws-ses';
import { OTPPurpose } from './otp';
import { sendOTPEmailDev, sendWelcomeEmailDev } from './email-service-dev';

// Development mode: แสดง OTP ใน console แทนการส่งอีเมลจริง
const IS_DEV_MODE = process.env.NODE_ENV === 'development' && !isSESConfigured();

export interface SendOTPEmailOptions {
  to: string;
  otpCode: string;
  purpose: OTPPurpose;
  expiresInMinutes?: number;
}

/**
 * สร้าง HTML template สำหรับอีเมล OTP
 */
function createOTPEmailTemplate(
  otpCode: string,
  purpose: OTPPurpose,
  expiresInMinutes: number = 10
): { subject: string; html: string; text: string } {
  let subject = '';
  let title = '';
  let description = '';

  switch (purpose) {
    case OTPPurpose.EMAIL_VERIFICATION:
      subject = 'ยืนยันอีเมลของคุณ - Smart Tax Assistant';
      title = 'ยืนยันอีเมลของคุณ';
      description = 'กรุณากรอกรหัส OTP ด้านล่างเพื่อยืนยันอีเมลและเปิดใช้งานบัญชีของคุณ';
      break;

    case OTPPurpose.LOGIN_MFA:
      subject = 'รหัส OTP สำหรับเข้าสู่ระบบ - Smart Tax Assistant';
      title = 'ยืนยันการเข้าสู่ระบบ';
      description = 'กรุณากรอกรหัส OTP ด้านล่างเพื่อยืนยันการเข้าสู่ระบบของคุณ';
      break;

    case OTPPurpose.PASSWORD_RESET:
      subject = 'รหัส OTP สำหรับรีเซ็ตรหัสผ่าน - Smart Tax Assistant';
      title = 'รีเซ็ตรหัสผ่าน';
      description = 'กรุณากรอกรหัส OTP ด้านล่างเพื่อรีเซ็ตรหัสผ่านของคุณ';
      break;
  }

  const html = `
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${subject}</title>
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f5f5f5;
      margin: 0;
      padding: 0;
    }
    .container {
      max-width: 600px;
      margin: 40px auto;
      background-color: #ffffff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      overflow: hidden;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      text-align: center;
    }
    .header h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
    }
    .content {
      padding: 40px 30px;
      text-align: center;
    }
    .content p {
      color: #555;
      font-size: 16px;
      line-height: 1.6;
      margin-bottom: 30px;
    }
    .otp-box {
      background-color: #f8f9fa;
      border: 2px dashed #667eea;
      border-radius: 8px;
      padding: 30px;
      margin: 30px 0;
    }
    .otp-code {
      font-size: 48px;
      font-weight: bold;
      color: #667eea;
      letter-spacing: 10px;
      margin: 0;
      font-family: 'Courier New', monospace;
    }
    .expiry {
      color: #dc3545;
      font-size: 14px;
      margin-top: 15px;
    }
    .footer {
      background-color: #f8f9fa;
      padding: 20px 30px;
      text-align: center;
      color: #6c757d;
      font-size: 14px;
      border-top: 1px solid #e9ecef;
    }
    .security-notice {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin: 20px 0;
      text-align: left;
    }
    .security-notice p {
      margin: 0;
      color: #856404;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Smart Tax Assistant</h1>
    </div>

    <div class="content">
      <h2>${title}</h2>
      <p>${description}</p>

      <div class="otp-box">
        <p class="otp-code">${otpCode}</p>
        <p class="expiry">รหัสนี้จะหมดอายุใน ${expiresInMinutes} นาที</p>
      </div>

      <div class="security-notice">
        <p><strong>⚠️ คำเตือนด้านความปลอดภัย:</strong></p>
        <p>• อย่าแชร์รหัส OTP นี้กับใครก็ตาม</p>
        <p>• พนักงานของเราจะไม่ขอรหัส OTP จากคุณ</p>
        <p>• หากคุณไม่ได้ร้องขอรหัสนี้ กรุณาเพิกเฉยต่ออีเมลนี้</p>
      </div>
    </div>

    <div class="footer">
      <p>© ${new Date().getFullYear()} Smart Tax Assistant. All rights reserved.</p>
      <p>อีเมลนี้ถูกส่งแบบอัตโนมัติ กรุณาอย่าตอบกลับอีเมลนี้</p>
    </div>
  </div>
</body>
</html>
  `;

  const text = `
${title}

${description}

รหัส OTP ของคุณคือ: ${otpCode}

รหัสนี้จะหมดอายุใน ${expiresInMinutes} นาที

คำเตือนด้านความปลอดภัย:
- อย่าแชร์รหัส OTP นี้กับใครก็ตาม
- พนักงานของเราจะไม่ขอรหัส OTP จากคุณ
- หากคุณไม่ได้ร้องขอรหัสนี้ กรุณาเพิกเฉยต่ออีเมลนี้

© ${new Date().getFullYear()} Smart Tax Assistant
  `;

  return { subject, html, text };
}

/**
 * ส่งอีเมล OTP
 * @param options - ตัวเลือกสำหรับส่งอีเมล OTP
 */
export async function sendOTPEmail(options: SendOTPEmailOptions) {
  const { to, otpCode, purpose, expiresInMinutes = 10 } = options;

  // Development Mode: แสดง OTP ใน console
  if (IS_DEV_MODE) {
    console.log('⚠️  DEV MODE: OTP will be displayed in console (not sent via email)');
    return await sendOTPEmailDev(options);
  }

  // Production Mode: ส่งอีเมลจริงผ่าน AWS SES
  const { subject, html, text } = createOTPEmailTemplate(
    otpCode,
    purpose,
    expiresInMinutes
  );

  const emailMessage = {
    to,
    subject,
    body: text,
    html,
  };

  try {
    // ส่งตรงผ่าน AWS SES
    const result = await sendEmailViaSES(emailMessage);

    if (result.success) {
      console.log(`✅ OTP email sent successfully to ${to}`);
      if (result.messageId) {
        console.log(`   Message ID: ${result.messageId}`);
      }
      return {
        success: true,
        messageId: result.messageId,
      };
    } else {
      console.error(`❌ Failed to send OTP email to ${to}:`, result.error);
      return {
        success: false,
        error: result.error,
      };
    }
  } catch (error) {
    console.error('❌ Error in sendOTPEmail:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * ส่งอีเมลยินดีต้อนรับหลังจากยืนยันอีเมลสำเร็จ
 */
export async function sendWelcomeEmail(to: string, name: string) {
  // Development Mode
  if (IS_DEV_MODE) {
    return await sendWelcomeEmailDev(to, name);
  }

  // Production Mode
  const subject = 'ยินดีต้อนรับสู่ Smart Tax Assistant!';

  const html = `
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: 'Segoe UI', sans-serif; background-color: #f5f5f5; }
    .container { max-width: 600px; margin: 40px auto; background: white; border-radius: 8px; overflow: hidden; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
    .content { padding: 40px 30px; }
    .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 14px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>ยินดีต้อนรับ!</h1>
    </div>
    <div class="content">
      <h2>สวัสดีคุณ ${name}!</h2>
      <p>ยินดีต้อนรับสู่ Smart Tax Assistant</p>
      <p>บัญชีของคุณได้รับการยืนยันเรียบร้อยแล้ว คุณสามารถเริ่มใช้งานระบบได้ทันที</p>
      <p>ขอบคุณที่ไว้วางใจในบริการของเรา!</p>
    </div>
    <div class="footer">
      <p>© ${new Date().getFullYear()} Smart Tax Assistant</p>
    </div>
  </div>
</body>
</html>
  `;

  const text = `
ยินดีต้อนรับสู่ Smart Tax Assistant!

สวัสดีคุณ ${name}!

บัญชีของคุณได้รับการยืนยันเรียบร้อยแล้ว คุณสามารถเริ่มใช้งานระบบได้ทันที

ขอบคุณที่ไว้วางใจในบริการของเรา!

© ${new Date().getFullYear()} Smart Tax Assistant
  `;

  return await sendEmailViaSES({ to, subject, body: text, html });
}
