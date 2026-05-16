"""Debug WebSocket connection with detailed error info."""
import asyncio
import json
import socket

async def test():
    # First check if port is open at TCP level
    try:
        s = socket.create_connection(("127.0.0.1", 8888), timeout=3)
        s.close()
        print("TCP port 8888: OPEN")
    except Exception as e:
        print(f"TCP port 8888: CLOSED ({e})")
        return

    # Try HTTP health
    import urllib.request
    try:
        resp = urllib.request.urlopen("http://localhost:8888/health", timeout=3)
        print("HTTP health:", resp.read().decode())
    except Exception as e:
        print("HTTP health FAILED:", e)
        return

    # Try WebSocket
    try:
        import websockets
        print("Trying WebSocket ws://localhost:8888/ws/live ...")
        ws = await asyncio.wait_for(
            websockets.connect("ws://localhost:8888/ws/live"),
            timeout=15
        )
        print("Handshake OK! Waiting for first message...")
        data = await asyncio.wait_for(ws.recv(), timeout=15)
        m = json.loads(data)
        print("SUCCESS! packets_per_sec =", m["packets_per_sec"])
        await ws.close()
    except Exception as e:
        print(f"WebSocket FAILED: {type(e).__name__}: {e}")

asyncio.run(test())
