from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import ContainerInfo
from schemas import ContainerInfoResponse
import docker
import os
import datetime

router = APIRouter(prefix="/api/docker", tags=["docker"])


def get_docker_client():
    try:
        # Try Unix socket (multiple paths)
        socket_paths = ["/var/run/docker.sock", "/run/docker.sock"]
        for socket_path in socket_paths:
            if os.path.exists(socket_path):
                try:
                    client = docker.DockerClient(base_url=f"unix://{socket_path}")
                    client.ping()
                    return client
                except Exception as e:
                    print(f"Failed to connect to {socket_path}: {e}")
                    continue
        # Windows Docker Desktop or remote Docker
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception as e:
            print(f"Failed to connect via from_env: {e}")
    except Exception as e:
        print(f"Docker client error: {e}")
    return None


@router.get("/containers", response_model=List[ContainerInfoResponse])
def get_containers(db: Session = Depends(get_db)):
    client = get_docker_client()
    if not client:
        stored = db.query(ContainerInfo).all()
        return stored

    container_list = []
    try:
        for c in client.containers.list(all=True):
            ports = ", ".join(
                f"{k}" for k in (c.attrs.get("NetworkSettings", {}).get("Ports", {}) or {}).keys()
            )
            stats = c.stats(stream=False)
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                        stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                           stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = round((cpu_delta / system_delta) * 100, 1)

            mem_usage = stats.get("memory_stats", {}).get("usage", 0)
            mem_limit = stats.get("memory_stats", {}).get("limit", 1)
            mem_str = f"{round(mem_usage / 1024 / 1024, 1)}MB / {round(mem_limit / 1024 / 1024, 1)}MB"

            started = c.attrs.get("State", {}).get("StartedAt", "")
            uptime_str = "N/A"
            if started:
                try:
                    started_dt = datetime.datetime.fromisoformat(started.replace("Z", "+00:00").split(".")[0])
                    delta = datetime.datetime.utcnow().replace(tzinfo=None) - started_dt.replace(tzinfo=None)
                    hours, rem = divmod(int(delta.total_seconds()), 3600)
                    mins, secs = divmod(rem, 60)
                    if hours > 24:
                        days = hours // 24
                        uptime_str = f"{days}d {hours % 24}h"
                    else:
                        uptime_str = f"{hours}h {mins}m"
                except Exception:
                    pass

            existing = db.query(ContainerInfo).filter(ContainerInfo.container_id == c.id).first()
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

            if existing:
                for k, v in info_data.items():
                    setattr(existing, k, v)
            else:
                existing = ContainerInfo(**info_data)
                db.add(existing)

            container_list.append(existing)

        db.commit()
    except Exception as e:
        container_list = db.query(ContainerInfo).all()

    return container_list


@router.post("/containers/{container_id}/start")
def start_container(container_id: str):
    client = get_docker_client()
    if not client:
        return {"ok": False, "error": "Docker not available"}
    try:
        c = client.containers.get(container_id)
        c.start()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/containers/{container_id}/stop")
def stop_container(container_id: str):
    client = get_docker_client()
    if not client:
        return {"ok": False, "error": "Docker not available"}
    try:
        c = client.containers.get(container_id)
        c.stop()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/containers/{container_id}/restart")
def restart_container(container_id: str):
    client = get_docker_client()
    if not client:
        return {"ok": False, "error": "Docker not available"}
    try:
        c = client.containers.get(container_id)
        c.restart()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/containers/{container_id}/logs")
def get_container_logs(container_id: str, tail: int = 100):
    client = get_docker_client()
    if not client:
        return {"ok": False, "error": "Docker not available"}
    try:
        c = client.containers.get(container_id)
        logs = c.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
        return {"ok": True, "logs": logs}
    except Exception as e:
        return {"ok": False, "error": str(e)}
