import io

import pytest

from app import create_app


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def register(client, name="Test Student", email="student@example.com", password="secret1"):
    return client.post("/auth", data={
        "register_submit": "1",
        "name": name,
        "email": email,
        "password": password,
        "confirm_password": password,
    }, follow_redirects=True)


def login(client, email="student@example.com", password="secret1"):
    return client.post("/auth", data={
        "login_submit": "1",
        "email": email,
        "password": password,
    }, follow_redirects=True)


def test_home_route(client):
    response = client.get("/")
    assert response.status_code == 200


def test_auth_route(client):
    response = client.get("/auth")
    assert response.status_code == 200


def test_resources_route(client):
    response = client.get("/resources")
    assert response.status_code == 200


def test_categories_are_seeded(app):
    with app.app_context():
        from models import Category
        assert Category.query.count() == 8
        assert Category.query.filter_by(key="practical").first() is not None


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login to Your Account" in response.data


def test_admin_requires_admin_role(client):
    register(client)
    login(client)
    response = client.get("/admin", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login to Your Account" in response.data


def test_register_and_login_flow(client):
    register_response = register(client)
    assert b"Registration successful" in register_response.data

    login_response = login(client)
    assert b"Login successful" in login_response.data

    dashboard_response = client.get("/dashboard")
    assert dashboard_response.status_code == 200
    assert b"Test Student" in dashboard_response.data


def test_duplicate_registration_is_rejected(client):
    register(client)
    second_attempt = register(client)
    assert b"Email already exists" in second_attempt.data


def test_upload_requires_login(client):
    response = client.get("/upload", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login to Your Account" in response.data


def test_upload_rejects_disallowed_file_type(client):
    register(client)
    login(client)

    data = {
        "title": "Malicious File",
        "category": "practical",
        "description": "test",
        "resource_file": (io.BytesIO(b"fake binary content"), "malware.exe"),
    }
    response = client.post(
        "/upload", data=data, content_type="multipart/form-data", follow_redirects=True,
    )
    assert b"not allowed" in response.data


def test_upload_and_view_resource(client):
    register(client)
    login(client)

    data = {
        "title": "Python Notes",
        "category": "practical",
        "description": "Basic python notes",
        "resource_file": (io.BytesIO(b"%PDF-1.4 fake pdf content"), "notes.pdf"),
    }
    upload_response = client.post(
        "/upload", data=data, content_type="multipart/form-data", follow_redirects=True,
    )
    assert b"Resource uploaded successfully" in upload_response.data

    resources_response = client.get("/resources")
    assert b"Python Notes" in resources_response.data
