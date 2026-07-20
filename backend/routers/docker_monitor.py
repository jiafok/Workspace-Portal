from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import ContainerInfo
from schemas import ContainerInfoResponse
import os
import json
import datetime
import subprocess
import socket as sock_mod

router = APIRouter(prefix="/api/docker", tags=["docker"])

DOCKER_SOCKET = "/var/run/docker.sock"

# ── Raw HTTP over Unix socket (works on any Linux, no deps) ─
def _raw_docker(method: str, path: str, body: Optional[dict] = None) -> dict:
    """Pure Python raw HTTP over Unix socket. No SDK, no http.client."""
    if not os.path.exists(DOCKER_SOCKET):
        raise RuntimeError(f"Docker socket not found: {DOCKER_SOCKET}")

    s = sock_mod.socket(sock_mod.AF_UNIX, sock_mod.SOCK_STREAM)
    s.settimeout(10)
    try:
        s.connect(DOCKER_SOCKET)

        body_json = json.dumps(body) if body else None
        req = f"{method} {path} HTTP/1.0\r\nHost: localhost\r\n"
        if body_json:
            req += f"Content-Type: application/json\r\nContent-Length: {len(body_json)}\r\n"
        req += "\r\n"
        s.sendall(req.encode())
        if body_json:
            s.sendall(body_json.encode())

        # Read all response data
        chunks = []
        while True:
            try:
                chunk = s.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
            except sock_mod.timeout:
                break
        raw = b"".join(chunks).decode("utf-8", errors="replace")

        # Split headers and body
        parts = raw.split("\r\n\r\n", 1)
        if len(parts) < 2:
            raise RuntimeError(f"Invalid HTTP response: {raw[:200]}")
        header_section, body_str = parts

        # Check status
        status_line = header_section.split("\r\n")[0]
        status_code = int(status_line.split(" ")[1]) if len(status_line.split(" ")) > 1 else 0

        # Handle chunked transfer encoding
        if "Transfer-Encoding: chunked" in header_section:
            decoded = b""
            remaining = body_str
            while remaining:
                line_end = remaining.find("\r\n")
                if line_end == -1:
                    break
                try:
                    chunk_size = int(remaining[:line_end], 16)
                except ValueError:
                    break
                if chunk_size == 0:
                    break
                chunk_start = line_end + 2
                decoded += remaining[chunk_start:chunk_start + chunk_size].encode() if isinstance(remaining, str) else remaining[chunk_start:chunk_start + chunk_size]
                remaining = remaining[chunk_start + chunk_size + 2:]
            body_str = decoded.decode("utf-8", errors="replace") if isinstance(decoded, bytes) else decoded

        if status_code >= 400:
            raise RuntimeError(f"Docker API {status_code}: {body_str[:200]}")

        return json.loads(body_str) if body_str and body_str.strip() else {}

    finally:
        try:
            s.close()
        except Exception:
            pass

# ── curl fallback (if installed) ──
def _curl_docker(method: str, path: str, body: Optional[dict] = None) -> dict:
    """Use curl --unix-socket as fallback."""
    cmd = ["curl", "-s", "--unix-socket", DOCKER_SOCKET, f"http://localhost{path}"]
    if method != "GET":
        cmd += ["-X", method]
    if body:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"curl error: {result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else {}

# ── client wrapper ──────────────────────────────────────────
class DockerClient:
    """Lightweight Docker API client using raw HTTP over socket."""

    class Container:
        def __init__(self, raw: dict):
            self.raw = raw
            self.id = raw.get("Id", "")
            self.name = (raw.get("Names", [""])[0] or "").lstrip("/")
            state = raw.get("State", "")
            self.status = "running" if state == "running" else state
            self.image = raw.get("Image", "")
            self.ports = ", ".join(
                f"{p.get('PrivatePort','')}/{p.get('Type','')}" 
                for p in raw.get("Ports", []) if p
            )
            started = raw.get("Status", "")
            self.uptime = started if started else "N/A"

    @staticmethod
    def _api(method: str, path: str, body: Optional[dict] = None) -> dict:
        """Try raw Python first, then curl, then SDK."""
        errors = []
        # 1) Pure Python raw socket (zero deps, works everywhere)
        if os.path.exists(DOCKER_SOCKET):
            try:
                return _raw_docker(method, path, body)
            except Exception as e:
                errors.append(f"raw: {e}")
        # 2) curl --unix-socket
        try:
            result = subprocess.run(["which", "curl"], capture_output=True, timeout=3)
            if result.returncode == 0:
                return _curl_docker(method, path, body)
        except Exception as e:
            errors.append(f"curl: {e}")
        # 3) docker SDK
        try:
            import docker as docker_sdk
            if os.path.exists(DOCKER_SOCKET):
                client = docker_sdk.DockerClient(base_url=f"unix://{DOCKER_SOCKET}")
                client.ping()
                # Delegate to SDK path
                raise RuntimeError("use_sdk")
        except Exception as e:
            if "use_sdk" in str(e):
                raise  # re-raise to use SDK
            errors.append(f"sdk: {e}")
        raise RuntimeError("; ".join(errors))

    def list_containers(self) -> list:
        data = self._api("GET", "/containers/json?all=true")
        return [self.Container(c) for c in data]

    def container_stats(self, container_id: str) -> dict:
        return self._api("GET", f"/containers/{container_id}/stats?stream=false")

    def container_action(self, container_id: str, action: str):
        self._api("POST", f"/containers/{container_id}/{action}")

    def info(self) -> dict:
        return self._api("GET", "/info")

    def ping(self) -> bool:
        try:
            self._api("GET", "/_ping")
            return True
        except Exception:
            return False

# ── factory ─────────────────────────────────────────────────
def get_docker_client():
    """Try raw HTTP first (works everywhere), fall back to SDK."""
    # Always try our pure-Python raw HTTP first — works on any Linux distro
    if os.path.exists(DOCKER_SOCKET):
        try:
            raw = DockerClient()
            if raw.ping():
                print("[docker] Connected via pure Python socket")
                return raw
        except Exception as e:
            print(f"[docker] Raw HTTP: {e}")

    # Fallback: docker SDK
    try:
        import docker as docker_sdk
        if os.path.exists(DOCKER_SOCKET):
            try:
                client = docker_sdk.DockerClient(base_url=f"unix://{DOCKER_SOCKET}")
                client.ping()
                print("[docker] Connected via SDK")
                return client
            except Exception as e:
                print(f"[docker] SDK: {e}")
        client = docker_sdk.from_env()
        client.ping()
        return client
    except Exception as e:
        print(f"[docker] SDK fallback: {e}")

    return None


# ── routes ──────────────────────────────────────────────────

def _parse_uptime(started_at: str) -> str:
    """Parse Docker's StartedAt into human-readable uptime."""
    try:
        # Docker returns "2024-01-01T00:00:00.000000000Z" or similar
        ts = started_at.replace("Z", "+00:00").split(".")[0]
        started_dt = datetime.datetime.fromisoformat(ts)
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = now - started_dt
        hours, rem = divmod(int(delta.total_seconds()), 3600)
        mins = rem // 60
        if hours >= 24:
            return f"{hours // 24}d {hours % 24}h"
        return f"{hours}h {mins}m"
    except Exception:
        return started_at or "N/A"


@router.get("/containers")
def get_containers(db: Session = Depends(get_db)):
    client = get_docker_client()
    if not client:
        return db.query(ContainerInfo).all()

    # Return live container data directly (Portainer-like behavior).
    # Avoid writing to SQLite here to prevent lock contention on NAS.
    raw_data: list[dict] = []
    try:
        if isinstance(client, DockerClient):
            for c in client.list_containers():
                cpu_percent = 0.0
                mem_str = "N/A"
                uptime_str = _parse_uptime(c.uptime) if c.uptime else "N/A"
                try:
                    stats = client.container_stats(c.id)
                    cpu_d = stats.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
                    precpu_d = stats.get("precpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
                    sys_d = stats.get("cpu_stats", {}).get("system_cpu_usage", 0)
                    presys_d = stats.get("precpu_stats", {}).get("system_cpu_usage", 0)
                    if sys_d > presys_d:
                        cpu_percent = round(((cpu_d - precpu_d) / (sys_d - presys_d)) * 100, 1)
                    mem_usage = stats.get("memory_stats", {}).get("usage", 0)
                    mem_limit = stats.get("memory_stats", {}).get("limit", 1)
                    mem_str = f"{round(mem_usage / 1024 / 1024, 1)}MB / {round(mem_limit / 1024 / 1024, 1)}MB"
                except Exception:
                    pass
                raw_data.append({
                    "container_id": c.id or "",
                    "name": c.name or "",
                    "status": c.status or "",
                    "image": c.image or "",
                    "ports": c.ports or "",
                    "cpu_percent": cpu_percent,
                    "memory_usage": mem_str,
                    "uptime": uptime_str,
                })
        else:
            for c in client.containers.list(all=True):
                ports = ", ".join(k for k in (c.attrs.get("NetworkSettings", {}).get("Ports", {}) or {}).keys())
                cpu_percent = 0.0
                mem_str = "N/A"
                try:
                    stats = c.stats(stream=False)
                    cpu_d = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    sys_d = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
                    cpu_percent = round((cpu_d / sys_d) * 100, 1) if sys_d > 0 else 0.0
                    mem_usage = stats.get("memory_stats", {}).get("usage", 0)
                    mem_limit = stats.get("memory_stats", {}).get("limit", 1)
                    mem_str = f"{round(mem_usage / 1024 / 1024, 1)}MB / {round(mem_limit / 1024 / 1024, 1)}MB"
                except Exception:
                    pass
                raw_data.append({
                    "container_id": c.id,
                    "name": c.name,
                    "status": c.status,
                    "image": c.image.tags[0] if c.image.tags else c.image.id[:12],
                    "ports": ports,
                    "cpu_percent": cpu_percent,
                    "memory_usage": mem_str,
                    "uptime": _parse_uptime(c.attrs.get("State", {}).get("StartedAt", "")),
                })
    except Exception as e:
        print(f"[docker] Failed to fetch container data: {e}")
        return db.query(ContainerInfo).all()

    return raw_data


def _do_container_action(container_id: str, action: str):
    client = get_docker_client()
    if not client:
        return {"ok": False, "error": "Docker not available"}
    try:
        if isinstance(client, DockerClient):
            client.container_action(container_id, action)
        else:
            c = client.containers.get(container_id)
            getattr(c, action)()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/containers/{container_id}/start")
def start_container(container_id: str):
    return _do_container_action(container_id, "start")

@router.post("/containers/{container_id}/stop")
def stop_container(container_id: str):
    return _do_container_action(container_id, "stop")

@router.post("/containers/{container_id}/restart")
def restart_container(container_id: str):
    return _do_container_action(container_id, "restart")


@router.get("/containers/{container_id}/logs")
def get_container_logs(container_id: str, tail: int = 100):
    client = get_docker_client()
    if not client:
        return {"ok": False, "error": "Docker not available"}
    try:
        if isinstance(client, DockerClient):
            data = DockerClient._api("GET", f"/containers/{container_id}/logs?stdout=true&stderr=true&tail={tail}")
            return {"ok": True, "logs": str(data)}
        else:
            logs = client.containers.get(container_id).logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
            return {"ok": True, "logs": logs}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/status")
def docker_status():
    """Check if Docker is available"""
    client = get_docker_client()
    if not client:
        return {"available": False, "error": "Docker socket not found"}
    try:
        if isinstance(client, DockerClient):
            info = client.info()
        else:
            info = client.info()
        return {"available": True, "containers": info.get("Containers", 0), "server_version": info.get("ServerVersion", "")}
    except Exception as e:
        return {"available": False, "error": str(e)}
