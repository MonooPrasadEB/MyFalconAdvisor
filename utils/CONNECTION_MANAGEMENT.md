# Connection Management Guide

## Automatic Features (No Manual Intervention)

### 1. PostgreSQL Server-Side Auto-Timeout
- Idle transactions terminated after 5 minutes
- Configured in `connect_args` of SQLAlchemy engine

### 2. Connection Pool Auto-Recycling
- Connections recycled every 30 minutes
- Pre-ping verifies connections before use
- No stale connections

### 3. Exit Cleanup
- All connections closed when CLI exits
- Registered via `atexit` in `cli.py`

### 4. Optimized Pool Settings

#### Before (Too Conservative)
```python
pool_size=2          # Only 2 permanent connections
max_overflow=3       # Max 5 total connections
```

#### After (Balanced with Auto-Cleanup)
```python
pool_size=5          # 5 permanent connections
max_overflow=10      # Up to 15 total connections for bursts
pool_timeout=30      # Timeout getting from pool
pool_recycle=1800    # Recycle after 30 min
pool_pre_ping=True   # Verify before use
```

**Why this works now:**
- Auto-cleanup prevents accumulation
- Server-side timeout kills stuck connections
- Exit handler closes all connections
- Recycling prevents stale connections

## Manual Commands (Run When Needed)

### Quick Status Check
```bash
python utils/connection_utils.py status
```

### Close Idle Connections
```bash
python utils/connection_utils.py cleanup
```

### Dispose Entire Pool
```bash
python utils/connection_utils.py dispose
```

## Connection Pool Explained

- **pool_size (5)**: Always-available connections
- **max_overflow (10)**: Extra connections created on demand
- **Total capacity**: 15 concurrent connections
- **Automatic cleanup**: Prevents leaks
- **No background processes**: Everything runs in-process

## Monitoring

Check pool status anytime:
```bash
python utils/connection_utils.py status
```

Output shows:
- `size`: Pool capacity (5)
- `checked_in`: Available connections
- `checked_out`: In-use connections
- `overflow`: Extra connections beyond pool_size
- `total`: Current active connections
