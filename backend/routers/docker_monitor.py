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

router = APIRouter(prefix="/api/docker", tags=["docker"])

# ── detect Docker ──────────────────────────────────────────
DOCKER_SOCKET_PATHS = ["/var/run/docker.sock", "/run/docker.sock"]

def _find_socket() -> Optional[str]:
    """Return the first existing Docker socket path, or None."""
    for p in DOCKER_SOCKET_PATHS:
        if os.path.exists(p):
            return p
    return None

def _docker_api(method: str, path: str, body: Optional[dict] = None) -> dict:
    """Make raw HTTP request to Docker socket (no SDK dependency)."""
    import http.client
    import urllib.parse

    socket_path = _find_socket()
    if not socket_path:
        raise RuntimeError("No Docker socket found")

    conn = http.client.HTTPConnection("localhost")
    conn.sock = None  # will be replaced below
    # Create Unix socket connection
    import socket as sock_mod
    s = sock_mod.socket(sock_mod.AF_UNIX, sock_mod.SOCK_STREAM)
    s.connect(socket_path)
    conn.sock = s

    body_bytes = json.dumps(body).encode() if body else None
    headers = {"Host": "localhost", "Content-Type": "application/json"} if body_bytes else {"Host": "localhost"}
    conn.request(method, path, body=body_bytes, headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode()
    conn.close()
    if resp.status >= 400:
        raise RuntimeError(f"Docker API {resp.status}: {data[:200]}")
    return json.loads(data) if data else {}

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

    def list_containers(self) -> list:
        data = _docker_api("GET", "/containers/json?all=true")
        return [self.Container(c) for c in data]

    def container_stats(self, container_id: str) -> dict:
        return _docker_api("GET", f"/containers/{container_id}/stats?stream=false")

    def container_action(self, container_id: str, action: str):
        _docker_api("POST", f"/containers/{container_id}/{action}")

    def info(self) -> dict:
        return _docker_api("GET", "/info")

    def ping(self) -> bool:
        try:
            _docker_api("GET", "/_ping")
            return True
        except Exception:
            return False

# ── factory ─────────────────────────────────────────────────
def get_docker_client() -> Optional[DockerClient]:
    """Try Docker SDK first, fall back to raw HTTP over Unix socket."""
    # 1) Python docker SDK
    try:
        import docker as docker_sdk
        for socket_path in DOCKER_SOCKET_PATHS:
            if os.path.exists(socket_path):
                try:
                    client = docker_sdk.DockerClient(base_url=f"unix://{socket_path}")
                    client.ping()
                    return client  # SDK client — will be handled below
                except Exception as e:
                    print(f"[docker] SDK {socket_path}: {e}")
        try:
            client = docker_sdk.from_env()
            client.ping()
            return client
        except Exception as e:
            print(f"[docker] SDK from_env: {e}")
    except ImportError:
        print("[docker] docker SDK not installed, skipping")

    # 2) Raw HTTP over Unix socket (NAS-friendly, no SDK needed)
    try:
        raw = DockerClient()
        if raw.ping():
            print("[docker] Connected via raw HTTP over socket")
            return raw
    except Exception as e:
        print(f"[docker] Raw HTTP: {e}")

    # 3) Subprocess docker CLI (if installed in container)
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("[docker] Connected via subprocess CLI")
            return "cli"
    except Exception as e:
        print(f"[docker] Subprocess: {e}")

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


@router.get("/containers", response_model=List[ContainerInfoResponse])
def get_containers(db: Session = Depends(get_db)):
    client = get_docker_client()
    if not client:
        return db.query(ContainerInfo).all()

    container_list = []
    try:
        # ── handle both SDK client and raw DockerClient ──
        if isinstance(client, DockerClient):
            # Raw HTTP client
            for c in client.list_containers():
                cpu_percent = 0.0
                mem_str = "N/A"
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
                uptime_str = _parse_uptime(c.uptime) if c.uptime else "N/A"

                info_data = {
                    "container_id": c.id,
                    "name": c.name,
                    "status": c.status,
                    "image": c.image,
                    "ports": c.ports,
                    "cpu_percent": cpu_percent,
                    "memory_usage": mem_str,
                    "uptime": uptime_str,
                }
                existing = db.query(ContainerInfo).filter(ContainerInfo.container_id == c.id).first()
                if existing:
                    for k, v in info_data.items():
                        setattr(existing, k, v)
                else:
                    db.add(ContainerInfo(**info_data))
                container_list.append(existing or ContainerInfo(**info_data))
        else:
            # SDK client
            import docker as docker_sdk
            for c in client.containers.list(all=True):
                ports = ", ".join(k for k in (c.attrs.get("NetworkSettings", {}).get("Ports", {}) or {}).keys())
                try:
                    stats = c.stats(stream=False)
                    cpu_d = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    sys_d = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
                    cpu_percent = round((cpu_d / sys_d) * 100, 1) if sys_d > 0 else 0.0
                    mem_usage = stats.get("memory_stats", {}).get("usage", 0)
                    mem_limit = stats.get("memory_stats", {}).get("limit", 1)
                    mem_str = f"{round(mem_usage / 1024 / 1024, 1)}MB / {round(mem_limit / 1024 / 1024, 1)}MB"
                except Exception:
                    cpu_percent = 0.0
                    mem_str = "N/A"
                started = c.attrs.get("State", {}).get("StartedAt", "")
                uptime_str = _parse_uptime(started)
                info_data = {
                    "container_id": c.id,
                    "name": c.name,
                    "status": c.status,
                    "image": c.image.tags[0] if c.image.tags else c.image.id[:12],
                    "ports": ports,
                    "cpu_percent": cpu_percent,
                    "memory_usage": mem_str,
                    "uptime": uptime_str,
                }
                existing = db.query(ContainerInfo).filter(ContainerInfo.container_id == c.id).first()
                if existing:
                    for k, v in info_data.items():
                        setattr(existing, k, v)
                else:
                    db.add(ContainerInfo(**info_data))
                container_list.append(existing or ContainerInfo(**info_data))

        db.commit()
    except Exception as e:
        print(f"[docker] Error listing containers: {e}")
        container_list = db.query(ContainerInfo).all()

    return container_list


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
            data = _docker_api("GET", f"/containers/{container_id}/logs?stdout=true&stderr=true&tail={tail}")
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
