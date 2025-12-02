# Commit Command

Commit changes for a specific part of the project (frontend or backend only).

## Arguments: $ARGUMENTS

## Rules

1. **If $ARGUMENTS is empty or not "frontend" or "backend"** - Do nothing and show:
   ```
   Usage: /commit <frontend|backend>

   Examples:
     /commit frontend  - Commit frontend changes only
     /commit backend   - Commit backend changes only
   ```

2. **If $ARGUMENTS is "frontend"**:
   - Run `git status frontend/`
   - If no changes, inform user and stop
   - Show changed files in frontend/
   - Run `git diff frontend/` to see changes
   - Analyze changes and draft a commit message
   - Ask user for confirmation
   - Run `git add frontend/` then `git commit -m "..."`

3. **If $ARGUMENTS is "backend"**:
   - Run `git status backend/`
   - If no changes, inform user and stop
   - Show changed files in backend/
   - Run `git diff backend/` to see changes
   - Analyze changes and draft a commit message
   - Ask user for confirmation
   - Run `git add backend/` then `git commit -m "..."`

## Commit Message Format

Use conventional commits:
- `feat: ...` - New feature
- `fix: ...` - Bug fix
- `refactor: ...` - Code refactoring
- `style: ...` - Formatting, styling
- `docs: ...` - Documentation
- `test: ...` - Tests
- `chore: ...` - Maintenance

Keep messages concise (1-2 sentences).

## Important

- NEVER include Claude Code signature or Co-Authored-By
- NEVER commit if $ARGUMENTS is empty
- NEVER commit files outside the specified directory
- Always ask for confirmation before committing
- Respond in Thai language
