# Safe Release Workflow (Clone + Feature Branch)

**Tags:** `git` `release` `branching` `risk-management`

## Concept
Implement risky/new feature in cloned workspace + dedicated branch, merge only after sign-off.

## When to use
- Production bot already running
- New module can break core flows

## When NOT to use
- Tiny hotfix needing immediate patch in same branch

## Minimal workflow
1. Clone to separate folder
2. Create feature branch
3. Implement + test in isolated docker stack
4. Push feature branch
5. Merge to main only after UAT
