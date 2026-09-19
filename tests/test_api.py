import os
import shutil
import pathlib
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services.generation_service import generation_service
from agent.tools import set_project_root, safe_path_for_project, read_file, write_file, get_project_root
from unittest.mock import patch, AsyncMock

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_agent_runner():
    """Mocks the LLM agent runner during API tests to prevent external API calls and ensure sub-second test runs."""
    with patch("api.services.generation_service.run_agent_generation", new_callable=AsyncMock) as mock_run:
        yield mock_run

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"

def test_dynamic_tools_scoping(tmp_path):
    test_dir = tmp_path / "test_workspace"
    set_project_root(test_dir)
    assert get_project_root() == test_dir.resolve()

    # Write file via tool
    res = write_file.invoke({"path": "index.html", "content": "<h1>Test</h1>"})
    assert "WROTE" in res

    # Read file back
    content = read_file.invoke({"path": "index.html"})
    assert content == "<h1>Test</h1>"

    # Test path traversal prevention
    with pytest.raises(ValueError, match="Attempt to access path outside project root"):
        safe_path_for_project("../../etc/passwd")

def test_generation_lifecycle_endpoints(tmp_path):
    # Mock storage dir for tests
    generation_service.storage_dir = tmp_path

    # Create generation
    payload = {"prompt": "Create a modern calculator app"}
    res = client.post("/api/generations", json=payload)
    assert res.status_code == 201
    gen_data = res.json()
    gen_id = gen_data["id"]
    assert gen_data["prompt"] == "Create a modern calculator app"
    assert gen_data["state"] in ["queued", "planning"]

    # Get generation status
    res = client.get(f"/api/generations/{gen_id}")
    assert res.status_code == 200
    assert res.json()["id"] == gen_id

    # Create file in project directory manually to verify file tree & content APIs
    proj_dir = generation_service._get_project_dir(gen_id)
    (proj_dir / "style.css").write_text("body { background: #000; }", encoding="utf-8")

    # Get file tree
    res = client.get(f"/api/generations/{gen_id}/files")
    assert res.status_code == 200
    files = res.json()
    assert len(files) >= 1
    assert files[0]["name"] == "style.css"

    # Read file content
    res = client.get(f"/api/generations/{gen_id}/files/style.css")
    assert res.status_code == 200
    file_info = res.json()
    assert file_info["content"] == "body { background: #000; }"

    # Path traversal attempt
    res = client.get(f"/api/generations/{gen_id}/files/../../etc/passwd")
    assert res.status_code in (400, 404)

    # Download ZIP
    res = client.get(f"/api/generations/{gen_id}/download")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    assert len(res.content) > 0
