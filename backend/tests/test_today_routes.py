from app.main import app


def test_today_routes_are_registered_under_api_v1():
    paths = app.openapi()["paths"]
    routes = {
        (method.upper(), path)
        for path, operations in paths.items()
        for method in operations
    }

    assert ("GET", "/api/v1/today") in routes
    assert ("POST", "/api/v1/medication-logs") in routes
