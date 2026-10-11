"""Pure exact VRPTW diagnostic admission; no provider/native actions."""
import hashlib
import json
CONTROLLER = 'vrptw-fixed-capture-diagnostic-owned-close-sol-v3'
OPERATION = 'vrptw-fixed-capture-diagnostic-sol-v3'
JOB_ID = 'vrptw-diagnostic-d9996161319eec2d'
ENVELOPE_CANONICAL_SHA256 = '93d4bb544573f14c5e8f1146bd657320b65cda8bbc992499e109b3448932dfff'
def validate_contract(job):
    if type(job) is not dict:
        raise ValueError('VRPTW diagnostic exact envelope object required')
    raw = json.dumps(job, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    if hashlib.sha256(raw).hexdigest() != ENVELOPE_CANONICAL_SHA256:
        raise ValueError('VRPTW diagnostic frozen full envelope required')
