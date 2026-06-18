import os

import requests

AUTH_REQUEST_TIMEOUT = float(os.environ.get("AUTH_REQUEST_TIMEOUT", "5"))


def login(request):
    auth = request.authorization
    if not auth:
        return None, ("missing credentials", 401)

    basicAuth = (auth.username, auth.password)

    try:
        response = requests.post(
            f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login",
            auth=basicAuth,
            timeout=AUTH_REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return None, ("auth service unavailable", 503)

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
