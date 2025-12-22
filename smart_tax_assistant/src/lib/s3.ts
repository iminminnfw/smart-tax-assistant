// src/lib/s3.ts
/**
 * AWS S3 Utility Library
 * Handles file uploads, deletions, and signed URL generation for private S3 bucket
 *
 * Configuration: Uses environment variables
 * - AWS_ACCESS_KEY_ID
 * - AWS_SECRET_ACCESS_KEY
 * - AWS_REGION
 * - AWS_S3_BUCKET_NAME
 */

import {
  S3Client,
  PutObjectCommand,
  DeleteObjectCommand,
  HeadObjectCommand,
  GetObjectCommand
} from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

// ==================== TYPES ====================

export interface UploadResult {
  url: string;      // S3 URL (for private bucket, this is the base URL)
  key: string;      // S3 key (path in bucket)
  signedUrl: string; // Temporary signed URL for immediate access
}

export interface S3Config {
  accessKeyId: string;
  secretAccessKey: string;
  region: string;
  bucketName: string;
}

// ==================== CONFIGURATION ====================

/**
 * Validate and load S3 configuration from environment variables
 * Throws error if required variables are missing (fail fast)
 */
function loadS3Config(): S3Config {
  const config: S3Config = {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
    region: process.env.AWS_REGION || 'ap-southeast-1',
    bucketName: process.env.AWS_S3_BUCKET_NAME || '',
  };

  // Validate required fields
  const missing: string[] = [];
  if (!config.accessKeyId) missing.push('AWS_ACCESS_KEY_ID');
  if (!config.secretAccessKey) missing.push('AWS_SECRET_ACCESS_KEY');
  if (!config.bucketName) missing.push('AWS_S3_BUCKET_NAME');

  if (missing.length > 0) {
    throw new Error(
      `Missing required AWS environment variables: ${missing.join(', ')}\n` +
      'Please check your .env file and restart the server.'
    );
  }

  return config;
}

// Load config once on module initialization
let s3Config: S3Config;
try {
  s3Config = loadS3Config();
} catch (error: any) {
  console.error('S3_CONFIG_ERROR:', error.message);
  throw error;
}

/**
 * Get or create singleton S3 client instance
 * Reuses the same client for better performance
 */
let s3ClientInstance: S3Client | null = null;

function getS3Client(): S3Client {
  if (!s3ClientInstance) {
    s3ClientInstance = new S3Client({
      region: s3Config.region,
      credentials: {
        accessKeyId: s3Config.accessKeyId,
        secretAccessKey: s3Config.secretAccessKey,
      },
    });
  }
  return s3ClientInstance;
}

// ==================== UTILITY FUNCTIONS ====================

/**
 * Sanitize filename to prevent S3 key issues
 * - Supports Thai and Unicode characters
 * - Replace unsafe characters with underscores
 * - Keep alphanumeric (including Thai), dots, hyphens, underscores
 *
 * @param filename - Original filename
 * @returns Sanitized filename safe for S3
 */
function sanitizeFilename(filename: string): string {
  // Replace unsafe characters but preserve Unicode (Thai, etc.)
  // Remove: / \ : * ? " < > | and control characters
  const safe = filename
    .replace(/[\/\\:*?"<>|\x00-\x1F\x7F]/g, '_')
    .replace(/\s+/g, '_'); // Replace spaces with underscores

  // Remove leading/trailing underscores and dots
  return safe.replace(/^[._]+|[._]+$/g, '');
}

/**
 * Generate unique S3 key with organized folder structure
 * Format: {folder}/{userId}/{timestamp}_{sanitizedFilename}
 *
 * Examples:
 * - documents/cm123abc/1729147823456_tax_form.pdf
 * - profiles/cm456def/1729147891234_avatar.jpg
 *
 * @param userId - User ID from session
 * @param folder - "profiles" or "documents"
 * @param filename - Original filename
 * @returns S3 key string
 */
export function generateS3Key(
  userId: string,
  folder: 'profiles' | 'documents',
  filename: string
): string {
  const timestamp = Date.now();
  const sanitized = sanitizeFilename(filename);
  return `${folder}/${userId}/${timestamp}_${sanitized}`;
}

/**
 * Extract S3 key from full S3 URL
 * Example:
 *   "https://bucket.s3.region.amazonaws.com/documents/user/file.pdf"
 *   -> "documents/user/file.pdf"
 *
 * Handles URL-encoded keys (e.g., Thai characters)
 *
 * @param url - Full S3 URL or local path
 * @returns S3 key (decoded) or null if not S3 URL
 */
export function extractS3Key(url: string): string | null {
  if (!url) return null;

  // Check if it's an S3 URL
  if (!isS3Url(url)) return null;

  try {
    // Parse URL and extract pathname (everything after domain)
    const urlObj = new URL(url);
    // Remove leading slash and decode URI components
    const encodedKey = urlObj.pathname.substring(1);

    // Decode URL encoding (e.g., %E0%B8%9B -> ป)
    return decodeURIComponent(encodedKey);
  } catch (error) {
    console.error('Failed to extract/decode S3 key:', error);
    return null;
  }
}

/**
 * Check if URL is an S3 URL
 * Detects both:
 * - https://bucket.s3.region.amazonaws.com/key
 * - https://s3.region.amazonaws.com/bucket/key
 *
 * @param url - URL to check
 * @returns true if S3 URL, false if local path
 */
export function isS3Url(url: string): boolean {
  if (!url) return false;
  return url.includes('s3.amazonaws.com') || url.includes('.s3.');
}

/**
 * Get base S3 URL for a key
 * Used for database storage (not for direct access since bucket is private)
 *
 * Properly encodes keys with special characters (Thai, spaces, etc.)
 *
 * @param key - S3 key (unencoded UTF-8)
 * @returns Full S3 URL (with properly encoded key)
 */
function getS3Url(key: string): string {
  // Split key into parts and encode each part to handle Thai characters
  const parts = key.split('/');
  const encodedParts = parts.map(part => encodeURIComponent(part));
  const encodedKey = encodedParts.join('/');

  return `https://${s3Config.bucketName}.s3.${s3Config.region}.amazonaws.com/${encodedKey}`;
}

// ==================== UPLOAD OPERATIONS ====================

/**
 * Upload file buffer to S3
 * For private bucket: Returns both permanent URL and temporary signed URL
 *
 * @param buffer - File content as Buffer
 * @param key - S3 key (use generateS3Key to create)
 * @param contentType - MIME type (e.g., "image/jpeg", "application/pdf")
 * @returns Upload result with URLs
 * @throws Error if upload fails
 *
 * @example
 * const buffer = Buffer.from(await file.arrayBuffer());
 * const key = generateS3Key(userId, 'documents', file.name);
 * const result = await uploadToS3(buffer, key, file.type);
 * console.log('Uploaded:', result.url);
 */
export async function uploadToS3(
  buffer: Buffer,
  key: string,
  contentType: string,
  fileName?: string
): Promise<UploadResult> {
  try {
    const client = getS3Client();

    const command = new PutObjectCommand({
      Bucket: s3Config.bucketName,
      Key: key,
      Body: buffer,
      ContentType: contentType,
      // ServerSideEncryption: 'AES256', // Enable if you set up encryption
    });

    await client.send(command);

    const url = getS3Url(key);

    // Generate signed URL for immediate access (expires in 1 hour, inline for preview)
    // Use provided fileName or extract from key
    const displayName = fileName || key.split('/').pop() || 'download';
    const signedUrl = await getSignedUrlForKey(key, 3600, displayName, true);

    console.log(`S3_UPLOAD_SUCCESS: ${key}`);

    return {
      url,        // Permanent URL (for database storage)
      key,        // S3 key (for future operations)
      signedUrl,  // Temporary URL (for immediate access/preview)
    };
  } catch (error: any) {
    console.error('S3_UPLOAD_ERROR:', error);
    throw new Error(`Failed to upload to S3: ${error.message}`);
  }
}

// ==================== DELETE OPERATIONS ====================

/**
 * Delete file from S3
 * Handles non-existent files gracefully (no error thrown)
 *
 * @param key - S3 key of file to delete
 * @returns void
 *
 * @example
 * const oldKey = extractS3Key(user.image);
 * if (oldKey) {
 *   await deleteFromS3(oldKey);
 * }
 */
export async function deleteFromS3(key: string): Promise<void> {
  if (!key) {
    console.warn('S3_DELETE_SKIPPED: Empty key provided');
    return;
  }

  try {
    const client = getS3Client();

    // Check if file exists first (optional, for better logging)
    try {
      await client.send(new HeadObjectCommand({
        Bucket: s3Config.bucketName,
        Key: key,
      }));
    } catch (error: any) {
      if (error.name === 'NotFound' || error.$metadata?.httpStatusCode === 404) {
        console.log(`S3_DELETE_SKIPPED: File not found: ${key}`);
        return; // File doesn't exist, nothing to delete
      }
      // Other errors, continue with delete attempt
    }

    // Delete the file
    await client.send(new DeleteObjectCommand({
      Bucket: s3Config.bucketName,
      Key: key,
    }));

    console.log(`S3_DELETE_SUCCESS: ${key}`);
  } catch (error: any) {
    // Don't throw error for delete operations (graceful degradation)
    // Old files remain in S3 but won't break the application
    console.error('S3_DELETE_ERROR:', error.message, 'Key:', key);
  }
}

// ==================== SIGNED URL GENERATION ====================

/**
 * Encode filename for Content-Disposition header (RFC 2231)
 * Supports Thai and Unicode characters
 *
 * @param filename - Original filename
 * @returns Encoded filename string for Content-Disposition
 */
function encodeRFC2231(filename: string): string {
  // Encode filename using percent-encoding
  const encoded = encodeURIComponent(filename);
  // RFC 2231 format: filename*=UTF-8''encoded_filename
  return `UTF-8''${encoded}`;
}

/**
 * Generate temporary signed URL for private file access
 * Required for private S3 buckets to allow client access
 *
 * @param key - S3 key
 * @param expiresIn - URL expiration in seconds (default: 3600 = 1 hour)
 * @param fileName - Filename for download (supports Thai/Unicode)
 * @param inline - If true, opens in browser; if false, downloads file (default: true)
 * @returns Signed URL
 * @throws Error if generation fails
 *
 * @example
 * // For file preview (opens in browser)
 * const signedUrl = await getSignedUrlForKey(doc.fileUrl, 3600, 'เอกสาร.pdf', true);
 * res.json({ previewUrl: signedUrl });
 *
 * // For download
 * const downloadUrl = await getSignedUrlForKey(doc.fileUrl, 7200, 'เอกสาร.pdf', false);
 */
export async function getSignedUrlForKey(
  key: string,
  expiresIn: number = 3600,
  fileName: string,
  inline: boolean = true
): Promise<string> {
  try {
    const client = getS3Client();

    // Support Thai/Unicode filenames with RFC 2231 encoding
    const encodedFilename = encodeRFC2231(fileName);
    const type = inline ? 'inline' : 'attachment';
    const disposition = `${type}; filename*=${encodedFilename}`;

    // Use GetObjectCommand for generating download/view URLs
    const command = new GetObjectCommand({
      Bucket: s3Config.bucketName,
      Key: key,
      ResponseContentDisposition: disposition,
    });

    const signedUrl = await getSignedUrl(client, command, { expiresIn });
    return signedUrl;
  } catch (error: any) {
    console.error('S3_SIGNED_URL_ERROR:', error);
    throw new Error(`Failed to generate signed URL: ${error.message}`);
  }
}

/**
 * Generate signed URL from full S3 URL
 * Convenience wrapper that extracts key and generates signed URL
 *
 * @param url - Full S3 URL or local path
 * @param expiresIn - URL expiration in seconds (default: 3600)
 * @param fileName - Filename for download
 * @param inline - If true, opens in browser; if false, downloads file (default: true)
 * @returns Signed URL or original URL if not S3
 *
 * @example
 * const accessUrl = await getSignedUrlFromUrl(doc.fileUrl, 3600, 'doc.pdf', true);
 * res.json({ url: accessUrl });
 */
export async function getSignedUrlFromUrl(
  url: string,
  expiresIn: number = 3600,
  fileName: string,
  inline: boolean = true
): Promise<string> {
  // If not an S3 URL, return as-is (backward compatibility with local files)
  if (!isS3Url(url)) {
    return url;
  }

  const key = extractS3Key(url);
  if (!key) {
    throw new Error('Invalid S3 URL: Could not extract key');
  }

  return getSignedUrlForKey(key, expiresIn, fileName, inline);
}

// ==================== EXPORTS ====================

export default {
  uploadToS3,
  deleteFromS3,
  getSignedUrlForKey,
  getSignedUrlFromUrl,
  generateS3Key,
  extractS3Key,
  isS3Url,
};
