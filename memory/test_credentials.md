# Test Credentials

Use these accounts for local development and QA. **Change all passwords before deploying to production.**

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| Admin | admin@learnhub.com | Set via `ADMIN_PASSWORD` in backend `.env` (Docker default: `change-me-in-production`) | Full platform access; account is only seeded when `ADMIN_PASSWORD` is set |
| Admin 2 | admin2@learnhub.com | Set via `ADMIN2_PASSWORD` in backend `.env` (Docker default: `change-me-admin2`) | Second admin; both `ADMIN2_EMAIL` and `ADMIN2_PASSWORD` must be set |
| Student | student@test.com | test123 | Create via registration or seed manually |

## Client Manager accounts

Client managers cannot self-register. An admin must:

1. Register the user as a student (or create the account), then
2. `PUT /api/users/{user_id}/role?role=client_manager`

## Creating test users via API

```bash
# Register student
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"test123","name":"Test Student"}'

# Login as admin, then promote to client manager
curl -X PUT "http://localhost:8001/api/users/{user_id}/role?role=client_manager" \
  --cookie "access_token=..."
```
