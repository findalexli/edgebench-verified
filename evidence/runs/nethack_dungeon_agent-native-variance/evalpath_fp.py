# Start-state fingerprint through the evaluator's own seed_process()+reset_env() for seed 0 (one call per process).
import hashlib, sys
sys.path.insert(0, "/tmp")
import eval_nethack as e
import gymnasium as gym
e.seed_process(0)
env = gym.make("NetHackChallenge-v0")
obs, info = e.reset_env(env, 0)
h = hashlib.sha256(obs["glyphs"].tobytes() + obs["blstats"].tobytes() + obs["inv_strs"].tobytes()).hexdigest()[:16]
inv = [bytes(s).rstrip(b"\0").decode(errors="replace") for s in obs["inv_strs"][:3]]
print("seed0 start fingerprint", h, inv, flush=True)
