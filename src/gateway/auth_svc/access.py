import os

import requests

AUTH_REQUEST_TIMEOUT = float(os.environ.get("AUTH_REQUEST_TIMEOUT", "5"))
AUTH_SVC_ADDRESS = os.environ.get("AUTH_SVC_ADDRESS")

if not AUTH_SVC_ADDRESS:
    raise RuntimeError("AUTH_SVC_ADDRESS must be configured")


def login(request):
    auth = request.authorization
    if not auth:
        return None, ("missing credentials", 401)

    basic_auth = (auth.username, auth.password)

    try:
        response = requests.post(
            f"http://{AUTH_SVC_ADDRESS}/login",
            auth=basic_auth,
            timeout=AUTH_REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return None, ("auth service unavailable", 503)

    if response.status_code == 200:
        return response.text.strip(), None

    status = 401 if response.status_code in {401, 403} else 503
    return None, ("invalid credentials" if status == 401 else "auth service unavailable", status)
