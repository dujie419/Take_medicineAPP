from app.main import app


def test_plan_routes_are_registered_under_api_v1():
    paths = app.openapi()["paths"]
    routes = {
        (method.upper(), path)
        for path, operations in paths.items()
        for method in operations
    }

    expected_routes = {
        ("GET", "/api/v1/plans"),
        ("POST", "/api/v1/plans"),
        ("GET", "/api/v1/plans/{plan_id}"),
        ("PUT", "/api/v1/plans/{plan_id}"),
        ("PATCH", "/api/v1/plans/{plan_id}"),
        ("DELETE", "/api/v1/plans/{plan_id}"),
    }

    assert expected_routes <= routes
