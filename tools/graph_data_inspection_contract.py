"""Pure exact Graph original installed-data auditor envelope; no provider or data read."""
import hashlib,json
CONTROLLER='graph-installed-data-owned-close-sol-v1'
OPERATION='graph-original-installed-data-sol-v1'
JOB_ID='graph-installed-data-4a4347f9086d0412'
ENVELOPE_CANONICAL_SHA256='9dc63aaa1c22e2c1e87475e9b88d024c7d1eb1d64d6908354ff52bab8678e8b6'
def validate_contract(job):
    if type(job) is not dict:
        raise ValueError('Graph data exact envelope object required')
    raw=json.dumps(job,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    if hashlib.sha256(raw).hexdigest()!=ENVELOPE_CANONICAL_SHA256:
        raise ValueError('Graph data frozen full envelope required')
