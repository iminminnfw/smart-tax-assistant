# AGENTS.md - Agentic Coding Guidelines

This file provides guidelines for AI agents operating in this repository.

## Project Overview

- **Project Name**: Smart Tax Assistant
- **Tech Stack**: Next.js 15 (App Router), TypeScript, PostgreSQL, Prisma ORM, NextAuth.js, Tailwind CSS
- **Language**: English for code, Thai language used in some UI text

## Build & Development Commands

```bash
# Development
npm run dev              # Start dev server with Turbopack on port 3000
npm run build            # Build for production
npm run start            # Start production server

# Linting & Formatting
npm run lint             # Run ESLint
npm run format           # Format code with Prettier
npm run type-check       # TypeScript type checking (no emit)

# Database
npm run db:push          # Push schema changes to database
npm run db:migrate       # Create and run migrations
npm run db:studio        # Open Prisma Studio

# Running Tests
# Note: This project currently has no formal test framework
# Manual testing via browser or API tools is used (see TESTING_GUIDE.md)
```

### Running a Single Test (Manual)

Since there's no test framework, test endpoints manually:

```bash
# Get session token from browser DevTools, then test with curl
curl -X POST http://localhost:3000/api/upload \
  -H "Cookie: next-auth.session-token=YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -F "type=TAX_FORM"
```

## Code Style Guidelines

### General Principles

- **API Routes are Thin**: Business logic must go in services under `src/modules/`
- **TypeScript**: Full strict typing required - avoid `any` when possible
- **Error Handling**: Always wrap async operations in try/catch, return structured error responses

### Imports & Path Aliases

Use `@/` path alias for imports:

```typescript
// ✅ Good
import { prisma } from '@/lib/prisma';
import { AuthService } from '@/modules/auth/services/auth.service';
import type { ApiResponse } from '@/shared/types/api.types';

// ❌ Bad
import { prisma } from '../../../lib/prisma';
```

Import order (ESLint enforces this):
1. React/Next imports
2. External libraries
3. Internal `@/` imports
4. Type imports

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files (components) | PascalCase | `FileUploadModal.tsx` |
| Files (services) | camelCase | `auth.service.ts` |
| Files (types) | camelCase | `auth.types.ts` |
| Directories | camelCase | `authservices` → `auth/services` |
| Functions | camelCase | `getUserById()` |
| Classes | PascalCase | `class AuthService` |
| Interfaces | PascalCase | `interface UserProfile` |
| Constants | UPPER_SNAKE_CASE | `MAX_FILE_SIZE` |
| React Components | PascalCase | `export default function FileUploadModal()` |
| Database Models | PascalCase | `User`, `DocumentFile` |

### File Organization

```
src/
├── app/                    # Next.js App Router (pages + API routes)
│   └── api/               # API routes (keep thin - delegate to services)
├── components/            # React components
│   └── ComponentName/    # Component with subfolder (index.ts + files)
├── modules/               # Business logic (organized by domain)
│   └── auth/
│       ├── services/     # Service classes
│       ├── types/       # Type definitions
│       └── index.ts     # Barrel export
├── lib/                  # Core utilities (DB, Auth config, AWS)
├── shared/               # Shared types across modules
└── config/               # Configuration files
```

### TypeScript Guidelines

- Always use explicit return types for exported functions
- Use `type` for unions/intersections, `interface` for objects
- Prefer `interface` over `type` for Prisma schema compatibility

```typescript
// ✅ Good
export interface DocumentFile {
  id: string;
  name: string;
  fileUrl: string;
}

export type UploadStatus = 'uploading' | 'success' | 'error';

// ❌ Bad
type DocumentFile = {
  id: string;
  name: string;
};
```

### React & Next.js Patterns

- Use `'use client'` directive for client components
- Use Server Components by default, opt-in to client with `'use client'`
- Follow Next.js 15 conventions for API routes

```typescript
// ✅ Good - API Route (thin)
export async function POST(req: Request) {
  const service = new AuthService();
  const data = await req.json();
  return Response.json(await service.register(data));
}

// ❌ Bad - API Route with business logic
export async function POST(req: Request) {
  // 50+ lines of logic here...
}
```

### Error Handling

API routes and services must handle errors gracefully:

```typescript
// ✅ Good - Service returns structured result
async login(input: LoginInput): Promise<LoginResult> {
  try {
    const user = await prisma.user.findUnique({ where: { email: input.email } });
    if (!user) return { success: false, error: 'Invalid credentials' };
    return { success: true, user };
  } catch (error) {
    return { success: false, error: 'Failed to login' };
  }
}

// ✅ Good - API route returns proper error response
return NextResponse.json(
  { error: 'Failed to connect to backend', detail: String(error) },
  { status: 500 }
);
```

### Database Access

- All DB operations via Prisma ORM
- Database client initialized in `src/lib/prisma.ts`
- Never access database directly in API routes - always use services

```typescript
// ✅ Good
import { prisma } from '@/lib/prisma';
const user = await prisma.user.create({ data: { ... } });
```

### Styling

- Use Tailwind CSS classes
- Follow existing color patterns (slate, blue for primary)
- Use `text-slate-*`, `bg-slate-*`, `border-slate-*` for neutrals
- Use `text-blue-*`, `bg-blue-*` for primary actions

### Logging

Use descriptive console logs for debugging:

```typescript
console.log('[Module] Action description:', someVar);
console.error('[Module] Error:', error);
```

### AWS/S3 Patterns

- Use `@aws-sdk/client-s3` for S3 operations
- Generate presigned URLs for private bucket access
- Store permanent URLs in database, serve presigned URLs to clients

### Environment Variables

Required in `.env`:
- `DATABASE_URL` - PostgreSQL connection
- `NEXTAUTH_SECRET` - NextAuth.js secret
- `NEXTAUTH_URL` - NextAuth URL
- AWS variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_S3_BUCKET_NAME`
- `NEXT_PUBLIC_TAX_ADVISOR_API_URL` - Python backend URL

### Git Commit Convention

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance

### What NOT to Do

1. Don't put business logic in API routes - use services
2. Don't use `any` type - use proper typing
3. Don't commit secrets - use `.env` and `.gitignore`
4. Don't use relative imports - use `@/` alias
5. Don't skip linting - run `npm run lint` before committing

### Key Files & Locations

- Prisma Schema: `prisma/schema.prisma`
- Auth Config: `src/lib/auth.ts`
- Database Client: `src/lib/prisma.ts`
- NextAuth Types: `src/next-auth.d.ts`
- Testing Guide: `TESTING_GUIDE.md`
- AWS Setup: `AWS_SETUP_GUIDE.md`

### Dependencies to Know

- `next-auth@4` - Authentication (note: v4, not v5)
- `@prisma/client@6` - Database ORM
- `bcryptjs` - Password hashing
- `@aws-sdk/client-s3` - S3 storage
- `lucide-react` - Icons
- `recharts` - Charts
- `date-fns` - Date utilities
