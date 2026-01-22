/**
 * AWS SES Email Service - สำหรับส่งอีเมล OTP และ notifications
 * ใช้ SES แทน SNS เพื่อความยืดหยุ่นและไม่ต้อง subscribe email ล่วงหน้า
 */

import { SESClient, SendEmailCommand } from '@aws-sdk/client-ses';

// AWS Configuration
const AWS_REGION = process.env.AWS_REGION || 'ap-southeast-1';
const AWS_ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID;
const AWS_SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY;

// SES Configuration
const SES_FROM_EMAIL = process.env.AWS_SES_FROM_EMAIL || 'noreply@smarttax.com';
const SES_FROM_NAME = process.env.AWS_SES_FROM_NAME || 'Smart Tax Assistant';

if (!AWS_ACCESS_KEY_ID || !AWS_SECRET_ACCESS_KEY) {
  console.warn('⚠️  AWS credentials not configured - Email sending will fail');
}

// Initialize SES Client
const sesClient = new SESClient({
  region: AWS_REGION,
  credentials:
    AWS_ACCESS_KEY_ID && AWS_SECRET_ACCESS_KEY
      ? {
          accessKeyId: AWS_ACCESS_KEY_ID,
          secretAccessKey: AWS_SECRET_ACCESS_KEY,
        }
      : undefined,
});

export interface EmailMessage {
  to: string | string[];
  subject: string;
  body: string;
  html?: string;
}

/**
 * ส่งอีเมลผ่าน AWS SES
 * @param message - ข้อมูลอีเมลที่ต้องการส่ง
 * @returns Promise<{ success: boolean; messageId?: string; error?: string }>
 */
export async function sendEmailViaSES(message: EmailMessage) {
  try {
    // Validate configuration
    if (!AWS_ACCESS_KEY_ID || !AWS_SECRET_ACCESS_KEY) {
      console.error('❌ AWS credentials are not configured');
      return {
        success: false,
        error: 'AWS credentials not configured',
      };
    }

    // Convert recipients to array
    const recipients = Array.isArray(message.to) ? message.to : [message.to];

    // Create email params
    // Note: ใน SES Sandbox mode, ใช้แค่ email address โดยไม่มีชื่อ
    // เพื่อให้ตรงกับที่ verify ใน AWS Console
    const params = {
      Source: SES_FROM_EMAIL,
      Destination: {
        ToAddresses: recipients,
      },
      Message: {
        Subject: {
          Data: message.subject,
          Charset: 'UTF-8',
        },
        Body: {
          Text: {
            Data: message.body,
            Charset: 'UTF-8',
          },
          ...(message.html && {
            Html: {
              Data: message.html,
              Charset: 'UTF-8',
            },
          }),
        },
      },
    };

    // Send email via SES
    const command = new SendEmailCommand(params);
    const response = await sesClient.send(command);

    console.log(`✅ Email sent successfully via SES to ${recipients.join(', ')}`);
    console.log(`   Message ID: ${response.MessageId}`);

    return {
      success: true,
      messageId: response.MessageId,
    };
  } catch (error: any) {
    console.error('❌ Error sending email via SES:', error);

    // Provide helpful error messages
    let errorMessage = 'Failed to send email';

    if (error.name === 'MessageRejected') {
      errorMessage = 'Email was rejected by SES. Please verify the sender email address.';
    } else if (error.name === 'InvalidParameterValue') {
      errorMessage = 'Invalid email parameters. Please check email addresses.';
    } else if (error.message) {
      errorMessage = error.message;
    }

    return {
      success: false,
      error: errorMessage,
    };
  }
}

/**
 * ตรวจสอบว่า SES ได้รับการตั้งค่าแล้วหรือยัง
 */
export function isSESConfigured(): boolean {
  return !!(
    AWS_ACCESS_KEY_ID &&
    AWS_SECRET_ACCESS_KEY &&
    SES_FROM_EMAIL &&
    SES_FROM_EMAIL !== 'noreply@smarttax.com'
  );
}

/**
 * ดึงข้อมูล configuration ปัจจุบัน (สำหรับ debugging)
 */
export function getSESConfig() {
  return {
    region: AWS_REGION,
    fromEmail: SES_FROM_EMAIL,
    fromName: SES_FROM_NAME,
    isConfigured: isSESConfigured(),
    hasCredentials: !!(AWS_ACCESS_KEY_ID && AWS_SECRET_ACCESS_KEY),
  };
}
