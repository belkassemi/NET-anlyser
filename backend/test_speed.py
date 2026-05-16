import time
from app.websocket.manager import _build_metrics
import json

start = time.time()
m = _build_metrics()
elapsed = time.time() - start
j = json.dumps(m)
print(f"_build_metrics took: {elapsed:.2f}s")
print("packets_per_sec:", m["packets_per_sec"])
print("bytes_per_sec:", m["bytes_per_sec"])
print("top_protocols:", m["top_protocols"][:3])
print("top_talkers_src:", m["top_talkers_src"][:2])
print("JSON OK, length:", len(j))
