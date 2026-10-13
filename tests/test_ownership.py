"""Tests for multi-tenant ownership enforcement, cross-tenant isolation, and RBAC roles."""
import uuid
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from api.main import app
from api.db.session import SessionLocal
from api.db.models.user import User
from api.db.models.organization import Organization, Membership
from api.services.generation_service import generation_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_agent_runners():
    with patch("api.services.generation_service.run_agent_generation", new_callable=AsyncMock), \
         patch("api.services.generation_service.run_agent_refinement", new_callable=AsyncMock):
        yield


@pytest.fixture
def tenancy_setup(tmp_path):
    """Sets up two distinct organizations with users and roles."""
    generation_service.storage_dir = tmp_path

    db = SessionLocal()
    suffix = uuid.uuid4().hex[:6]
    email_a = f"alice-{suffix}@alpha.com"
    email_viewer = f"viewer-{suffix}@alpha.com"
    email_b = f"bob-{suffix}@beta.com"

    try:
        # Organization 1 (Alpha Corp)
        org_a = Organization(id=uuid.uuid4(), name="Alpha Corp", slug=f"alpha-corp-{suffix}")
        user_a = User(id=uuid.uuid4(), email=email_a, status="active")
        mem_a = Membership(id=uuid.uuid4(), user_id=user_a.id, organization_id=org_a.id, role="owner")

        # Viewer in Organization 1
        user_viewer = User(id=uuid.uuid4(), email=email_viewer, status="active")
        mem_viewer = Membership(id=uuid.uuid4(), user_id=user_viewer.id, organization_id=org_a.id, role="viewer")

        # Organization 2 (Beta LLC)
        org_b = Organization(id=uuid.uuid4(), name="Beta LLC", slug=f"beta-llc-{suffix}")
        user_b = User(id=uuid.uuid4(), email=email_b, status="active")
        mem_b = Membership(id=uuid.uuid4(), user_id=user_b.id, organization_id=org_b.id, role="owner")

        db.add_all([org_a, user_a, mem_a, user_viewer, mem_viewer, org_b, user_b, mem_b])
        db.commit()

        yield {
            "user_a_headers": {"X-User-Email": email_a},
            "user_b_headers": {"X-User-Email": email_b},
            "viewer_headers": {"X-User-Email": email_viewer},
        }
    finally:
        db.close()


def test_cross_tenant_isolation_user_b_cannot_access_user_a(tenancy_setup):
    """User B must receive 404 when trying to access User A's generation even with known UUID."""
    headers_a = tenancy_setup["user_a_headers"]
    headers_b = tenancy_setup["user_b_headers"]

    # 1. User A creates a generation in Organization A
    res_create = client.post(
        "/api/generations",
        json={"prompt": "Confidential internal app for Alpha Corp"},
        headers=headers_a,
    )
    assert res_create.status_code == 201
    gen_a_id = res_create.json()["id"]

    # 2. User A can view their generation
    res_a = client.get(f"/api/generations/{gen_a_id}", headers=headers_a)
    assert res_a.status_code == 200
    assert res_a.json()["id"] == gen_a_id

    # 3. User B attempts to access User A's generation -> 404 Not Found
    res_b_get = client.get(f"/api/generations/{gen_a_id}", headers=headers_b)
    assert res_b_get.status_code == 404
    assert res_b_get.json()["detail"] == "Generation run not found"

    # 4. User B attempts to access files -> 404 Not Found
    res_b_files = client.get(f"/api/generations/{gen_a_id}/files", headers=headers_b)
    assert res_b_files.status_code == 404

    # 5. User B attempts to download ZIP -> 404 Not Found
    res_b_dl = client.get(f"/api/generations/{gen_a_id}/download", headers=headers_b)
    assert res_b_dl.status_code == 404

    # 6. User B attempts to refine User A's generation -> 404 Not Found
    res_b_refine = client.post(
        f"/api/generations/{gen_a_id}/refine",
        json={"prompt": "Malicious edit attempt"},
        headers=headers_b,
    )
    assert res_b_refine.status_code == 404

    # 7. User B attempts to cancel User A's generation -> 404 Not Found
    res_b_cancel = client.post(f"/api/generations/{gen_a_id}/cancel", headers=headers_b)
    assert res_b_cancel.status_code == 404

    # 8. User B listing generations does NOT see User A's generation
    res_b_list = client.get("/api/generations", headers=headers_b)
    assert res_b_list.status_code == 200
    assert not any(run["id"] == gen_a_id for run in res_b_list.json())


def test_viewer_role_policy_read_only(tenancy_setup):
    """Viewers can read and download, but get 403 Forbidden on create, refine, and cancel."""
    headers_a = tenancy_setup["user_a_headers"]
    headers_viewer = tenancy_setup["viewer_headers"]

    # User A creates a generation
    res_create = client.post(
        "/api/generations",
        json={"prompt": "Shared organization project"},
        headers=headers_a,
    )
    assert res_create.status_code == 201
    gen_id = res_create.json()["id"]

    # Viewer CAN read generation details (200 OK)
    res_viewer_get = client.get(f"/api/generations/{gen_id}", headers=headers_viewer)
    assert res_viewer_get.status_code == 200

    # Viewer CAN download ZIP (200 OK)
    res_viewer_dl = client.get(f"/api/generations/{gen_id}/download", headers=headers_viewer)
    assert res_viewer_dl.status_code == 200

    # Viewer CANNOT create generation -> 403 Forbidden
    res_viewer_create = client.post(
        "/api/generations",
        json={"prompt": "Viewer attempt to create"},
        headers=headers_viewer,
    )
    assert res_viewer_create.status_code == 403
    assert "Viewer role has read-only access" in res_viewer_create.json()["detail"]

    # Viewer CANNOT refine generation -> 403 Forbidden
    res_viewer_refine = client.post(
        f"/api/generations/{gen_id}/refine",
        json={"prompt": "Viewer attempt to refine"},
        headers=headers_viewer,
    )
    assert res_viewer_refine.status_code == 403
    assert "Viewer role has read-only access" in res_viewer_refine.json()["detail"]

    # Viewer CANNOT cancel generation -> 403 Forbidden
    res_viewer_cancel = client.post(f"/api/generations/{gen_id}/cancel", headers=headers_viewer)
    assert res_viewer_cancel.status_code == 403
    assert "Viewer role has read-only access" in res_viewer_cancel.json()["detail"]
