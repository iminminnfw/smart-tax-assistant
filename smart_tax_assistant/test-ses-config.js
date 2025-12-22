// ไฟล์ทดสอบ configuration ของ AWS SES
// วิธีรัน: node test-ses-config.js

require('dotenv').config();

const AWS_ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID;
const AWS_SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY;
const AWS_REGION = process.env.AWS_REGION;
const AWS_SES_FROM_EMAIL = process.env.AWS_SES_FROM_EMAIL || 'noreply@smarttax.com';
const AWS_SES_FROM_NAME = process.env.AWS_SES_FROM_NAME || 'Smart Tax Assistant';

function isSESConfigured() {
  return !!(
    AWS_ACCESS_KEY_ID &&
    AWS_SECRET_ACCESS_KEY &&
    AWS_SES_FROM_EMAIL &&
    AWS_SES_FROM_EMAIL !== 'noreply@smarttax.com'
  );
}

console.log('='.repeat(60));
console.log('📧 AWS SES Configuration Status');
console.log('='.repeat(60));
console.log('');

console.log('Environment Variables:');
console.log('├─ AWS_ACCESS_KEY_ID:', AWS_ACCESS_KEY_ID ? '✅ Set (' + AWS_ACCESS_KEY_ID.substring(0, 8) + '...)' : '❌ Not set');
console.log('├─ AWS_SECRET_ACCESS_KEY:', AWS_SECRET_ACCESS_KEY ? '✅ Set (hidden)' : '❌ Not set');
console.log('├─ AWS_REGION:', AWS_REGION || '❌ Not set');
console.log('├─ AWS_SES_FROM_EMAIL:', AWS_SES_FROM_EMAIL);
console.log('└─ AWS_SES_FROM_NAME:', AWS_SES_FROM_NAME);
console.log('');

console.log('Configuration Status:');
console.log('├─ isSESConfigured():', isSESConfigured() ? '✅ true' : '❌ false');
console.log('└─ Is using default email?:', AWS_SES_FROM_EMAIL === 'noreply@smarttax.com' ? '⚠️ YES (using default)' : '✅ NO (custom email set)');
console.log('');

const NODE_ENV = process.env.NODE_ENV || 'development';
const IS_DEV_MODE = NODE_ENV === 'development' && !isSESConfigured();

console.log('Email Sending Mode:');
console.log('├─ NODE_ENV:', NODE_ENV);
console.log('├─ IS_DEV_MODE:', IS_DEV_MODE ? '⚠️ true (OTP in console)' : '✅ false (real emails via SES)');
console.log('└─ Email will be sent via:', IS_DEV_MODE ? 'Console (Development)' : 'AWS SES (Production)');
console.log('');

if (!isSESConfigured()) {
  console.log('⚠️  WARNING:');
  console.log('AWS SES is NOT properly configured.');
  console.log('');
  console.log('Missing configuration:');
  if (!AWS_ACCESS_KEY_ID) console.log('  ❌ AWS_ACCESS_KEY_ID not set');
  if (!AWS_SECRET_ACCESS_KEY) console.log('  ❌ AWS_SECRET_ACCESS_KEY not set');
  if (AWS_SES_FROM_EMAIL === 'noreply@smarttax.com') {
    console.log('  ❌ AWS_SES_FROM_EMAIL is using default value');
    console.log('     Please set a custom email in .env file');
  }
  console.log('');
  console.log('📝 Action required:');
  console.log('1. Set AWS_SES_FROM_EMAIL in your .env file');
  console.log('2. Verify the email address in AWS SES Console');
  console.log('3. Restart your application');
} else {
  console.log('✅ SUCCESS:');
  console.log('AWS SES is properly configured!');
  console.log('');
  console.log('📧 Email will be sent from:');
  console.log('   ' + AWS_SES_FROM_NAME + ' <' + AWS_SES_FROM_EMAIL + '>');
  console.log('');
  console.log('⚠️  Important reminders:');
  console.log('1. Make sure "' + AWS_SES_FROM_EMAIL + '" is VERIFIED in AWS SES Console');
  console.log('2. In Sandbox mode, recipient emails must also be verified');
  console.log('3. Check AWS SES Console at: https://console.aws.amazon.com/ses/');
}

console.log('');
console.log('='.repeat(60));
