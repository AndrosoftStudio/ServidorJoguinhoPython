
PORT = 7777
TICK_RATE = 60          # server ticks per second
STATE_BROADCAST_HZ = 20 # how often server broadcasts full state
MAX_PLAYERS = 16
WORLD_W, WORLD_H = 2400, 1800
PLAYER_SPEED = 220.0    # pixels per second
BULLET_SPEED = 600.0
BULLET_TTL = 1.1        # seconds
PLAYER_RADIUS = 16
BULLET_RADIUS = 4
RESPAWN_TIME = 2.0
WALLS = [
    # Some rectangular obstacles (x, y, w, h)
    (500, 300, 200, 40),
    (900, 720, 320, 40),
    (1200, 200, 40, 350),
    (1300, 1000, 400, 40),
    (300, 1200, 280, 40),
    (1600, 500, 40, 400),
    (1700, 1400, 320, 40),
]
