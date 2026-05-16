"""Quick test: hit /ws/live and print the first frame."""
import asyncio, json, sys

async def main():
    try:
        import websockets
    except ImportError:
        print("websockets not installed — testing via _build_metrics directly")
        from app.websocket.manager import _build_metrics
        m = _build_metrics()
        print("_build_metrics OK:", json.dumps(m)[:300])
        return

    uri = "ws://localhost:8888/ws/live"
    print(f"Connecting to {uri} ...")
    try:
        async with websockets.connect(uri, open_timeout=5) as ws:
            raw = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(raw)
            print("Connected! packets_per_sec =", data.get("packets_per_sec"))
            print("bytes_per_sec =", data.get("bytes_per_sec"))
            print("active_connections =", data.get("active_connections"))
            print("SUCCESS - WebSocket is working!")
    except Exception as e:
        print("FAILED:", type(e).__name__, e)

asyncio.run(main())
