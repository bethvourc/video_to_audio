import os

import requests

AUTH_REQUEST_TIMEOUT = float(os.environ.get("AUTH_REQUEST_TIMEOUT", "5"))


def token(request):
    if not "Authorization" in request.headers:
        return None, ("missing credentials", 401)

    token = request.headers["Authorization"]

    if not token:
        return None, ("missing credentials", 401)

    try:
        response = requests.post(
            f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/validate",
            headers={"Authorization": token},
            timeout=AUTH_REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return None, ("auth service unavailable", 503)

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
