"""
Centre AI - Admin Web UI
Elegant Apple-style black and white interface for managing the MCP server
"""
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, Request, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import jwt
import bcrypt

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.config import config
from mcp_server.database import db, vector_store, init_databases
from mcp_server.tools import MCPTools
from mcp_server.oauth import OAuth2Server

# Initialize FastAPI app
app = FastAPI(
    title="Centre AI Admin",
    description="Admin interface for Centre AI MCP Server",
    version="2.0.0"
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=config.security.secret_key,
    session_cookie="centre_admin_session",
    max_age=86400  # 24 hours
)

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Tools instance
tools = MCPTools()


# ==================== AUTHENTICATION ====================

def create_token(username: str) -> str:
    """Create JWT token"""
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(hours=config.security.jwt_expiry_hours),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, config.security.secret_key, algorithm="HS256")


def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return username"""
    try:
        payload = jwt.decode(token, config.security.secret_key, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_user(request: Request) -> Optional[str]:
    """Get current user from session"""
    token = request.session.get("token")
    if token:
        return verify_token(token)
    return None


async def require_auth(request: Request):
    """Require authentication"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ==================== STARTUP ====================

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    await init_databases()

    # Create default admin if not exists
    async with db.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM admins WHERE username = $1",
            config.security.admin_username
        )
        if not existing:
            password_hash = bcrypt.hashpw(
                config.security.admin_password.encode(),
                bcrypt.gensalt()
            ).decode()
            await conn.execute("""
                INSERT INTO admins (username, password_hash, display_name)
                VALUES ($1, $2, $3)
            """, config.security.admin_username, password_hash, "Administrator")


# ==================== ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page - show login form directly"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return await login_page(request)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login"""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT password_hash FROM admins WHERE username = $1",
            username
        )

    if row and bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        token = create_token(username)
        request.session["token"] = token
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid credentials"
    })


@app.get("/logout")
async def logout(request: Request):
    """Handle logout"""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: str = Depends(require_auth)):
    """Main dashboard"""
    # Get statistics
    async with db.acquire() as conn:
        memory_count = await conn.fetchval("SELECT COUNT(*) FROM memories")
        codebase_count = await conn.fetchval("SELECT COUNT(*) FROM codebases")
        project_count = await conn.fetchval("SELECT COUNT(*) FROM projects")
        instruction_count = await conn.fetchval("SELECT COUNT(*) FROM instructions")
        conversation_count = await conn.fetchval("SELECT COUNT(*) FROM conversations")

    vector_stats = await vector_store.get_stats()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "stats": {
            "memories": memory_count,
            "codebases": codebase_count,
            "projects": project_count,
            "instructions": instruction_count,
            "conversations": conversation_count,
            "vectors": vector_stats
        }
    })


@app.get("/memories", response_class=HTMLResponse)
async def memories_page(request: Request, user: str = Depends(require_auth)):
    """Memories management page"""
    result = await tools.get_memory(limit=100, semantic_search=False)
    return templates.TemplateResponse("memories.html", {
        "request": request,
        "user": user,
        "memories": result.get("memories", [])
    })


@app.post("/memories")
async def create_memory(
    request: Request,
    user: str = Depends(require_auth),
    content: str = Form(...),
    memory_type: str = Form("general"),
    importance: int = Form(5),
    tags: str = Form("")
):
    """Create new memory"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    await tools.create_memory(
        content=content,
        memory_type=memory_type,
        importance=importance,
        tags=tag_list
    )
    return RedirectResponse(url="/memories", status_code=302)


@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: int, user: str = Depends(require_auth)):
    """Delete memory"""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT embedding_id FROM memories WHERE id = $1",
            memory_id
        )
        if row and row["embedding_id"]:
            await vector_store.delete(vector_store.COLLECTION_MEMORIES, row["embedding_id"])
        await conn.execute("DELETE FROM memories WHERE id = $1", memory_id)
    return JSONResponse({"success": True})


@app.get("/codebases", response_class=HTMLResponse)
async def codebases_page(request: Request, user: str = Depends(require_auth)):
    """Codebases management page"""
    result = await tools.get_codebase(limit=50)
    return templates.TemplateResponse("codebases.html", {
        "request": request,
        "user": user,
        "codebases": result.get("results", {}).get("codebases", [])
    })


@app.post("/codebases")
async def create_codebase(
    request: Request,
    user: str = Depends(require_auth),
    name: str = Form(...),
    path: str = Form(...),
    description: str = Form(""),
    repo_url: str = Form("")
):
    """Index new codebase"""
    result = await tools.capture_codebase(
        name=name,
        path=path,
        description=description or None,
        repo_url=repo_url or None
    )
    return RedirectResponse(url="/codebases", status_code=302)


@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request, user: str = Depends(require_auth)):
    """Projects management page"""
    result = await tools.project_overview()
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "user": user,
        "projects": result.get("projects", [])
    })


@app.post("/projects")
async def create_project(
    request: Request,
    user: str = Depends(require_auth),
    name: str = Form(...),
    description: str = Form(""),
    status: str = Form("active"),
    priority: int = Form(5),
    tags: str = Form("")
):
    """Create new project"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    async with db.acquire() as conn:
        await conn.execute("""
            INSERT INTO projects (name, description, status, priority, tags)
            VALUES ($1, $2, $3, $4, $5)
        """, name, description, status, priority, tag_list)
    return RedirectResponse(url="/projects", status_code=302)


@app.get("/instructions", response_class=HTMLResponse)
async def instructions_page(request: Request, user: str = Depends(require_auth)):
    """Instructions management page"""
    result = await tools.get_instructions(active_only=False)
    return templates.TemplateResponse("instructions.html", {
        "request": request,
        "user": user,
        "instructions": result.get("instructions", [])
    })


@app.post("/instructions")
async def create_instruction(
    request: Request,
    user: str = Depends(require_auth),
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form(""),
    priority: int = Form(5)
):
    """Create new instruction"""
    async with db.acquire() as conn:
        await conn.execute("""
            INSERT INTO instructions (title, content, category, priority)
            VALUES ($1, $2, $3, $4)
        """, title, content, category or None, priority)
    return RedirectResponse(url="/instructions", status_code=302)


@app.get("/admins", response_class=HTMLResponse)
async def admins_page(request: Request, user: str = Depends(require_auth)):
    """Admin profiles management page"""
    result = await tools.who_am_i_talking_to()
    return templates.TemplateResponse("admins.html", {
        "request": request,
        "user": user,
        "admins": result.get("admins", [])
    })


@app.post("/admins")
async def update_admin(
    request: Request,
    user: str = Depends(require_auth),
    display_name: str = Form(""),
    email: str = Form(""),
    bio: str = Form(""),
    timezone: str = Form(""),
    languages: str = Form(""),
    expertise: str = Form("")
):
    """Update admin profile"""
    languages_list = [l.strip() for l in languages.split(",") if l.strip()]
    expertise_list = [e.strip() for e in expertise.split(",") if e.strip()]

    metadata = {
        "timezone": timezone,
        "languages": languages_list,
        "expertise": expertise_list
    }

    async with db.acquire() as conn:
        await conn.execute("""
            UPDATE admins SET
                display_name = $1,
                email = $2,
                bio = $3,
                metadata = $4,
                updated_at = CURRENT_TIMESTAMP
            WHERE username = $5
        """, display_name, email, bio, json.dumps(metadata), user)

    return RedirectResponse(url="/admins", status_code=302)


@app.get("/knowledge", response_class=HTMLResponse)
async def knowledge_page(request: Request, user: str = Depends(require_auth)):
    """Knowledge graph visualization page"""
    return templates.TemplateResponse("knowledge.html", {
        "request": request,
        "user": user
    })


@app.get("/api/knowledge-graph")
async def get_knowledge_graph(user: str = Depends(require_auth)):
    """API endpoint for knowledge graph data"""
    result = await tools.get_knowledge_graph(limit=200)
    return JSONResponse(result)


@app.post("/api/knowledge-node")
async def create_knowledge_node(
    request: Request,
    user: str = Depends(require_auth)
):
    """Create knowledge node"""
    data = await request.json()
    async with db.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO knowledge_nodes (node_type, title, content, parent_id)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """, data.get("type", "concept"), data["title"], data.get("content"), data.get("parent_id"))
    return JSONResponse({"success": True, "id": row["id"]})


@app.post("/api/knowledge-edge")
async def create_knowledge_edge(
    request: Request,
    user: str = Depends(require_auth)
):
    """Create knowledge edge"""
    data = await request.json()
    async with db.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO knowledge_edges (source_id, target_id, relationship, weight)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """, data["source"], data["target"], data["relationship"], data.get("weight", 1.0))
    return JSONResponse({"success": True, "id": row["id"]})


@app.post("/api/knowledge-graph/sync")
async def sync_knowledge_graph(user: str = Depends(require_auth)):
    """
    Automatically sync knowledge graph with memories, codebases, and projects.
    Creates nodes and edges based on existing data.
    """
    nodes_created = 0
    edges_created = 0

    async with db.acquire() as conn:
        # Sync memories as nodes
        memories = await conn.fetch("""
            SELECT id, content, memory_type, importance, tags
            FROM memories
            ORDER BY importance DESC, created_at DESC
            LIMIT 50
        """)

        for memory in memories:
            # Check if node already exists
            existing = await conn.fetchrow("""
                SELECT id FROM knowledge_nodes
                WHERE node_type = 'memory' AND title = $1
            """, f"Memory #{memory['id']}")

            if not existing:
                title = memory['content'][:50] + "..." if len(memory['content']) > 50 else memory['content']
                await conn.execute("""
                    INSERT INTO knowledge_nodes (node_type, title, content, parent_id)
                    VALUES ($1, $2, $3, $4)
                """, 'memory', title, memory['content'], None)
                nodes_created += 1

        # Sync codebases as nodes
        codebases = await conn.fetch("""
            SELECT id, name, description, language, file_count
            FROM codebases
            ORDER BY indexed_at DESC
        """)

        for codebase in codebases:
            existing = await conn.fetchrow("""
                SELECT id FROM knowledge_nodes
                WHERE node_type = 'codebase' AND title = $1
            """, codebase['name'])

            if not existing:
                content = f"{codebase['description'] or 'No description'} | Language: {codebase['language'] or 'Mixed'} | Files: {codebase['file_count'] or 0}"
                node_row = await conn.fetchrow("""
                    INSERT INTO knowledge_nodes (node_type, title, content, parent_id)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                """, 'technology', codebase['name'], content, None)
                nodes_created += 1

                # Create edges to related code files (most important ones)
                code_files = await conn.fetch("""
                    SELECT DISTINCT language FROM code_files
                    WHERE codebase_id = $1
                    LIMIT 5
                """, codebase['id'])

                for file in code_files:
                    # Find or create language node
                    lang_node = await conn.fetchrow("""
                        SELECT id FROM knowledge_nodes
                        WHERE node_type = 'technology' AND title = $1
                    """, file['language'].title())

                    if not lang_node:
                        lang_node = await conn.fetchrow("""
                            INSERT INTO knowledge_nodes (node_type, title, content, parent_id)
                            VALUES ($1, $2, $3, $4)
                            RETURNING id
                        """, 'technology', file['language'].title(), f"Programming language: {file['language']}", None)
                        nodes_created += 1

                    # Create edge between codebase and language
                    edge_exists = await conn.fetchrow("""
                        SELECT id FROM knowledge_edges
                        WHERE source_id = $1 AND target_id = $2
                    """, node_row['id'], lang_node['id'])

                    if not edge_exists:
                        await conn.execute("""
                            INSERT INTO knowledge_edges (source_id, target_id, relationship, weight)
                            VALUES ($1, $2, $3, $4)
                        """, node_row['id'], lang_node['id'], 'uses_language', 1.0)
                        edges_created += 1

        # Sync projects as nodes
        projects = await conn.fetch("""
            SELECT id, name, description, status, priority, tags
            FROM projects
            ORDER BY priority DESC, updated_at DESC
        """)

        for project in projects:
            existing = await conn.fetchrow("""
                SELECT id FROM knowledge_nodes
                WHERE node_type = 'project' AND title = $1
            """, project['name'])

            if not existing:
                content = f"{project['description'] or 'No description'} | Status: {project['status']} | Priority: {project['priority']}"
                project_node = await conn.fetchrow("""
                    INSERT INTO knowledge_nodes (node_type, title, content, parent_id)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                """, 'project', project['name'], content, None)
                nodes_created += 1

                # Create edges based on tags
                if project['tags']:
                    for tag in project['tags']:
                        # Find related codebases with similar names or descriptions
                        related_codebases = await conn.fetch("""
                            SELECT kn.id FROM knowledge_nodes kn
                            WHERE kn.node_type = 'technology'
                            AND (kn.title ILIKE $1 OR kn.content ILIKE $1)
                            LIMIT 3
                        """, f"%{tag}%")

                        for cb in related_codebases:
                            edge_exists = await conn.fetchrow("""
                                SELECT id FROM knowledge_edges
                                WHERE source_id = $1 AND target_id = $2
                            """, project_node['id'], cb['id'])

                            if not edge_exists:
                                await conn.execute("""
                                    INSERT INTO knowledge_edges (source_id, target_id, relationship, weight)
                                    VALUES ($1, $2, $3, $4)
                                """, project_node['id'], cb['id'], 'relates_to', 0.7)
                                edges_created += 1

    return JSONResponse({
        "success": True,
        "nodes_created": nodes_created,
        "edges_created": edges_created,
        "message": f"Synced {nodes_created} nodes and {edges_created} edges"
    })


@app.get("/conversations", response_class=HTMLResponse)
async def conversations_page(request: Request, user: str = Depends(require_auth)):
    """Conversations view page"""
    result = await tools.conversation_overview(limit=50)
    return templates.TemplateResponse("conversations.html", {
        "request": request,
        "user": user,
        "conversations": result.get("conversations", [])
    })


@app.get("/oauth-clients", response_class=HTMLResponse)
async def oauth_clients_page(request: Request, user: str = Depends(require_auth)):
    """OAuth clients management page"""
    async with db.acquire() as conn:
        clients = await conn.fetch("""
            SELECT id, client_id, client_name, redirect_uris, is_public, is_active,
                   created_at::text as created_at
            FROM oauth_clients
            ORDER BY created_at DESC
        """)

    return templates.TemplateResponse("oauth_clients.html", {
        "request": request,
        "user": user,
        "clients": [dict(c) for c in clients],
        "mcp_port": config.server.mcp_port
    })


@app.post("/api/oauth/clients")
async def create_oauth_client(
    request: Request,
    user: str = Depends(require_auth)
):
    """Create new OAuth client"""
    data = await request.json()

    client_name = data.get("client_name")
    redirect_uris = data.get("redirect_uris", [])
    is_public = data.get("is_public", True)

    if not client_name or not redirect_uris:
        return JSONResponse({
            "success": False,
            "error": "client_name and redirect_uris are required"
        })

    try:
        client = await OAuth2Server.register_client(
            client_name=client_name,
            redirect_uris=redirect_uris,
            is_public=is_public
        )

        return JSONResponse({
            "success": True,
            "client": client
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })


@app.patch("/api/oauth/clients/{client_id}")
async def update_oauth_client(
    client_id: int,
    request: Request,
    user: str = Depends(require_auth)
):
    """Update OAuth client"""
    data = await request.json()
    is_active = data.get("is_active")

    async with db.acquire() as conn:
        await conn.execute("""
            UPDATE oauth_clients SET is_active = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, is_active, client_id)

    return JSONResponse({"success": True})


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, user: str = Depends(require_auth)):
    """Settings page"""
    # Load search engine settings
    async with db.acquire() as conn:
        search_engine_row = await conn.fetchrow(
            "SELECT setting_value FROM system_settings WHERE setting_key = 'search_engine'"
        )
        searx_url_row = await conn.fetchrow(
            "SELECT setting_value FROM system_settings WHERE setting_key = 'searx_instance_url'"
        )
        results_count_row = await conn.fetchrow(
            "SELECT setting_value FROM system_settings WHERE setting_key = 'search_results_count'"
        )

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user,
        "mcp_token": config.security.mcp_auth_token,
        "mcp_port": config.server.mcp_port,
        "search_engine": search_engine_row["setting_value"] if search_engine_row else "duckduckgo",
        "searx_instance_url": searx_url_row["setting_value"] if searx_url_row else "https://searx.be",
        "search_results_count": int(results_count_row["setting_value"]) if results_count_row else 10
    })


@app.post("/settings/regenerate-token")
async def regenerate_token(user: str = Depends(require_auth)):
    """Regenerate MCP auth token"""
    # Note: In production, this would update the config and restart the MCP server
    new_token = secrets.token_hex(32)
    return JSONResponse({"token": new_token})


@app.post("/api/settings/search")
async def save_search_settings(
    request: Request,
    user: str = Depends(require_auth)
):
    """Save search engine settings"""
    data = await request.json()

    search_engine = data.get("search_engine", "duckduckgo")
    searx_url = data.get("searx_instance_url", "https://searx.be")
    results_count = data.get("search_results_count", 10)

    # Validate
    valid_engines = ["duckduckgo", "searx", "qwant", "startpage"]
    if search_engine not in valid_engines:
        return JSONResponse({
            "success": False,
            "error": f"Invalid search engine. Must be one of: {', '.join(valid_engines)}"
        })

    if not isinstance(results_count, int) or results_count < 1 or results_count > 50:
        return JSONResponse({
            "success": False,
            "error": "Results count must be between 1 and 50"
        })

    # Save to database
    async with db.acquire() as conn:
        await conn.execute("""
            INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
            VALUES ('search_engine', $1, 'string', 'Default web search engine')
            ON CONFLICT (setting_key) DO UPDATE SET setting_value = $1, updated_at = CURRENT_TIMESTAMP
        """, search_engine)

        await conn.execute("""
            INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
            VALUES ('searx_instance_url', $1, 'string', 'SearX instance URL')
            ON CONFLICT (setting_key) DO UPDATE SET setting_value = $1, updated_at = CURRENT_TIMESTAMP
        """, searx_url)

        await conn.execute("""
            INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
            VALUES ('search_results_count', $1, 'integer', 'Default number of search results')
            ON CONFLICT (setting_key) DO UPDATE SET setting_value = $1, updated_at = CURRENT_TIMESTAMP
        """, str(results_count))

    return JSONResponse({
        "success": True,
        "message": "Search settings saved successfully",
        "settings": {
            "search_engine": search_engine,
            "searx_instance_url": searx_url,
            "search_results_count": results_count
        }
    })


@app.get("/api/settings/search")
async def get_search_settings(user: str = Depends(require_auth)):
    """Get search engine settings"""
    async with db.acquire() as conn:
        search_engine_row = await conn.fetchrow(
            "SELECT setting_value FROM system_settings WHERE setting_key = 'search_engine'"
        )
        searx_url_row = await conn.fetchrow(
            "SELECT setting_value FROM system_settings WHERE setting_key = 'searx_instance_url'"
        )
        results_count_row = await conn.fetchrow(
            "SELECT setting_value FROM system_settings WHERE setting_key = 'search_results_count'"
        )

    return JSONResponse({
        "success": True,
        "settings": {
            "search_engine": search_engine_row["setting_value"] if search_engine_row else "duckduckgo",
            "searx_instance_url": searx_url_row["setting_value"] if searx_url_row else "https://searx.be",
            "search_results_count": int(results_count_row["setting_value"]) if results_count_row else 10
        }
    })


# Health check
@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "admin_ui.app:app",
        host=config.server.admin_host,
        port=config.server.admin_port,
        reload=config.server.debug
    )
