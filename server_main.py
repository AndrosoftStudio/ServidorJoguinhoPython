
import os, asyncio
from server import GameServer
from config import PORT as DEFAULT_PORT

def get_port():
    try:
        return int(os.environ.get("PORT", DEFAULT_PORT))
    except Exception:
        return DEFAULT_PORT

async def main():
    port = get_port()
    gs = GameServer(port=port)
    print("[BOOT] Dedicated server. Listening on 0.0.0.0:%d" % port)
    await gs.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SERVER] Stopped.")
