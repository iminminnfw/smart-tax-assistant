// test-s3-connection.ts
/**
 * Quick test script to verify S3 configuration
 * Run with: npx ts-node test-s3-connection.ts
 */

import { S3Client, ListBucketsCommand } from "@aws-sdk/client-s3";
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load .env file
dotenv.config({ path: path.join(__dirname, '.env') });

async function testS3Connection() {
  console.log('🔍 Testing S3 Configuration...\n');

  // Check environment variables
  console.log('📋 Environment Variables:');
  console.log(`   AWS_ACCESS_KEY_ID: ${process.env.AWS_ACCESS_KEY_ID ? '✅ Set' : '❌ Missing'}`);
  console.log(`   AWS_SECRET_ACCESS_KEY: ${process.env.AWS_SECRET_ACCESS_KEY ? '✅ Set' : '❌ Missing'}`);
  console.log(`   AWS_REGION: ${process.env.AWS_REGION || '❌ Missing'}`);
  console.log(`   AWS_S3_BUCKET_NAME: ${process.env.AWS_S3_BUCKET_NAME || '❌ Missing'}`);
  console.log('');

  if (!process.env.AWS_ACCESS_KEY_ID || !process.env.AWS_SECRET_ACCESS_KEY) {
    console.error('❌ Missing required AWS credentials!');
    console.error('   Please add them to your .env file');
    process.exit(1);
  }

  // Test connection
  try {
    console.log('🔌 Testing connection to AWS...');

    const client = new S3Client({
      region: process.env.AWS_REGION || 'ap-southeast-1',
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
      },
    });

    const command = new ListBucketsCommand({});
    const response = await client.send(command);

    console.log('✅ Successfully connected to AWS!');
    console.log('');
    console.log('📦 Available Buckets:');

    if (response.Buckets && response.Buckets.length > 0) {
      response.Buckets.forEach((bucket) => {
        const isTargetBucket = bucket.Name === process.env.AWS_S3_BUCKET_NAME;
        console.log(`   ${isTargetBucket ? '→' : ' '} ${bucket.Name}${isTargetBucket ? ' ⭐ (configured)' : ''}`);
      });
    } else {
      console.log('   No buckets found');
    }

    console.log('');

    // Check if configured bucket exists
    const targetBucket = process.env.AWS_S3_BUCKET_NAME;
    if (targetBucket) {
      const bucketExists = response.Buckets?.some(b => b.Name === targetBucket);
      if (bucketExists) {
        console.log(`✅ Target bucket "${targetBucket}" exists!`);
      } else {
        console.log(`⚠️  Warning: Configured bucket "${targetBucket}" not found!`);
        console.log('   Please create it in AWS Console or update AWS_S3_BUCKET_NAME');
      }
    }

    console.log('');
    console.log('🎉 S3 Configuration Test Complete!');
    console.log('   You are ready to proceed to Phase 3.');

  } catch (error: any) {
    console.error('❌ Connection failed!');
    console.error('');
    console.error('Error details:', error.message);
    console.error('');
    console.error('Common issues:');
    console.error('   1. Invalid credentials (check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)');
    console.error('   2. IAM user lacks permissions (needs S3 access)');
    console.error('   3. Network connectivity issues');
    console.error('');
    process.exit(1);
  }
}

testS3Connection();
