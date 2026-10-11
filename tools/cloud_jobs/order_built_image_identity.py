"""No evaluator/helper call: unchanged native actor already checks installed pins."""

def run(fixtures):
    if fixtures != {'purpose':'derived_judge_installed_identity'}:
        raise ValueError('fixed_identity_only_scope')
    return [{'component':'derived_judge_installed_identity','public_calls':0,
             'helper_calls':0,'pytest_calls':0,'body_exported':False}]
