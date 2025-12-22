/**
 * AWS Messaging Service - SQS และ SNS สำหรับส่งอีเมล OTP
 */

import { SQSClient, SendMessageCommand } from '@aws-sdk/client-sqs';
import { SNSClient, PublishCommand } from '@aws-sdk/client-sns';

// AWS Configuration
const AWS_REGION = process.env.AWS_REGION || 'ap-southeast-1';
const AWS_ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID;
const AWS_SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY;

// SQS Configuration
const SQS_QUEUE_URL = process.env.AWS_SQS_QUEUE_URL;

// SNS Configuration
const SNS_TOPIC_ARN = process.env.AWS_SNS_TOPIC_ARN;

if (!AWS_ACCESS_KEY_ID || !AWS_SECRET_ACCESS_KEY) {
  console.warn('AWS credentials not configured');
}

// Initialize AWS Clients
const sqsClient = new SQSClient({
  region: AWS_REGION,
  credentials:
    AWS_ACCESS_KEY_ID && AWS_SECRET_ACCESS_KEY
      ? {
          accessKeyId: AWS_ACCESS_KEY_ID,
          secretAccessKey: AWS_SECRET_ACCESS_KEY,
        }
      : undefined,
});

const snsClient = new SNSClient({
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
  to: string;
  subject: string;
  body: string;
  html?: string;
}

/**
 * ส่งข้อความไป SQS Queue
 * ใช้สำหรับ async email sending
 */
export async function sendToSQS(message: EmailMessage) {
  if (!SQS_QUEUE_URL || SQS_QUEUE_URL === 'YOUR_SQS_QUEUE_URL_HERE' || SQS_QUEUE_URL === 'SKIP_SQS') {
    console.error('SQS Queue URL not configured');
    return {
      success: false,
      error: 'SQS Queue URL not configured',
    };
  }

  try {
    const command = new SendMessageCommand({
      QueueUrl: SQS_QUEUE_URL,
      MessageBody: JSON.stringify(message),
      MessageAttributes: {
        MessageType: {
          DataType: 'String',
          StringValue: 'OTP_EMAIL',
        },
        To: {
          DataType: 'String',
          StringValue: message.to,
        },
        Subject: {
          DataType: 'String',
          StringValue: message.subject,
        },
      },
    });

    const response = await sqsClient.send(command);

    console.log(`✅ Message sent to SQS: ${response.MessageId}`);

    return {
      success: true,
      messageId: response.MessageId,
    };
  } catch (error) {
    console.error('❌ Error sending message to SQS:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * ส่งอีเมลผ่าน SNS
 * SNS สามารถส่งไปยัง email subscribers โดยตรง
 */
export async function sendEmailViaSNS(message: EmailMessage) {
  if (!SNS_TOPIC_ARN || SNS_TOPIC_ARN === 'YOUR_SNS_TOPIC_ARN_HERE') {
    console.error('SNS Topic ARN not configured');
    return {
      success: false,
      error: 'SNS Topic ARN not configured',
    };
  }

  try {
    // ใช้ text body สำหรับ email (SNS email subscription ไม่รองรับ HTML)
    const emailBody = `
${message.subject}

${message.body}

---
Smart Tax Assistant
    `.trim();

    const command = new PublishCommand({
      TopicArn: SNS_TOPIC_ARN,
      Subject: message.subject,
      Message: emailBody,
      MessageAttributes: {
        email: {
          DataType: 'String',
          StringValue: message.to,
        },
        messageType: {
          DataType: 'String',
          StringValue: 'OTP_EMAIL',
        },
      },
    });

    const response = await snsClient.send(command);

    console.log(`✅ Email sent via SNS: ${response.MessageId}`);

    return {
      success: true,
      messageId: response.MessageId,
    };
  } catch (error) {
    console.error('❌ Error sending email via SNS:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * ส่งอีเมลแบบ hybrid: SQS + SNS
 * - ส่งไป SQS เพื่อ queue message (reliable, async)
 * - SQS จะ trigger SNS (ต้อง subscribe SQS to SNS ใน AWS Console)
 * - SNS ส่งอีเมลไปยัง subscribers
 */
export async function sendEmailViaQueue(message: EmailMessage) {
  // ลองส่งผ่าน SQS ก่อน
  const sqsResult = await sendToSQS(message);

  if (sqsResult.success) {
    console.log('📬 Email queued in SQS successfully');
    return sqsResult;
  }

  // ถ้า SQS ไม่ได้ตั้งค่าหรือล้มเหลว → Fallback ส่งตรงผ่าน SNS
  console.warn('⚠️  SQS failed, falling back to direct SNS');
  return await sendEmailViaSNS(message);
}

/**
 * ส่งอีเมลโดยตรงผ่าน SNS (bypass SQS)
 */
export async function sendEmailDirect(message: EmailMessage) {
  return await sendEmailViaSNS(message);
}
