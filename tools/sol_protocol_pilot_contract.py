"""Pure exact V7 partial protocol envelope; no source, provider or auth access."""
import hashlib
import json
CONTROLLER = 'sol-protocol-owned-close-v7'
OPERATION = 'sol-agent-protocol-pilot-v7'
JOB_ID = 'sol-k12-audit-protocol-pilot-v7'
ENVELOPE_CANONICAL_SHA256 = 'ee06b905a8be0c51e70e7948eb06af135addbcc6e6aeab43b0b5d0725bdcfc98'
def validate_contract(job):
    if type(job) is not dict:
        raise ValueError('V7 exact envelope object required')
    raw = json.dumps(job, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    if hashlib.sha256(raw).hexdigest() != ENVELOPE_CANONICAL_SHA256:
        raise ValueError('V7 frozen full partial protocol envelope required')
