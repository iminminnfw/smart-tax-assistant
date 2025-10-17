# Trash/Recovery Feature Documentation

## Overview
The trash feature allows users to recover deleted files and folders within 7 days. Items are automatically deleted after 7 days in trash.

## Database Changes
Added soft delete fields to `DocumentFolder` and `DocumentFile` models:
- `isDeleted: Boolean` - Flag indicating if item is in trash
- `deletedAt: DateTime?` - Timestamp when item was moved to trash

## API Endpoints

### 1. Move to Trash (Soft Delete)
**DELETE** `/api/folder/[id]` - Move folder and its files to trash
**DELETE** `/api/document/[id]` - Move file to trash

Response:
```json
{
  "ok": true,
  "message": "Folder moved to trash",
  "deletedFiles": 3
}
```

### 2. List Trash Items
**GET** `/api/trash`

Returns all deleted items for the authenticated user:
```json
{
  "folders": [...],
  "files": [...]
}
```

### 3. Restore from Trash
**POST** `/api/trash/restore`

Body:
```json
{
  "id": "folder_or_file_id",
  "type": "folder" | "file"
}
```

Response:
```json
{
  "ok": true,
  "message": "Folder restored successfully",
  "restoredFiles": 3
}
```

### 4. Permanent Delete (Single Item)
**DELETE** `/api/trash/permanent`

Body:
```json
{
  "id": "folder_or_file_id",
  "type": "folder" | "file"
}
```

Response:
```json
{
  "ok": true,
  "message": "Folder permanently deleted",
  "deletedFiles": 3
}
```

### 5. Clean Expired Items (Manual)
**DELETE** `/api/trash`

Permanently deletes all items older than 7 days:
```json
{
  "ok": true,
  "message": "Expired items permanently deleted",
  "deletedFiles": 5,
  "deletedFolders": 2
}
```

### 6. Automated Cleanup (Cron)
**GET** `/api/cron/cleanup-trash`

Automatically runs cleanup for items older than 7 days.

## Setup Automated Cleanup

### Option 1: Using Vercel Cron (Recommended for Vercel deployment)

Add to `vercel.json`:
```json
{
  "crons": [
    {
      "path": "/api/cron/cleanup-trash",
      "schedule": "0 2 * * *"
    }
  ]
}
```
This runs daily at 2 AM UTC.

### Option 2: Using External Cron Service

Use services like:
- **Cron-job.org** (Free): https://cron-job.org
- **EasyCron**: https://www.easycron.com
- **GitHub Actions** (Free)

Configure to call:
```bash
GET https://your-domain.com/api/cron/cleanup-trash
```

Schedule: `0 2 * * *` (Daily at 2 AM)

### Option 3: GitHub Actions (Free)

Create `.github/workflows/cleanup-trash.yml`:
```yaml
name: Cleanup Trash
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - name: Call cleanup endpoint
        run: |
          curl -X GET https://your-domain.com/api/cron/cleanup-trash
```

### Option 4: Add Authentication (Optional)

1. Add to `.env`:
```env
CRON_SECRET=your_secret_key_here
```

2. Uncomment authentication check in `/api/cron/cleanup-trash/route.ts`:
```typescript
if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
  return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
}
```

3. Configure cron service to send header:
```
Authorization: Bearer your_secret_key_here
```

## Frontend Integration (To-Do)

You'll need to create UI components for:
1. Trash page listing deleted items
2. Restore button for each item
3. Permanent delete confirmation dialog
4. Empty trash button
5. Days remaining indicator (7 - days since deletion)

Example component structure:
```
/app/(app)/trash/
  page.tsx - Trash listing page

/components/trash/
  TrashList.tsx - List of trash items
  TrashItem.tsx - Single trash item with actions
  RestoreButton.tsx - Restore functionality
  PermanentDeleteButton.tsx - Permanent delete with confirmation
```

## Testing

1. Delete a folder/file - should move to trash
2. Visit trash page - should see deleted items
3. Restore item - should appear in original location
4. Permanent delete - should remove immediately
5. Wait 7 days (or manually change deletedAt) - item should be auto-deleted

## Migration Applied
✅ Migration `20251016100445_add_soft_delete_to_documents` applied successfully
