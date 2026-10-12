import hashlib, sys, traceback
import gymnasium as gym, nle
print("nle", getattr(nle, "__version__", "?"), "gymnasium", gym.__version__, flush=True)
env = gym.make("NetHackChallenge-v0")
print("wrapper chain:", type(env).__name__, "->", type(env.unwrapped).__name__)
for label, obj in (("env.seed (as evaluator calls it)", env), ("env.unwrapped.seed", env.unwrapped)):
    try:
        obj.seed(1729); print(label, ": returned without error")
    except Exception as ex:
        print(label, ": RAISED", type(ex).__name__, "-", ex)
try:
    env.reset(seed=1729); print("env.reset(seed=1729): no error")
except Exception as ex:
    print("env.reset(seed=1729): RAISED", type(ex).__name__, "-", ex)
def fp(obs):
    return hashlib.sha256(obs["glyphs"].tobytes() + obs["blstats"].tobytes() + obs["inv_strs"].tobytes()).hexdigest()[:16]
for i in range(4):
    obs, info = env.reset()
    print("plain reset", i, fp(obs), bytes(obs["message"]).rstrip(b"\0")[:70])
env.close()
