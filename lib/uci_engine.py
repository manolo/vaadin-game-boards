"""Minimal UCI engine wrapper for communicating with Stockfish or any UCI engine."""

import subprocess


class UCIEngine:
    """Communicates with a UCI chess engine via stdin/stdout."""

    def __init__(self, path: str, depth: int = 15, threads: int = 1, hash_mb: int = 64):
        self._path = path
        self._depth = depth
        self._process = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        self._send("uci")
        self._wait_for("uciok")
        self._send(f"setoption name Threads value {threads}")
        self._send(f"setoption name Hash value {hash_mb}")
        self._send("isready")
        self._wait_for("readyok")

    def _send(self, cmd: str):
        self._process.stdin.write(cmd + "\n")
        self._process.stdin.flush()

    def _wait_for(self, token: str) -> list[str]:
        """Read lines until one starts with token. Returns all lines read."""
        lines = []
        while True:
            line = self._process.stdout.readline().strip()
            lines.append(line)
            if line.startswith(token):
                return lines

    def set_skill_level(self, level: int):
        self._send(f"setoption name Skill Level value {level}")

    def set_fen_position(self, fen: str):
        self._send(f"position fen {fen}")

    def get_best_move_time(self, time_ms: int) -> str | None:
        """Search for the best move with a time limit. Returns UCI move string or None."""
        self._send(f"go movetime {time_ms}")
        lines = self._wait_for("bestmove")
        for line in lines:
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2 and parts[1] != "(none)":
                    return parts[1]
                return None
        return None

    def quit(self):
        try:
            self._send("quit")
            self._process.wait(timeout=3)
        except (BrokenPipeError, OSError, subprocess.TimeoutExpired):
            self._process.kill()

    def __del__(self):
        if self._process.poll() is None:
            self.quit()
