# ADR-003: Database Strategy

## Status
Accepted

## Date
2025-01-15

## Context

MedCode AI uses databases for several purposes:
- Clinical coding session storage and results
- Claim tracking and billing workflows
- Webhook delivery records
- Error event tracking
- Audit trail storage

The system originally used SQLite for all storage but needs to support PostgreSQL for production deployments with concurrent access requirements.

## Decision

### Dual-Database Architecture

1. **SQLite (default)** — Used for single-instance deployments and development. The `data/` directory contains:
   - `claims.db` — Claim tracking, webhook registrations, delivery records
   - Session data via `storage/database.py`

2. **PostgreSQL (production)** — Available via `postgres_claim_tracker.py` for multi-instance deployments. The PostgreSQL backend provides:
   - Connection pooling
   - Concurrent write support
   - ACID guarantees under load
   - Better crash recovery

### Abstraction Layer

The `billing/claim_tracker.py` provides a unified interface:
```python
tracker = ClaimTracker()  # Uses SQLite by default
# or
tracker = PostgresClaimTracker(connection_string=...)  # PostgreSQL
```

Both implementations share the same public API (`submit`, `update_status`, `get_status`, `list_claims`).

### Schema Management

- SQLite schemas are created via `CREATE TABLE IF NOT EXISTS` on first use
- PostgreSQL schemas are managed via `schema.sql`
- No migration framework is used — schema changes are additive (new columns with defaults)

### Data Retention

- Session data: 90 days (configurable via `DATA_RETENTION_DAYS`)
- Error events: 180 days
- Claim records: 7 years (HIPAA requirement)
- Audit logs: 7 years (HIPAA requirement)

## Consequences

**Positive:**
- Zero-config development experience with SQLite
- Production-ready with PostgreSQL for concurrent access
- Shared API surface means no code changes when switching databases
- HIPAA-compliant retention periods

**Negative:**
- Two database backends to test and maintain
- SQLite limitations (single-writer) mean development behavior may differ from production
- Schema drift possible if SQLite and PostgreSQL schemas diverge

## Alternatives Considered

1. **PostgreSQL-only** — Rejected because it adds a mandatory dependency for development and simple deployments.

2. **ORM-based (SQLAlchemy)** — Rejected because the query patterns are simple enough that raw SQL is clearer and has no ORM overhead.

3. **MongoDB/NoSQL** — Rejected because the data is relational (claims reference patients, providers, payer rules) and SQL provides stronger consistency guarantees.

## Migration Path

For production deployments:
1. Set `DATABASE_URL` environment variable to PostgreSQL connection string
2. The `postgres_claim_tracker.py` module handles connection management
3. SQLite remains available as a fallback for read-heavy operations
