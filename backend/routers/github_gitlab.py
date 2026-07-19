"""
GitHub / GitLab Integration router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import GitHubConnection, GitHubItem
from schemas import (
    GitHubConnectionCreate, GitHubConnectionUpdate, GitHubConnectionResponse,
    GitHubItemResponse,
)
from datetime import datetime
import httpx
import json

router = APIRouter(prefix="/api/github", tags=["github"])


@router.get("/connections", response_model=List[GitHubConnectionResponse])
def list_connections(db: Session = Depends(get_db)):
    return db.query(GitHubConnection).all()


@router.post("/connections", response_model=GitHubConnectionResponse)
def create_connection(data: GitHubConnectionCreate, db: Session = Depends(get_db)):
    conn = GitHubConnection(**data.model_dump())
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.put("/connections/{cid}", response_model=GitHubConnectionResponse)
def update_connection(cid: int, data: GitHubConnectionUpdate, db: Session = Depends(get_db)):
    conn = db.query(GitHubConnection).filter(GitHubConnection.id == cid).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(conn, k, v)
    db.commit()
    db.refresh(conn)
    return conn


@router.delete("/connections/{cid}")
def delete_connection(cid: int, db: Session = Depends(get_db)):
    conn = db.query(GitHubConnection).filter(GitHubConnection.id == cid).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(conn)
    db.commit()
    return {"ok": True}


@router.get("/items", response_model=List[GitHubItemResponse])
def list_items(connection_id: int = None, item_type: str = None, state: str = None,
               limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(GitHubItem).order_by(GitHubItem.updated_at_remote.desc().nullslast())
    if connection_id:
        q = q.filter(GitHubItem.connection_id == connection_id)
    if item_type:
        q = q.filter(GitHubItem.item_type == item_type)
    if state:
        q = q.filter(GitHubItem.state == state)
    return q.limit(limit).all()


@router.post("/sync/{cid}")
async def sync_github(cid: int, db: Session = Depends(get_db)):
    """Sync pull requests and issues from GitHub/GitLab."""
    conn = db.query(GitHubConnection).filter(GitHubConnection.id == cid).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    if not conn.is_enabled or not conn.api_token:
        raise HTTPException(status_code=400, detail="Connection not enabled or missing API token")

    repos = json.loads(conn.repos or "[]")
    headers = {}
    is_gitlab = conn.platform == "gitlab"

    if is_gitlab:
        headers["PRIVATE-TOKEN"] = conn.api_token
    else:
        headers["Authorization"] = f"token {conn.api_token}"
        headers["Accept"] = "application/vnd.github.v3+json"

    synced_count = 0

    for repo in repos:
        try:
            if is_gitlab:
                # GitLab API - merge requests
                encoded_repo = repo.replace("/", "%2F")
                mr_url = f"{conn.base_url}/projects/{encoded_repo}/merge_requests?state=opened&per_page=20"
                issue_url = f"{conn.base_url}/projects/{encoded_repo}/issues?state=opened&per_page=20"
            else:
                # GitHub API
                mr_url = f"{conn.base_url}/repos/{repo}/pulls?state=open&per_page=20"
                issue_url = f"{conn.base_url}/repos/{repo}/issues?state=open&per_page=20"

            async with httpx.AsyncClient(timeout=30) as client:
                # Sync PRs/MRs
                if conn.sync_pull_requests:
                    resp = await client.get(mr_url, headers=headers)
                    if resp.status_code == 200:
                        for item in resp.json():
                            title = item.get("title", "")
                            url = item.get("html_url", "")
                            author = item.get("user", {}).get("login", "")
                            labels = json.dumps([l.get("name", "") for l in item.get("labels", [])])
                            state = "merged" if item.get("merged_at") else item.get("state", "open")

                            existing = db.query(GitHubItem).filter(
                                GitHubItem.connection_id == cid,
                                GitHubItem.repo_name == repo,
                                GitHubItem.title == title,
                                GitHubItem.item_type == "pr",
                            ).first()

                            if existing:
                                existing.state = state
                                existing.labels = labels
                                existing.synced_at = datetime.utcnow()
                            else:
                                db.add(GitHubItem(
                                    connection_id=cid, item_type="pr", repo_name=repo,
                                    title=title, url=url, state=state, author=author,
                                    labels=labels, synced_at=datetime.utcnow(),
                                ))
                            synced_count += 1

                # Sync Issues
                if conn.sync_issues:
                    resp = await client.get(issue_url, headers=headers)
                    if resp.status_code == 200:
                        for item in resp.json():
                            if "pull_request" in item:  # Skip PRs that appear in issues endpoint
                                continue
                            title = item.get("title", "")
                            url = item.get("html_url", "")
                            author = item.get("user", {}).get("login", "")
                            labels = json.dumps([l.get("name", "") for l in item.get("labels", [])])
                            state = item.get("state", "open")

                            existing = db.query(GitHubItem).filter(
                                GitHubItem.connection_id == cid,
                                GitHubItem.repo_name == repo,
                                GitHubItem.title == title,
                                GitHubItem.item_type == "issue",
                            ).first()

                            if existing:
                                existing.state = state
                                existing.labels = labels
                                existing.synced_at = datetime.utcnow()
                            else:
                                db.add(GitHubItem(
                                    connection_id=cid, item_type="issue", repo_name=repo,
                                    title=title, url=url, state=state, author=author,
                                    labels=labels, synced_at=datetime.utcnow(),
                                ))
                            synced_count += 1

            db.commit()
        except Exception as e:
            print(f"Sync error for repo {repo}: {e}")
            continue

    conn.last_synced = datetime.utcnow()
    db.commit()

    return {"ok": True, "synced": synced_count, "repos_processed": len(repos)}


@router.delete("/items/{iid}")
def delete_item(iid: int, db: Session = Depends(get_db)):
    item = db.query(GitHubItem).filter(GitHubItem.id == iid).first()
    if item:
        db.delete(item)
        db.commit()
    return {"ok": True}
