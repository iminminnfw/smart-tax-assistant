# Smart Tax Assistant

Full-stack tax document management system with planned AI capabilities.

## 🏗️ Project Structure

```
smart_tax_assistant/
├── src/
│   ├── app/                  # Next.js App Router (Frontend + API routes)
│   ├── components/           # React components (Frontend)
│   ├── modules/              # Business logic modules
│   │   ├── auth/             # Authentication services
│   │   ├── documents/        # Document management
│   │   ├── users/            # User management
│   │   └── rag/              # 🚧 RAG implementation (planned)
│   ├── lib/                  # Core utilities (DB, Auth config)
│   └── shared/               # Shared types and utilities
├── prisma/                   # Database schema and migrations
└── public/                   # Static assets
```

## 🚀 Tech Stack

- **Framework:** Next.js 15+ (App Router)
- **Database:** PostgreSQL + Prisma ORM
- **Auth:** NextAuth.js
- **Styling:** Tailwind CSS + styled-components
- **Language:** TypeScript

## 📋 Prerequisites

- Node.js 18+
- PostgreSQL 14+
- pnpm (recommended) or npm

## 🛠️ Development Setup

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
npm run db:migrate

# Start development server
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to see the application.

## 🌿 Git Workflow

We follow GitHub Flow for collaboration.

### Branch Structure

- **main** - Production-ready code (protected)
- **develop** - Integration branch for features
- **feature/*** - New features
- **bugfix/*** - Bug fixes
- **hotfix/*** - Urgent production fixes

### Workflow

1. **Create feature branch from develop:**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

3. **Push and create Pull Request:**
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. After code review, merge to `develop`
5. Periodically merge `develop` → `main` for releases

### Commit Message Convention

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

## 📚 Module Documentation

### Authentication (`src/modules/auth/`)
Handles user authentication, session management, and authorization.

**Key Services:**
- `AuthService` - Registration, login, password validation

### Documents (`src/modules/documents/`)
Manages tax documents, file uploads, and document metadata.

**Key Services:**
- `DocumentService` - CRUD operations for documents
- `FolderService` - Folder management
- `TrashService` - Soft delete and recovery

### Users (`src/modules/users/`)
User profile management and preferences.

**Key Services:**
- `UserService` - Profile management, password changes

### RAG - Planned (`src/modules/rag/`)
🚧 **Status:** Architecture designed, implementation pending

- Will provide AI-powered document analysis
- Vector embeddings for semantic search
- Context-aware responses with source citations
- See `src/modules/rag/README.md` for details

## 🎯 Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run db:push      # Push schema changes to database
npm run db:migrate   # Create and run migrations
npm run db:studio    # Open Prisma Studio
npm run format       # Format code with Prettier
npm run type-check   # TypeScript type checking
```

## 🏛️ Architecture Decisions

### Why Modular Structure?

- **Separation of Concerns:** Business logic separated from API routes
- **Testability:** Services can be tested independently
- **Reusability:** Services can be used across multiple routes
- **Scalability:** Easy to add new features without cluttering API routes

### API Routes are Thin Layers

API routes in `src/app/api/` should be minimal:

```typescript
// ✅ Good: Thin API route
export async function POST(req: Request) {
  const service = new DocumentService();
  const data = await req.json();
  const result = await service.createDocument(data);
  return Response.json(result);
}

// ❌ Bad: Business logic in API route
export async function POST(req: Request) {
  // 50+ lines of logic here...
}
```

### Database Access

- All database operations go through Prisma ORM
- Database client initialized in `src/lib/prisma.ts`
- Never access database directly in API routes - always use services

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

## 📝 License

MIT

## 👥 Team

- **Lead Developer:** Atikun
- **Contributors:** (Will be updated as team grows)

## 🗺️ Roadmap

- [x] Project restructuring
- [x] Git workflow setup
- [x] Document management system
- [x] Trash/recovery feature
- [x] Global loader system
- [x] Tax calendar
- [ ] Complete all existing features
- [ ] Implement RAG module
- [ ] Add comprehensive testing
- [ ] Deploy to production

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Contact team lead
- Check documentation in `/docs`

---

**Built with ❤️ for better tax management in Thailand**
