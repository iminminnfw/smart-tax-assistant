# ✅ Rename Feature - Complete Implementation Guide

---

## 🎯 Feature Overview

Added ability to rename files and folders in the document management system.

**Key Features**:
- ✅ Rename files (database only, S3 key unchanged)
- ✅ Rename folders
- ✅ Validation (no duplicates, invalid characters)
- ✅ Clean UI with modal dialog
- ✅ Real-time updates

---

## 📋 Files Created/Modified

### Created Files

1. **`src/app/api/document/[id]/rename/route.ts`** - File rename API
2. **`src/app/api/folder/[id]/rename/route.ts`** - Folder rename API
3. **`src/components/RenameModal.tsx`** - Rename modal component
4. **`RENAME_FEATURE_GUIDE.md`** - This documentation

### Modified Files

5. **`src/app/(app)/document/page.tsx`** - Added rename buttons and modal integration

---

## 🔑 Design Decisions

### Why NOT Rename in S3?

**S3 keys remain unchanged** when renaming files. Here's why:

1. **S3 has no rename operation** - Must copy + delete (expensive)
2. **Timestamp in key** - `documents/{userId}/{timestamp}_{filename}` - timestamp ensures uniqueness
3. **Database has display name** - `DocumentFile.name` field for user-facing name
4. **Performance** - Database update is instant vs S3 copy/delete
5. **Cost** - Free database update vs S3 PUT + DELETE charges

**Example**:
```
S3 Key:        documents/user123/1729147823456_old_name.pdf  (never changes)
Database name: "Tax Form 2024"                                (user-editable)
```

---

## 📊 API Endpoints

### 1. Rename File

**Endpoint**: `PATCH /api/document/[id]/rename`

**Authentication**: Required (session-based)

**Request Body**:
```json
{
  "name": "New File Name"
}
```

**Validation**:
- Name is required
- Max length: 255 characters
- No invalid characters: `/ \ : * ? " < > |`
- No duplicate name in same folder
- Whitespace trimmed

**Response (Success)**:
```json
{
  "ok": true,
  "message": "File renamed successfully",
  "document": {
    "id": "file123",
    "name": "New File Name",
    "fileUrl": "https://s3.../documents/user123/1729147823456_old_name.pdf",
    // ... other fields
  }
}
```

**Response (Error)**:
```json
{
  "error": "A file with this name already exists in this folder"
}
```

**Status Codes**:
- `200` - Success
- `400` - Invalid input
- `401` - Unauthorized
- `404` - File not found
- `409` - Duplicate name
- `500` - Server error

---

### 2. Rename Folder

**Endpoint**: `PATCH /api/folder/[id]/rename`

**Authentication**: Required (session-based)

**Request Body**:
```json
{
  "name": "New Folder Name"
}
```

**Validation**: Same as file rename

**Response (Success)**:
```json
{
  "ok": true,
  "message": "Folder renamed successfully",
  "folder": {
    "id": "folder123",
    "name": "New Folder Name",
    "color": "#3B82F6",
    "files": [...],
    "subfolders": [...]
  }
}
```

**Response (Error)**:
```json
{
  "error": "A folder with this name already exists in this location"
}
```

---

## 🎨 UI Components

### RenameModal Component

**Location**: `src/components/RenameModal.tsx`

**Props**:
```typescript
interface RenameModalProps {
  item: {
    id: string;
    name: string;
    type: 'file' | 'folder';
  };
  onClose: () => void;
  onSuccess: () => void;
}
```

**Features**:
- Auto-focus on input field
- Real-time client-side validation
- Loading state during API call
- Error display
- Responsive design
- Dark mode support

**Usage**:
```tsx
{renameItem && (
  <RenameModal
    item={renameItem}
    onClose={() => setRenameItem(null)}
    onSuccess={() => {
      setRenameItem(null);
      fetchData(); // Refresh
    }}
  />
)}
```

---

### Document Page Integration

**Location**: `src/app/(app)/document/page.tsx`

**Changes**:

1. **Import Pencil icon**:
```tsx
import { Pencil } from 'lucide-react';
```

2. **Import RenameModal**:
```tsx
import RenameModal from '@/components/RenameModal';
```

3. **Add state**:
```tsx
const [renameItem, setRenameItem] = useState<{
  id: string;
  name: string;
  type: 'file' | 'folder'
} | null>(null);
```

4. **Add rename button (Files)**:
```tsx
<button
  onClick={(e) => {
    e.stopPropagation();
    setRenameItem({ id: file.id, name: file.name, type: 'file' });
  }}
  className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 hover:shadow-md rounded-xl transition-all duration-300"
>
  <Pencil className="w-4 h-4" />
</button>
```

5. **Add rename button (Folders)**:
```tsx
<button
  onClick={(e) => {
    e.stopPropagation();
    setRenameItem({ id: folder.id, name: folder.name, type: 'folder' });
  }}
  className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 hover:shadow-md rounded-xl transition-all duration-300"
>
  <Pencil className="w-4 h-4" />
</button>
```

6. **Add modal**:
```tsx
{renameItem && (
  <RenameModal
    item={renameItem}
    onClose={() => setRenameItem(null)}
    onSuccess={() => {
      setRenameItem(null);
      fetchData();
    }}
  />
)}
```

---

## 🔐 Security & Validation

### Server-Side Validation

All validation occurs on both client and server:

```typescript
// Invalid character regex
const INVALID_CHARS = /[\/\\:\*\?"<>\|]/;

// Validation checks
1. Name is required (not null/undefined)
2. Name is string type
3. Trimmed name not empty
4. Length <= 255 characters
5. No invalid characters: / \ : * ? " < > |
6. No duplicate name in same location
7. User owns the file/folder
8. Item is not deleted (isDeleted = false)
```

### Authorization

```typescript
// Verify user owns the file
const file = await prisma.documentFile.findFirst({
  where: {
    id,
    userId: user.id,
    isDeleted: false,
  },
});

if (!file) {
  return NextResponse.json({ error: 'File not found' }, { status: 404 });
}
```

### Duplicate Check

**Files**: Check within same folder
```typescript
const duplicate = await prisma.documentFile.findFirst({
  where: {
    userId: user.id,
    folderId: file.folderId, // Same folder
    name: trimmedName,
    isDeleted: false,
    id: { not: id }, // Exclude current file
  },
});
```

**Folders**: Check within same parent
```typescript
const duplicate = await prisma.documentFolder.findFirst({
  where: {
    userId: user.id,
    parentId: folder.parentId, // Same parent
    name: trimmedName,
    isDeleted: false,
    id: { not: id }, // Exclude current folder
  },
});
```

---

## 🧪 Testing Guide

### Test 1: Rename File (Success)

**Steps**:
1. Go to Documents page
2. Hover over a file card
3. Click pencil icon (blue)
4. Enter new name: "Tax Form 2024"
5. Click "Rename"

**Expected**:
- ✅ Modal opens with current name pre-filled
- ✅ Input field auto-focused
- ✅ Name updates instantly
- ✅ Modal closes
- ✅ File list refreshes
- ✅ Console log: `[Rename File] Renamed file old_name → Tax Form 2024`

**Verify Database**:
```sql
SELECT id, name, fileUrl FROM document_files WHERE id = 'file-id';
-- name should be "Tax Form 2024"
-- fileUrl should be UNCHANGED (S3 key same)
```

---

### Test 2: Rename Folder (Success)

**Steps**:
1. Hover over folder card
2. Click pencil icon
3. Enter: "Tax Documents 2024"
4. Click "Rename"

**Expected**:
- ✅ Folder name updates
- ✅ All files remain in folder
- ✅ Folder structure intact

---

### Test 3: Validation - Empty Name

**Steps**:
1. Click rename
2. Clear input field (empty)
3. Click "Rename"

**Expected**:
- ✅ Client-side error: "Name cannot be empty"
- ✅ Rename button disabled when empty
- ✅ No API call

---

### Test 4: Validation - Invalid Characters

**Steps**:
1. Click rename
2. Enter: `Test/File*Name?.pdf`
3. Click "Rename"

**Expected**:
- ✅ Error: "Name contains invalid characters: / \ : * ? " < > |"
- ✅ No database update

---

### Test 5: Validation - Duplicate Name

**Steps**:
1. Create two files: "File A", "File B"
2. Rename "File A" to "File B"
3. Click "Rename"

**Expected**:
- ✅ Server error (409): "A file with this name already exists in this folder"
- ✅ Original name preserved
- ✅ Error displayed in modal

---

### Test 6: Validation - Max Length

**Steps**:
1. Click rename
2. Enter 300 characters
3. Click "Rename"

**Expected**:
- ✅ Error: "Name too long (max 255 characters)"

---

### Test 7: Cross-Folder Duplicate (Allowed)

**Steps**:
1. Folder A has "File1.pdf"
2. Folder B has "File2.pdf"
3. Rename Folder B's "File2.pdf" to "File1.pdf"

**Expected**:
- ✅ Success! (Different folders allow same name)

---

### Test 8: S3 Key Unchanged

**Steps**:
1. Upload file: "original.pdf"
2. Note S3 key in database
3. Rename to "renamed.pdf"
4. Check database again

**Expected**:
```
Before:
  name: "original.pdf"
  fileUrl: "https://.../documents/user123/1729147823456_original.pdf"

After:
  name: "renamed.pdf"
  fileUrl: "https://.../documents/user123/1729147823456_original.pdf"  ✅ UNCHANGED
```

---

## 📈 User Flow

```
User hovers file/folder card
  ↓
Pencil icon appears (blue)
  ↓
User clicks pencil
  ↓
RenameModal opens with current name
  ↓
User types new name
  ↓
Client validation runs (real-time)
  ↓
User clicks "Rename"
  ↓
API call: PATCH /api/.../rename
  ↓
Server validation:
  - Required, length, characters
  - Duplicate check
  - Authorization
  ↓
Database update (name field only)
  ↓
Success response
  ↓
Modal closes
  ↓
fetchData() refreshes list
  ↓
UI updates with new name
```

---

## 🎨 UI/UX Features

### Visual Feedback

**Button States**:
- Default: Gray icon
- Hover: Blue icon + blue background
- Active: Modal opens

**Modal States**:
- Loading: Spinner + disabled buttons
- Error: Red error message
- Success: Auto-close

**Validation**:
- Real-time: As user types
- Color-coded: Red for errors
- Clear messages: Specific error text

### Accessibility

- ✅ Auto-focus on input
- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ Clear labels
- ✅ Error announcements
- ✅ Disabled state when loading

---

## 🐛 Troubleshooting

### Issue: Rename button not visible

**Check**:
1. Hover over file/folder card
2. Icons appear on hover (`opacity-0 group-hover:opacity-100`)
3. Pencil icon should be before trash icon

---

### Issue: "File not found" error

**Causes**:
1. File was deleted (soft delete)
2. File belongs to different user
3. Invalid file ID

**Solution**:
```sql
-- Check file status
SELECT id, name, userId, isDeleted FROM document_files WHERE id = 'file-id';
```

---

### Issue: Duplicate name error when renaming to same name

**Expected Behavior**: This should work!

**Check**:
- API excludes current file: `id: { not: id }`
- If fails, check database query

---

### Issue: Special characters allowed

**Should NOT happen** - validation blocks them

**If happens**:
1. Check regex: `INVALID_FILENAME_CHARS = /[\/\\:\*\?"<>\|]/`
2. Verify client + server validation
3. Test with: `Test/File*.pdf`

---

## 💡 Future Enhancements

### Optional Improvements

1. **Bulk Rename**: Rename multiple files at once
2. **Rename History**: Track name changes
3. **Undo Rename**: Revert to previous name
4. **Smart Suggestions**: Auto-complete based on existing files
5. **Rename with Move**: Rename + change folder simultaneously
6. **Extension Preservation**: Auto-preserve file extensions
7. **Rename Preview**: Show before/after comparison

---

## 📊 Database Impact

### Before Rename
```sql
-- Original record
{
  id: "file123",
  name: "old_name.pdf",
  fileUrl: "https://.../documents/user123/1729147823456_old_name.pdf",
  folderId: "folder456",
  // ...
}
```

### After Rename
```sql
-- Updated record
{
  id: "file123",
  name: "new_name.pdf",  ✅ CHANGED
  fileUrl: "https://.../documents/user123/1729147823456_old_name.pdf",  ✅ UNCHANGED
  folderId: "folder456",
  // ...
}
```

**Key Point**: Only `name` field changes, `fileUrl` (S3 key) stays the same!

---

## ✅ Feature Checklist

- [x] File rename API endpoint
- [x] Folder rename API endpoint
- [x] RenameModal component
- [x] Client-side validation
- [x] Server-side validation
- [x] Duplicate name check
- [x] Authorization check
- [x] UI integration (file cards)
- [x] UI integration (folder cards)
- [x] Modal state management
- [x] Error handling
- [x] Loading states
- [x] Success feedback
- [x] Responsive design
- [x] Dark mode support
- [x] Documentation

---

## 🎯 Success Criteria

Rename feature is successful if:

- [x] ✅ Users can rename files via UI
- [x] ✅ Users can rename folders via UI
- [x] ✅ Invalid names rejected (characters, length)
- [x] ✅ Duplicate names prevented
- [x] ✅ S3 keys remain unchanged
- [x] ✅ Database name field updates
- [x] ✅ UI refreshes after rename
- [x] ✅ Authorization enforced (own files only)
- [x] ✅ Error messages clear and helpful
- [x] ✅ Modal UX smooth and intuitive

---

## 📚 Code Examples

### API Call (Frontend)

```typescript
// Rename file
const renameFile = async (fileId: string, newName: string) => {
  const res = await fetch(`/api/document/${fileId}/rename`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: newName }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error);
  }

  return data.document;
};

// Rename folder
const renameFolder = async (folderId: string, newName: string) => {
  const res = await fetch(`/api/folder/${folderId}/rename`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: newName }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error);
  }

  return data.folder;
};
```

### Manual Testing (curl)

```bash
# Get session token
# 1. Login to app
# 2. DevTools → Application → Cookies → next-auth.session-token

# Rename file
curl -X PATCH http://localhost:3000/api/document/FILE_ID/rename \
  -H "Cookie: next-auth.session-token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"New File Name.pdf"}'

# Rename folder
curl -X PATCH http://localhost:3000/api/folder/FOLDER_ID/rename \
  -H "Cookie: next-auth.session-token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"New Folder Name"}'
```

---

## 🎉 Summary

**What was added**:
- ✅ Rename files (database only, S3 unchanged)
- ✅ Rename folders
- ✅ Validation (duplicates, characters, length)
- ✅ Clean modal UI
- ✅ Real-time updates

**How it works**:
1. User clicks pencil icon
2. Modal opens with current name
3. User enters new name
4. Validation runs (client + server)
5. Database updates (name field only)
6. UI refreshes

**Key benefit**: Fast, cost-free renames without touching S3 storage!

---

**Ready to use!** 🚀

Start renaming files and folders in your document management system!

```bash
npm run dev
```

Then hover over any file/folder and click the pencil icon! ✏️
