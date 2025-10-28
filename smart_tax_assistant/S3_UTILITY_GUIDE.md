# S3 Utility Library Guide

Complete documentation for `src/lib/s3.ts` - AWS S3 integration for Smart Tax Assistant

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Functions Reference](#functions-reference)
3. [Usage Examples](#usage-examples)
4. [Error Handling](#error-handling)
5. [Best Practices](#best-practices)
6. [Testing](#testing)

---

## Overview

### What This Library Does

- ✅ Uploads files to private S3 bucket
- ✅ Generates signed URLs for secure access (required for private buckets)
- ✅ Deletes files from S3
- ✅ Manages S3 keys with organized folder structure
- ✅ Handles errors gracefully following codebase patterns

### File Organization in S3

```
smart-tax-assistant-uploads/
├── documents/
│   ├── {userId1}/
│   │   ├── 1729147823456_tax_form_2024.pdf
│   │   ├── 1729147891234_receipt.jpg
│   │   └── 1729147923789_w2_form.pdf
│   └── {userId2}/
│       └── 1729150023456_invoice.pdf
└── profiles/
    ├── {userId1}/
    │   └── 1729148923456_avatar.jpg
    └── {userId2}/
        └── 1729149023456_photo.png
```

### Configuration

Automatically loads from environment variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `AWS_S3_BUCKET_NAME`

**Fails fast** if variables are missing (throws error on import).

---

## Functions Reference

### 🔑 generateS3Key()

**Generate unique S3 key with organized folder structure**

```typescript
function generateS3Key(
  userId: string,
  folder: 'profiles' | 'documents',
  filename: string
): string
```

**Parameters**:
- `userId`: User ID from session
- `folder`: `"profiles"` or `"documents"`
- `filename`: Original filename (will be sanitized)

**Returns**: S3 key string

**Examples**:
```typescript
generateS3Key('cm123abc', 'documents', 'tax form 2024.pdf')
// → "documents/cm123abc/1729147823456_tax_form_2024.pdf"

generateS3Key('cm456def', 'profiles', 'my avatar.jpg')
// → "profiles/cm456def/1729148923456_my_avatar.jpg"
```

**Features**:
- Timestamp prefix for uniqueness
- Sanitizes filename (removes special chars, spaces → underscores)
- Organized by folder type and user

---

### ⬆️ uploadToS3()

**Upload file buffer to S3 and get access URLs**

```typescript
async function uploadToS3(
  buffer: Buffer,
  key: string,
  contentType: string
): Promise<UploadResult>

interface UploadResult {
  url: string;       // Permanent S3 URL (for database)
  key: string;       // S3 key (for delete operations)
  signedUrl: string; // Temporary signed URL (for immediate access)
}
```

**Parameters**:
- `buffer`: File content as Buffer
- `key`: S3 key (use `generateS3Key()`)
- `contentType`: MIME type (e.g., `"image/jpeg"`, `"application/pdf"`)

**Returns**: `UploadResult` object with 3 properties

**Example**:
```typescript
// In API route
const file = form.get("file") as File;
const bytes = Buffer.from(await file.arrayBuffer());

const key = generateS3Key(userId, 'documents', file.name);
const result = await uploadToS3(bytes, key, file.type);

// Save to database
await prisma.documentFile.create({
  data: {
    userId,
    fileUrl: result.url,        // Permanent URL
    fileName: file.name,
    // ...
  }
});

// Return signed URL to client for immediate preview
return NextResponse.json({
  ok: true,
  url: result.signedUrl  // Temporary URL (1 hour expiration)
});
```

**Why Two URLs?**
- `url`: Permanent base URL → Save to database
- `signedUrl`: Temporary access URL → Send to client for preview

**Error Handling**:
```typescript
try {
  const result = await uploadToS3(buffer, key, contentType);
} catch (error: any) {
  console.error('Upload failed:', error.message);
  return NextResponse.json({ error: 'Upload failed' }, { status: 500 });
}
```

---

### 🗑️ deleteFromS3()

**Delete file from S3 (graceful, won't throw on missing files)**

```typescript
async function deleteFromS3(key: string): Promise<void>
```

**Parameters**:
- `key`: S3 key to delete

**Returns**: `void` (always succeeds)

**Features**:
- Checks if file exists first
- No error thrown if file doesn't exist (idempotent)
- Logs errors but doesn't throw (graceful degradation)

**Example**:
```typescript
// Delete old profile image before uploading new one
const user = await prisma.user.findUnique({
  where: { id: userId },
  select: { image: true }
});

if (user.image) {
  const oldKey = extractS3Key(user.image);
  if (oldKey) {
    await deleteFromS3(oldKey); // Safe even if already deleted
  }
}
```

---

### 🔗 getSignedUrlForKey()

**Generate temporary signed URL for private file access**

```typescript
async function getSignedUrlForKey(
  key: string,
  expiresIn?: number  // Default: 3600 (1 hour)
): Promise<string>
```

**Parameters**:
- `key`: S3 key
- `expiresIn`: Expiration in seconds (default: 3600 = 1 hour)

**Returns**: Signed URL string

**Use Cases**:

| Use Case | Expiration | Example |
|----------|-----------|---------|
| File preview | 1 hour (3600s) | Document viewer |
| Download link | 2 hours (7200s) | Email attachments |
| Temporary share | 24 hours (86400s) | Share with accountant |

**Example**:
```typescript
// API route for file preview
export async function GET(req: NextRequest) {
  const { userId } = await requireUserId();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { searchParams } = new URL(req.url);
  const fileId = searchParams.get('fileId');

  const file = await prisma.documentFile.findFirst({
    where: { id: fileId, userId }
  });

  if (!file) return NextResponse.json({ error: "Not found" }, { status: 404 });

  // Generate signed URL for preview
  const key = extractS3Key(file.fileUrl);
  if (!key) return NextResponse.json({ error: "Invalid file" }, { status: 400 });

  const signedUrl = await getSignedUrlForKey(key, 3600); // 1 hour

  return NextResponse.json({ url: signedUrl });
}
```

---

### 🔗 getSignedUrlFromUrl()

**Convenience wrapper - generates signed URL from full S3 URL**

```typescript
async function getSignedUrlFromUrl(
  url: string,
  expiresIn?: number  // Default: 3600
): Promise<string>
```

**Parameters**:
- `url`: Full S3 URL or local path
- `expiresIn`: Expiration in seconds

**Returns**: Signed URL (or original URL if not S3)

**Benefits**:
- Backward compatible with local files
- Auto-detects S3 URLs
- Extracts key automatically

**Example**:
```typescript
// Works with both S3 and local files
const file = await prisma.documentFile.findUnique({ where: { id } });

// If local file: returns "/uploads/user/file.pdf"
// If S3 file: returns signed URL
const accessUrl = await getSignedUrlFromUrl(file.fileUrl);

return NextResponse.json({ url: accessUrl });
```

---

### 🔍 extractS3Key()

**Extract S3 key from full URL**

```typescript
function extractS3Key(url: string): string | null
```

**Parameters**:
- `url`: Full S3 URL or local path

**Returns**: S3 key or `null` if not S3 URL

**Example**:
```typescript
const url = "https://bucket.s3.ap-southeast-1.amazonaws.com/documents/user/file.pdf";
const key = extractS3Key(url);
// → "documents/user/file.pdf"

// Local path
const localUrl = "/uploads/user/file.pdf";
const key2 = extractS3Key(localUrl);
// → null
```

---

### ✅ isS3Url()

**Check if URL is an S3 URL**

```typescript
function isS3Url(url: string): boolean
```

**Parameters**:
- `url`: URL to check

**Returns**: `true` if S3 URL, `false` if local

**Example**:
```typescript
isS3Url("https://bucket.s3.region.amazonaws.com/key")  // → true
isS3Url("/uploads/user/file.pdf")                      // → false
isS3Url("https://example.com/file.pdf")                // → false
```

---

## Usage Examples

### Example 1: Upload Document File

```typescript
// src/app/api/upload/route.ts
import { uploadToS3, generateS3Key } from "@/lib/s3";

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let userId = (session.user as any).id;
  if (!userId && session.user.email) {
    const u = await prisma.user.findUnique({
      where: { email: session.user.email },
      select: { id: true },
    });
    userId = u?.id;
  }
  if (!userId) {
    return NextResponse.json({ error: "No user id" }, { status: 401 });
  }

  try {
    const form = await req.formData();
    const file = form.get("file") as File;
    if (!file) return NextResponse.json({ error: "Missing file" }, { status: 400 });

    // Convert to Buffer
    const bytes = Buffer.from(await file.arrayBuffer());

    // Generate S3 key
    const s3Key = generateS3Key(userId, 'documents', file.name);

    // Upload to S3
    const s3Result = await uploadToS3(bytes, s3Key, file.type);

    // Save to database
    const doc = await prisma.documentFile.create({
      data: {
        userId,
        name: file.name,
        fileUrl: s3Result.url,  // Permanent URL
        fileName: file.name,
        fileSize: file.size,
        mimeType: file.type,
        isUploaded: true,
      },
    });

    return NextResponse.json({
      ok: true,
      id: doc.id,
      url: s3Result.signedUrl,  // Signed URL for preview
      document: doc
    });

  } catch (err: any) {
    console.error("UPLOAD_ERROR", err);
    return NextResponse.json({ error: err.message || "Upload failed" }, { status: 500 });
  }
}
```

---

### Example 2: Upload Profile Image

```typescript
// src/app/api/profile/image/route.ts
import { uploadToS3, generateS3Key, deleteFromS3, extractS3Key } from "@/lib/s3";

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let userId = (session.user as any).id;
  if (!userId && session.user.email) {
    const u = await prisma.user.findUnique({
      where: { email: session.user.email },
      select: { id: true },
    });
    userId = u?.id;
  }
  if (!userId) {
    return NextResponse.json({ error: "No user id" }, { status: 401 });
  }

  try {
    const form = await req.formData();
    const file = form.get("file") as File;
    if (!file) return NextResponse.json({ error: "Missing file" }, { status: 400 });

    // Validate image
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      return NextResponse.json({ error: "Only JPG, PNG, WEBP allowed" }, { status: 400 });
    }

    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      return NextResponse.json({ error: "File too large (max 5MB)" }, { status: 400 });
    }

    // Delete old profile image
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { image: true },
    });

    if (user?.image) {
      const oldKey = extractS3Key(user.image);
      if (oldKey) {
        await deleteFromS3(oldKey);
      }
    }

    // Upload new image
    const bytes = Buffer.from(await file.arrayBuffer());
    const s3Key = generateS3Key(userId, 'profiles', file.name);
    const s3Result = await uploadToS3(bytes, s3Key, file.type);

    // Update database
    await prisma.user.update({
      where: { id: userId },
      data: { image: s3Result.url },
    });

    return NextResponse.json({
      ok: true,
      imageUrl: s3Result.signedUrl,  // Signed URL for immediate display
    });

  } catch (err: any) {
    console.error("PROFILE_IMAGE_UPLOAD_ERROR", err);
    return NextResponse.json({ error: err.message || "Upload failed" }, { status: 500 });
  }
}
```

---

### Example 3: Get File for Preview

```typescript
// src/app/api/document/[id]/preview/route.ts
import { getSignedUrlFromUrl } from "@/lib/s3";

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let userId = (session.user as any).id;
  if (!userId && session.user.email) {
    const u = await prisma.user.findUnique({
      where: { email: session.user.email },
      select: { id: true },
    });
    userId = u?.id;
  }
  if (!userId) {
    return NextResponse.json({ error: "No user id" }, { status: 401 });
  }

  try {
    const file = await prisma.documentFile.findFirst({
      where: { id, userId }
    });

    if (!file) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    // Generate signed URL (works for both S3 and local files)
    const accessUrl = await getSignedUrlFromUrl(file.fileUrl, 3600);

    return NextResponse.json({
      id: file.id,
      name: file.name,
      url: accessUrl,  // Signed URL if S3, original if local
      mimeType: file.mimeType,
    });

  } catch (err: any) {
    console.error("FILE_PREVIEW_ERROR", err);
    return NextResponse.json({ error: "Failed to get preview" }, { status: 500 });
  }
}
```

---

## Error Handling

### Module Initialization Errors

```typescript
// If env vars are missing, error is thrown on import
try {
  import { uploadToS3 } from '@/lib/s3';
} catch (error) {
  // Error: Missing required AWS environment variables: AWS_ACCESS_KEY_ID, AWS_S3_BUCKET_NAME
}
```

**Solution**: Add variables to `.env` and restart server

---

### Upload Errors

```typescript
try {
  const result = await uploadToS3(buffer, key, contentType);
} catch (error: any) {
  // Possible errors:
  // - Network errors
  // - Invalid credentials
  // - Bucket permissions
  // - Bucket doesn't exist

  console.error('S3_UPLOAD_ERROR:', error);
  // Always includes context: "Failed to upload to S3: {original error}"
}
```

---

### Delete Errors

```typescript
await deleteFromS3(key);
// Never throws errors!
// Logs errors to console but continues execution
```

**Philosophy**: Deleting files is best-effort. Failed deletes won't break the app.

---

### Signed URL Errors

```typescript
try {
  const signedUrl = await getSignedUrlForKey(key, 3600);
} catch (error: any) {
  // Possible errors:
  // - Invalid key
  // - File doesn't exist
  // - Permissions issue

  console.error('S3_SIGNED_URL_ERROR:', error);
  // Includes context: "Failed to generate signed URL: {original error}"
}
```

---

## Best Practices

### 1. Always Use generateS3Key()

❌ **Bad**:
```typescript
const key = `documents/${userId}/${file.name}`;  // No timestamp, no sanitization
```

✅ **Good**:
```typescript
const key = generateS3Key(userId, 'documents', file.name);
```

---

### 2. Delete Old Files Before Upload

❌ **Bad**:
```typescript
// Upload new image without deleting old one
const result = await uploadToS3(buffer, key, contentType);
await prisma.user.update({ where: { id: userId }, data: { image: result.url } });
```

✅ **Good**:
```typescript
// Delete old image first
const user = await prisma.user.findUnique({ where: { id: userId }, select: { image: true } });
if (user?.image) {
  const oldKey = extractS3Key(user.image);
  if (oldKey) await deleteFromS3(oldKey);
}

// Then upload new one
const result = await uploadToS3(buffer, key, contentType);
await prisma.user.update({ where: { id: userId }, data: { image: result.url } });
```

---

### 3. Use Signed URLs for Client Access

❌ **Bad** (private bucket):
```typescript
// Client can't access this URL directly
return NextResponse.json({ url: s3Result.url });
```

✅ **Good**:
```typescript
// Use signed URL for client access
return NextResponse.json({ url: s3Result.signedUrl });
```

---

### 4. Store Permanent URL in Database

❌ **Bad**:
```typescript
// Signed URL expires after 1 hour!
await prisma.documentFile.create({
  data: { fileUrl: s3Result.signedUrl }  // Will break after expiration
});
```

✅ **Good**:
```typescript
// Store permanent URL, generate signed URL when needed
await prisma.documentFile.create({
  data: { fileUrl: s3Result.url }  // Permanent
});

// Later, when client needs access:
const signedUrl = await getSignedUrlFromUrl(doc.fileUrl);
```

---

### 5. Handle Both S3 and Local Files

✅ **Good** (backward compatible):
```typescript
// Works with both old local files and new S3 files
const accessUrl = await getSignedUrlFromUrl(file.fileUrl);
// If local: returns "/uploads/user/file.pdf"
// If S3: returns signed URL
```

---

## Testing

### Manual Test: Upload File

```bash
# Test upload endpoint
curl -X POST http://localhost:3000/api/upload \
  -H "Cookie: next-auth.session-token=YOUR_SESSION_TOKEN" \
  -F "file=@/path/to/test.pdf" \
  -F "type=TAX_FORM"

# Expected response:
{
  "ok": true,
  "id": "clx123abc",
  "url": "https://smart-tax-assistant-uploads.s3.ap-southeast-1.amazonaws.com/...",
  "document": { /* ... */ }
}
```

### Verify in S3

1. Go to AWS Console → S3
2. Open bucket: `smart-tax-assistant-uploads`
3. Check folder: `documents/{userId}/`
4. File should exist with timestamp prefix

### Test Signed URL

```bash
# Copy signed URL from upload response
# Paste in browser
# Should display/download file (expires in 1 hour)
```

---

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | ✅ Yes | - | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | ✅ Yes | - | IAM user secret key |
| `AWS_REGION` | No | `ap-southeast-1` | AWS region |
| `AWS_S3_BUCKET_NAME` | ✅ Yes | - | S3 bucket name |

### TypeScript Types

```typescript
// All types are exported from src/lib/s3.ts
import type { UploadResult, S3Config } from '@/lib/s3';

interface UploadResult {
  url: string;       // Permanent S3 URL
  key: string;       // S3 key
  signedUrl: string; // Temporary signed URL
}

interface S3Config {
  accessKeyId: string;
  secretAccessKey: string;
  region: string;
  bucketName: string;
}
```

---

## Summary

✅ **Created**: `src/lib/s3.ts` (474 lines)
✅ **Functions**: 8 public functions
✅ **Error Handling**: Follows codebase patterns (try-catch, console.error)
✅ **Types**: Full TypeScript support
✅ **Documentation**: JSDoc comments on all functions
✅ **Private Bucket Support**: Signed URLs for secure access
✅ **Backward Compatible**: Works with both S3 and local files

**Ready for Phase 3**: Update Upload API Route! 🚀
