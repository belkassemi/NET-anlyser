"""Add covering index on traffic_logs(timestamp, src_ip, bytes) to speed up bandwidth queries."""
import sqlite3, time

DB = "./netanalyzer.db"

print("Connecting...")
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("Creating index idx_traffic_time_src_bytes ...")
start = time.time()
cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_traffic_time_src_bytes
    ON traffic_logs (timestamp, src_ip, bytes)
""")
conn.commit()
print(f"Index created in {time.time()-start:.1f}s")

# Now re-test
start = time.time()
cur.execute("""
    SELECT src_ip, SUM(bytes)
    FROM traffic_logs
    WHERE timestamp >= datetime('now', '-1 hour')
    GROUP BY src_ip
    ORDER BY 2 DESC
    LIMIT 5
""")
r = cur.fetchall()
print(f"Top talkers after index: {r[:2]} in {time.time()-start:.2f}s")

conn.close()
print("Done.")
