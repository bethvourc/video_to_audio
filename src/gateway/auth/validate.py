import os

import requests

AUTH_REQUEST_TIMEOUT = float(os.environ.get("AUTH_REQUEST_TIMEOUT", "5"))
AUTH_SVC_ADDRESS = os.environ.get("AUTH_SVC_ADDRESS")

if not AUTH_SVC_ADDRESS:
    raise RuntimeError("AUTH_SVC_ADDRESS must be configured")


def token(request):
    if "Authorization" not in request.headers:
        return None, ("missing credentials", 401)

    token = request.headers["Authorization"]

    if not token:
        return None, ("missing credentials", 401)

    try:
        response = requests.post(
            f"http://{AUTH_SVC_ADDRESS}/validate",
            headers={"Authorization": token},
            timeout=AUTH_REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return None, ("auth service unavailable", 503)

    if response.status_code != 200:
        status = 401 if response.status_code in {401, 403} else 503
        return None, ("not authorized" if status == 401 else "auth service unavailable", status)

    try:
        claims = response.json()
    except requests.JSONDecodeError:
        return None, ("auth service unavailable", 503)

    if (
        not isinstance(claims, dict)
        or not isinstance(claims.get("username"), str)
        or not claims["username"]
        or not isinstance(claims.get("admin"), bool)
    ):
        return None, ("auth service unavailable", 503)

    return claims, None
