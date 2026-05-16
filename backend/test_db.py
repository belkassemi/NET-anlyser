import time, sqlite3
conn = sqlite3.connect('./netanalyzer.db')
cur = conn.cursor()

# Test 1: simple count recent
start = time.time()
cur.execute("SELECT count(*) FROM traffic_logs WHERE timestamp >= datetime('now', '-5 minutes')")
r = cur.fetchone()
print(f"5-min count: {r[0]} rows in {time.time()-start:.2f}s")

# Test 2: sum bytes (slow?)
start = time.time()
cur.execute("SELECT src_ip, SUM(bytes) FROM traffic_logs WHERE timestamp >= datetime('now', '-1 hour') GROUP BY src_ip ORDER BY 2 DESC LIMIT 5")
r = cur.fetchall()
print(f"Top talkers: {r[:2]} in {time.time()-start:.2f}s")

# Test 3: protocol count
start = time.time()
cur.execute("SELECT protocol, count(*) FROM traffic_logs WHERE timestamp >= datetime('now', '-1 hour') GROUP BY protocol ORDER BY 2 DESC LIMIT 8")
r = cur.fetchall()
print(f"Protocols: {r[:3]} in {time.time()-start:.2f}s")
