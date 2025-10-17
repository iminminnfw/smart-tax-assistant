# Contributing Guidelines

Thank you for contributing to Smart Tax Assistant!

## 🌿 Git Workflow

### Setting Up

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd smart_tax_assistant
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create your development branch:**
   ```bash
   git checkout develop
   git checkout -b feature/your-feature-name
   ```

### Branch Naming

- `feature/user-authentication` - New features
- `bugfix/login-error` - Bug fixes
- `hotfix/security-patch` - Urgent fixes
- `refactor/api-structure` - Code improvements
- `docs/api-documentation` - Documentation updates

## Making Changes

1. Write clean, documented code
2. Follow existing code style
3. Add TypeScript types for all functions
4. Update relevant documentation
5. Test your changes locally

## Commit Messages

Follow Conventional Commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Code style (formatting, no logic change)
- `refactor` - Code restructuring
- `test` - Adding tests
- `chore` - Maintenance

**Examples:**

```
feat(auth): implement two-factor authentication

- Add 2FA setup flow
- Integrate with authenticator apps
- Add backup codes

Closes #123
```

```
fix(documents): resolve upload timeout for large files

Increase timeout limit from 30s to 120s for files > 10MB
```

## Pull Request Process

1. **Ensure your branch is up to date:**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout your-feature-branch
   git rebase develop
   ```

2. **Push your branch:**
   ```bash
   git push -u origin feature/your-feature-name
   ```

3. **Create Pull Request on GitHub:**
   - Base: `develop`
   - Compare: `your-feature-branch`
   - Fill in PR template
   - Request review from team lead

4. Address review comments
5. Merge after approval

## Code Review Checklist

Before submitting PR, ensure:

- [ ] Code follows project structure
- [ ] All TypeScript types defined
- [ ] No `console.log` statements (use proper logging)
- [ ] Error handling implemented
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Meaningful commit messages

## 📁 Project Structure Guidelines

### Where to Put Your Code

**Frontend Components:**
```
src/components/YourComponent/
├── YourComponent.tsx
└── index.ts
```

**Business Logic:**
```
src/modules/your-module/
├── services/
│   └── your.service.ts      # Business logic here
├── types/
│   └── your.types.ts        # TypeScript interfaces
└── utils/
    └── your.utils.ts        # Helper functions
```

**API Routes (thin layer only):**
```typescript
// src/app/api/your-endpoint/route.ts
import { YourService } from '@/modules/your-module/services/your.service';

export async function POST(req: Request) {
  const service = new YourService();
  return service.handleRequest(await req.json());
}
```

### Don't Put Business Logic in API Routes!

❌ **Bad:**
```typescript
export async function POST(req: Request) {
  // 100 lines of business logic...
}
```

✅ **Good:**
```typescript
export async function POST(req: Request) {
  const service = new YourService();
  return service.handleRequest(await req.json());
}
```

## 🧪 Testing (Future)

Testing will be implemented later. Guidelines TBD.

## 📞 Getting Help

- Create an issue for bugs
- Start a discussion for questions
- Contact team lead for urgent matters

## 🎯 Current Priorities

1. ✅ Project restructuring
2. ✅ Git workflow setup
3. ⏳ Complete existing features
4. ⏳ Implement RAG module
5. ⏳ Add comprehensive testing

Thank you for contributing! 🙏
