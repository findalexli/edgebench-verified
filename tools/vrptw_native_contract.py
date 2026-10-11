"""Pure exact standalone VRPTW admission contract; no provider/native actions."""
import hashlib
import json
CONTROLLER = 'vrptw-original-checker-owned-close-sol-v1'
OPERATION = 'vrptw-original-checker-controls-sol-v1'
JOB_ID = 'vrptw-native-11b411cb9aacbb27'
ENVELOPE_CANONICAL_SHA256 = 'a5906612fedce27ca62ee3ae70861f0e3949c692bc15a66845aa0b1003b7c786'
def validate_contract(job):
    if type(job) is not dict:
        raise ValueError('VRPTW exact envelope object required')
    raw = json.dumps(job, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    if hashlib.sha256(raw).hexdigest() != ENVELOPE_CANONICAL_SHA256:
        raise ValueError('VRPTW frozen full envelope required')
