# Security Fixes Deployment Checklist

## Pre-Deployment Verification

### ✅ Code Changes
- [x] Issue #1: File locking implemented in `workflow_storage.py`
- [x] Issue #2: Workflow ID validation implemented
- [x] Issue #3: Rate limiting added to `/generate` endpoint
- [x] Issue #4: Input validators for `user_id` and `user_address`
- [x] Issue #6: Storage quotas implemented
- [x] Issue #7: Error messages sanitized

### ✅ Dependencies
- [x] `filelock==3.16.1` added to `requirements.txt`
- [x] Library already installed and tested
- [x] All imports verified

### ✅ Syntax & Validation
- [x] `workflow_storage.py` - Python syntax valid
- [x] `workflow.py` - Python syntax valid
- [x] Workflow ID pattern tested (regex validation)
- [x] User ID validation tested (injection protection)
- [x] Neo N3 address validation tested (Base58 format)

### ✅ Backward Compatibility
- [x] Existing workflow files remain compatible
- [x] API endpoints maintain same signatures
- [x] No breaking changes to response formats

---

## Deployment Steps

### 1. Install Dependencies (if not already installed)
```bash
cd /Users/siphoyawe/Desktop/Projects/Encode\ Hackathon/spica/backend
pip install -r requirements.txt
```

### 2. Run Tests (if test suite exists)
```bash
pytest tests/ -v
```

### 3. Start Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Verify Endpoints

**Test Rate Limiting on /parse:**
```bash
# Should succeed for first 10 requests, then return 429
for i in {1..12}; do
  echo "Request $i:"
  curl -X POST "http://localhost:8000/api/v1/workflow/parse" \
    -H "Content-Type: application/json" \
    -d '{"input": "When GAS drops below $5, swap 10 GAS for NEO"}' \
    -w "\nStatus: %{http_code}\n\n"
  sleep 1
done
```

**Test Rate Limiting on /generate:**
```bash
# Should succeed for first 10 requests, then return 429
for i in {1..12}; do
  echo "Request $i:"
  curl -X POST "http://localhost:8000/api/v1/workflow/generate" \
    -H "Content-Type: application/json" \
    -d '{
      "workflow_spec": {
        "name": "Test Workflow",
        "description": "Test",
        "trigger": {"type": "price", "token": "GAS", "operator": "below", "value": 5.0},
        "steps": []
      },
      "user_id": "test_user",
      "user_address": "N/A"
    }' \
    -w "\nStatus: %{http_code}\n\n"
  sleep 1
done
```

**Test Input Validation:**
```bash
# Should reject invalid user_id (contains @)
curl -X POST "http://localhost:8000/api/v1/workflow/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_spec": {...},
    "user_id": "user@invalid",
    "user_address": "N/A"
  }'
# Expected: 422 Unprocessable Entity

# Should reject invalid Neo address (doesn't start with N)
curl -X POST "http://localhost:8000/api/v1/workflow/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_spec": {...},
    "user_id": "valid_user",
    "user_address": "AInvalidAddress123456789"
  }'
# Expected: 422 Unprocessable Entity
```

**Test Workflow ID Validation:**
```bash
# Should reject path traversal attempt
curl -X GET "http://localhost:8000/api/v1/workflow/../../../etc/passwd"
# Expected: 400 or 404 (not file contents)
```

### 5. Monitor Logs

**Check for errors:**
```bash
tail -f logs/app.log | grep ERROR
```

**Check for rate limit hits:**
```bash
tail -f logs/app.log | grep "Rate limit exceeded"
```

**Check for quota violations:**
```bash
tail -f logs/app.log | grep "quota exceeded"
```

---

## Post-Deployment Monitoring

### Metrics to Track

1. **Rate Limiting:**
   - Track HTTP 429 responses
   - Monitor rate limit hits per IP
   - Alert if legitimate users are being blocked

2. **Storage Quotas:**
   - Monitor total workflow count
   - Track workflows per user
   - Alert at 80% and 90% capacity

3. **File Locking:**
   - Monitor lock timeout errors
   - Track average lock acquisition time
   - Alert on frequent timeouts

4. **Input Validation:**
   - Track validation errors (HTTP 422)
   - Monitor for attack patterns
   - Log suspicious input attempts

### Alerts to Configure

```yaml
alerts:
  - name: Rate Limit High Hit Rate
    condition: rate_limit_429_count > 100 per 10 minutes
    action: notify_team

  - name: Storage Quota Critical
    condition: total_workflows > 9000
    action: notify_ops_team

  - name: File Lock Timeouts
    condition: lock_timeout_count > 10 per hour
    action: investigate_concurrency

  - name: Invalid Input Pattern
    condition: validation_errors > 50 per minute
    action: check_for_attack
```

---

## Rollback Plan

If issues occur after deployment:

### 1. Quick Rollback (if critical)
```bash
# Revert to previous commit
git revert HEAD
git push

# Restart service
systemctl restart spica-backend
```

### 2. Selective Disable

**Disable rate limiting (temporary):**
```python
# In workflow.py, comment out rate limit check
# if not check_rate_limit(client_ip):
#     raise HTTPException(...)
```

**Disable quotas (temporary):**
```python
# In workflow_storage.py, comment out quota check
# await self._check_storage_quotas(user_id)
```

### 3. Monitor and Fix
- Collect error logs
- Identify root cause
- Apply targeted fix
- Re-deploy

---

## Security Validation Checklist

After deployment, verify:

- [ ] Path traversal attacks are blocked (workflow_id validation)
- [ ] Rate limiting works on both `/parse` and `/generate`
- [ ] Invalid `user_id` inputs are rejected
- [ ] Invalid `user_address` inputs are rejected
- [ ] Storage quotas prevent unbounded growth
- [ ] Error messages don't expose internal paths
- [ ] File locking prevents concurrent write corruption
- [ ] Lock timeouts are handled gracefully

---

## Success Criteria

✅ Deployment is successful if:

1. All 6 security issues are resolved
2. No backward compatibility breaks
3. API endpoints respond correctly
4. Rate limiting works as expected
5. Input validation rejects malicious inputs
6. Storage quotas are enforced
7. Error messages are sanitized
8. File operations are thread-safe

---

## Support Information

**For issues or questions:**
- Review: `/spica/backend/SECURITY_FIXES_SUMMARY.md`
- Logs: `/spica/backend/logs/`
- Metrics: Monitor dashboard (if configured)

**Security incidents:**
- Immediately notify security team
- Collect relevant logs
- Document attack vectors
- Apply emergency patches if needed

---

**Deployment Date:** [TO BE FILLED]
**Deployed By:** [TO BE FILLED]
**Environment:** [TO BE FILLED]
**Status:** ✅ READY FOR DEPLOYMENT
