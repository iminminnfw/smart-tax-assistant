# Global Loader Usage Guide

## Overview
A global loading system has been set up for your project using styled-components. The loader automatically shows during route changes and can be manually controlled from any component.

## Files Created
1. `/src/components/GlobalLoader.tsx` - The animated loader component
2. `/src/contexts/LoadingContext.tsx` - Context provider for loading state
3. `/src/components/RouteChangeListener.tsx` - Automatic route change detection
4. `/src/components/LoaderWrapper.tsx` - Wrapper component
5. `/src/lib/registry.tsx` - Styled-components registry for Next.js App Router
6. Updated `/src/app/layout.tsx` - Root layout with loader integration

## Features
- ✅ Beautiful animated spinner with gradient colors
- ✅ Automatic loading on route changes
- ✅ Manual control from any component
- ✅ Customizable loading text and subtext
- ✅ Smooth fade-in/fade-out animations
- ✅ Backdrop blur effect
- ✅ Responsive design

## How to Use

### 1. Automatic Loading (Already Set Up)
The loader automatically shows when navigating between pages. No additional code needed!

### 2. Manual Loading Control

#### Basic Usage
```tsx
'use client';

import { useLoading } from '@/contexts/LoadingContext';

export default function MyComponent() {
  const { startLoading, stopLoading } = useLoading();

  const handleClick = async () => {
    // Show loader
    startLoading();

    try {
      // Do some async work
      await fetch('/api/some-endpoint');
    } finally {
      // Hide loader
      stopLoading();
    }
  };

  return <button onClick={handleClick}>Load Data</button>;
}
```

#### With Custom Text
```tsx
'use client';

import { useLoading } from '@/contexts/LoadingContext';

export default function MyComponent() {
  const { startLoading, stopLoading } = useLoading();

  const handleSubmit = async () => {
    // Show loader with custom text
    startLoading('กำลังบันทึกข้อมูล...', 'กรุณารอสักครู่');

    try {
      await fetch('/api/save-data', { method: 'POST' });
    } finally {
      stopLoading();
    }
  };

  return <button onClick={handleSubmit}>Save</button>;
}
```

#### Using setLoading (More Control)
```tsx
'use client';

import { useLoading } from '@/contexts/LoadingContext';

export default function MyComponent() {
  const { setLoading } = useLoading();

  const handleProcess = async () => {
    // Start loading
    setLoading(true, 'กำลังประมวลผล...', 'อาจใช้เวลาสักครู่');

    try {
      await processData();
    } finally {
      // Stop loading
      setLoading(false);
    }
  };

  return <button onClick={handleProcess}>Process</button>;
}
```

### 3. Access Loading State

```tsx
'use client';

import { useLoading } from '@/contexts/LoadingContext';

export default function MyComponent() {
  const { isLoading, loadingText, loadingSubtext } = useLoading();

  return (
    <div>
      <p>Loading: {isLoading ? 'Yes' : 'No'}</p>
      <p>Text: {loadingText}</p>
      <p>Subtext: {loadingSubtext}</p>
    </div>
  );
}
```

## API Reference

### useLoading Hook

```typescript
const {
  isLoading,        // boolean - current loading state
  loadingText,      // string - main loading text
  loadingSubtext,   // string - secondary loading text
  setLoading,       // (loading: boolean, text?: string, subtext?: string) => void
  startLoading,     // (text?: string, subtext?: string) => void
  stopLoading,      // () => void
} = useLoading();
```

### Methods

#### `startLoading(text?, subtext?)`
Show the loader with optional custom text.

**Parameters:**
- `text` (optional): Main loading text (default: "กำลังโหลด...")
- `subtext` (optional): Secondary text (default: "โปรดรอสักครู่")

**Example:**
```tsx
startLoading('กำลังอัพโหลดไฟล์...', 'กรุณาอย่าปิดหน้าต่าง');
```

#### `stopLoading()`
Hide the loader.

**Example:**
```tsx
stopLoading();
```

#### `setLoading(loading, text?, subtext?)`
More explicit control over loading state.

**Parameters:**
- `loading`: boolean - true to show, false to hide
- `text` (optional): Main loading text
- `subtext` (optional): Secondary text

**Example:**
```tsx
setLoading(true, 'กำลังโหลด...', 'โปรดรอสักครู่');
// later...
setLoading(false);
```

## Common Use Cases

### 1. Form Submission
```tsx
const handleSubmit = async (e: FormEvent) => {
  e.preventDefault();
  startLoading('กำลังบันทึก...', 'กรุณารอสักครู่');

  try {
    await submitForm(formData);
    alert('บันทึกสำเร็จ!');
  } catch (error) {
    alert('เกิดข้อผิดพลาด');
  } finally {
    stopLoading();
  }
};
```

### 2. Data Fetching
```tsx
useEffect(() => {
  const fetchData = async () => {
    startLoading('กำลังโหลดข้อมูล...');

    try {
      const res = await fetch('/api/data');
      const data = await res.json();
      setData(data);
    } finally {
      stopLoading();
    }
  };

  fetchData();
}, []);
```

### 3. File Upload
```tsx
const handleUpload = async (file: File) => {
  startLoading('กำลังอัพโหลดไฟล์...', 'กรุณาอย่าปิดหน้าต่าง');

  const formData = new FormData();
  formData.append('file', file);

  try {
    await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
  } finally {
    stopLoading();
  }
};
```

### 4. Navigation with Loading
```tsx
const router = useRouter();
const { startLoading } = useLoading();

const navigateToPage = () => {
  startLoading('กำลังโหลดหน้าถัดไป...');
  router.push('/next-page');
  // RouteChangeListener will automatically stop loading when route changes
};
```

## Customization

### Change Loader Colors
Edit `/src/components/GlobalLoader.tsx`:

```tsx
const Spinner = styled.div`
  border-top-color: #3b82f6;  // Change this
  border-right-color: #8b5cf6; // Change this
`;

const SpinnerInner = styled.div`
  border-bottom-color: #ec4899; // Change this
  border-left-color: #f59e0b;   // Change this
`;
```

### Change Animation Speed
```tsx
animation: ${spin} 1s infinite; // Change duration (e.g., 0.5s for faster)
```

### Change Backdrop Style
```tsx
const LoaderOverlay = styled.div`
  background: rgba(255, 255, 255, 0.95); // Change opacity or color
  backdrop-filter: blur(8px); // Change blur amount
`;
```

## Notes
- ⚠️ The loader is global - only one instance runs at a time
- ⚠️ Always call `stopLoading()` in a `finally` block to ensure it stops even if errors occur
- ✅ Route changes automatically stop the loader
- ✅ The loader is client-side only and won't affect SSR

## Troubleshooting

### Loader doesn't show
Make sure you're in a client component (`'use client'` at the top).

### Loader doesn't stop
Always use `finally` block or ensure `stopLoading()` is called in error cases.

### TypeScript errors
Make sure you have styled-components types installed:
```bash
npm i -D @types/styled-components
```
