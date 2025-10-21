
import asyncio, math, random, socket, json, time
from typing import Dict, Any, List, Tuple
from config import *
from common import send_msg, recv_msg, now, circle_rect_collision, get_lan_ip, clamp

PHASE_LOBBY = "lobby"
PHASE_GAME  = "game"

class Player:
    __slots__ = ("id", "name", "x", "y", "angle", "hp", "alive", "last_input_seq", "score", "respawn_at", "ready")
    def __init__(self, pid, name):
        self.id = pid
        self.name = name
        self.x = random.uniform(100, WORLD_W-100)
        self.y = random.uniform(100, WORLD_H-100)
        self.angle = 0.0
        self.hp = 100
        self.alive = True
        self.last_input_seq = -1
        self.score = 0
        self.respawn_at = 0.0
        self.ready = False

class Bullet:
    __slots__ = ("id","owner","x","y","vx","vy","spawn_time")
    def __init__(self, bid, owner, x, y, vx, vy):
        self.id = bid
        self.owner = owner
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.spawn_time = now()

class GameServer:
    def __init__(self, port=PORT):
        self.port = port
        self.next_player_id = 1
        self.next_bullet_id = 1
        self.players: Dict[int, Player] = {}
        self.bullets: Dict[int, Bullet] = {}
        self.clients: Dict[int, asyncio.StreamWriter] = {}
        self.last_broadcast = 0.0
        self.phase = PHASE_LOBBY
        self.host_id = None

    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, host="0.0.0.0", port=self.port)
        ip = get_lan_ip()
        print(f"[SERVER] Rodando em {ip}:{self.port}")
        async with self.server:
            await asyncio.gather(self.server.serve_forever(), self.game_loop())

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        pid = self.next_player_id; self.next_player_id += 1
        addr = writer.get_extra_info('peername')
        try:
            raw = await self.read_msg(reader)
            if not raw or raw.get("t") != "join":
                writer.close(); await writer.wait_closed(); return
            name = raw.get("name", f"P{pid}")[:16]
            if len(self.players) >= MAX_PLAYERS:
                await self.send(writer, {"t":"reject","reason":"Servidor cheio."})
                writer.close(); await writer.wait_closed(); return

            p = Player(pid, name)
            self.players[pid] = p
            self.clients[pid] = writer
            if self.host_id is None:
                self.host_id = pid
            print(f"[JOIN] {name} (id={pid}) de {addr}")
            await self.send(writer, {"t":"welcome","id":pid,"world":[WORLD_W, WORLD_H],"walls":WALLS,"phase":self.phase,"host":self.host_id})
            await self.send_lobby_state()  # envia estado de lobby atualizado
            await self.broadcast({"t":"player_join","id":pid,"name":name})

            while not reader.at_eof():
                msg = await self.read_msg(reader)
                if msg is None: break
                await self.process_message(pid, msg)
        except Exception as e:
            pass
        finally:
            if pid in self.players:
                del self.players[pid]
            if pid in self.clients:
                del self.clients[pid]
            if self.host_id == pid:
                # promover novo host, se existir
                self.host_id = next(iter(self.players.keys()), None)
            await self.send_lobby_state()
            await self.broadcast({"t":"player_leave","id":pid})
            print(f"[LEAVE] id={pid} desconectou")

    async def send(self, writer, obj):
        data = json.dumps(obj).encode('utf-8')
        writer.write(len(data).to_bytes(4, 'big') + data)
        await writer.drain()

    async def read_msg(self, reader):
        hdr = await reader.readexactly(4)
        n = int.from_bytes(hdr, 'big')
        data = await reader.readexactly(n)
        return json.loads(data.decode('utf-8'))

    async def process_message(self, pid: int, msg: Dict[str, Any]):
        t = msg.get("t")
        if t == "input":
            if self.phase != PHASE_GAME:
                return
            p = self.players.get(pid)
            if not p: return
            seq = msg.get("seq", 0)
            if seq <= p.last_input_seq: return
            p.last_input_seq = seq
            dt = 1.0 / TICK_RATE
            mx, my = float(msg.get("mx", 0)), float(msg.get("my", 0))
            p.angle = float(msg.get("angle", 0))
            dx = clamp(mx, -1.0, 1.0)
            dy = clamp(my, -1.0, 1.0)
            speed = PLAYER_SPEED * dt
            nx = p.x + dx * speed
            ny = p.y + dy * speed
            nx = clamp(nx, 0+16, WORLD_W-16)
            ny = clamp(ny, 0+16, WORLD_H-16)
            blocked = False
            for wx, wy, ww, wh in WALLS:
                if circle_rect_collision(nx, ny, PLAYER_RADIUS, wx, wy, ww, wh):
                    blocked = True; break
            if not blocked:
                p.x, p.y = nx, ny

            fire = bool(msg.get("fire", False))
            if fire and p.alive:
                bx = p.x + math.cos(p.angle) * (PLAYER_RADIUS+8)
                by = p.y + math.sin(p.angle) * (PLAYER_RADIUS+8)
                bvx = math.cos(p.angle) * BULLET_SPEED
                bvy = math.sin(p.angle) * BULLET_SPEED
                bid = self.next_bullet_id; self.next_bullet_id += 1
                self.bullets[bid] = Bullet(bid, pid, bx, by, bvx, bvy)

        elif t == "chat":
            txt = str(msg.get("msg",""))[:140]
            await self.broadcast({"t":"chat","from":pid,"txt":txt})

        elif t == "set_ready":
            p = self.players.get(pid)
            if p:
                p.ready = bool(msg.get("ready", False))
                await self.send_lobby_state()

        elif t == "start_game":
            if pid != self.host_id:  # apenas host
                return
            if self.phase != PHASE_LOBBY:
                return
            # só começa se todos prontos e no mínimo 2 jogadores
            if len(self.players) < 2: 
                return
            if not all(pl.ready for pl in self.players.values()):
                return
            await self.begin_round()

    async def begin_round(self):
        self.phase = PHASE_GAME
        # reset players for round
        for p in self.players.values():
            p.hp = 100
            p.alive = True
            p.respawn_at = 0.0
            p.x = random.uniform(80, WORLD_W-80)
            p.y = random.uniform(80, WORLD_H-80)
        self.bullets.clear()
        await self.broadcast({"t":"phase","phase":self.phase})
        print("[ROUND] Iniciado")

    async def end_round_to_lobby(self, winner_id: int):
        if winner_id in self.players:
            self.players[winner_id].score += 1
        self.phase = PHASE_LOBBY
        # reset lobby states
        for p in self.players.values():
            p.ready = False
            p.hp = 100; p.alive = True
            p.x = random.uniform(80, WORLD_W-80)
            p.y = random.uniform(80, WORLD_H-80)
        self.bullets.clear()
        await self.broadcast({"t":"round_end","winner":winner_id})
        await self.broadcast({"t":"phase","phase":self.phase})
        await self.send_lobby_state()
        print(f"[ROUND] Venceu id={winner_id}. Voltando ao lobby.")

    async def game_loop(self):
        dt = 1.0 / TICK_RATE
        while True:
            start = now()
            if self.phase == PHASE_GAME:
                rm = []
                for b in list(self.bullets.values()):
                    if now() - b.spawn_time > BULLET_TTL:
                        rm.append(b.id); continue
                    b.x += b.vx * dt; b.y += b.vy * dt
                    if b.x<0 or b.y<0 or b.x>WORLD_W or b.y>WORLD_H:
                        rm.append(b.id); continue
                    hit_wall = False
                    for wx, wy, ww, wh in WALLS:
                        if (wx<=b.x<=wx+ww) and (wy<=b.y<=wy+wh):
                            hit_wall = True; break
                    if hit_wall:
                        rm.append(b.id); continue
                    for pid, p in self.players.items():
                        if pid == b.owner or not p.alive:
                            continue
                        dx = p.x - b.x; dy = p.y - b.y
                        if dx*dx + dy*dy <= (PLAYER_RADIUS+BULLET_RADIUS)**2:
                            p.hp -= 34
                            rm.append(b.id)
                            if p.hp <= 0:
                                p.alive = False
                            break
                for bid in rm:
                    self.bullets.pop(bid, None)

                # checar fim de round (somente 1 vivo)
                alive_ids = [pid for pid,p in self.players.items() if p.alive]
                if len(alive_ids) <= 1 and len(self.players) >= 2:
                    winner = alive_ids[0] if alive_ids else None
                    await self.end_round_to_lobby(winner_id=winner if winner is not None else -1)

            # broadcast state (lobby também mostra players/score)
            if now() - self.last_broadcast >= 1.0/STATE_BROADCAST_HZ:
                self.last_broadcast = now()
                await self.broadcast_state()

            elapsed = now() - start
            await asyncio.sleep(max(0.0, dt - elapsed))

    async def broadcast(self, obj):
        dead = []
        for pid, w in list(self.clients.items()):
            try:
                await self.send(w, obj)
            except Exception:
                dead.append(pid)
        for pid in dead:
            self.clients.pop(pid, None)

    async def broadcast_state(self):
        players = {pid: {"x":p.x,"y":p.y,"a":p.angle,"hp":p.hp,"alive":p.alive,"name":p.name,"score":p.score,"ready":p.ready}
                   for pid,p in self.players.items()}
        bullets = [{"x":b.x,"y":b.y} for b in self.bullets.values()]
        await self.broadcast({"t":"state","players":players,"bullets":bullets,"phase":self.phase,"host":self.host_id})

    async def send_lobby_state(self):
        data = {"t":"lobby_state",
                "players": {pid: {"name":p.name,"ready":p.ready,"score":p.score} for pid,p in self.players.items()},
                "host": self.host_id}
        await self.broadcast(data)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="HyperShooter Servidor")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    gs = GameServer(port=args.port)
    try:
        asyncio.run(gs.start())
    except KeyboardInterrupt:
        print("\n[SERVER] Encerrado.")
