"""Cliente HTTP do backend. Toda comunicação com a API passa por aqui."""
import requests


class BackendError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class Unauthorized(BackendError):
    """Token ausente, inválido ou expirado (HTTP 401)."""


class BackendUnavailable(BackendError):
    """Não foi possível conectar ao backend."""


def _detail(resp: requests.Response) -> str:
    try:
        detail = resp.json().get("detail")
    except ValueError:
        return resp.text or resp.reason or "Erro no backend"
    if isinstance(detail, list):  # erros de validação do FastAPI (422)
        return "; ".join(str(item.get("msg", item)) for item in detail)
    return str(detail) if detail else "Erro no backend"


class BackendClient:
    def __init__(self, base_url: str, token: str | None = None, timeout: float = 30, http=None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.http = http or requests.Session()

    # --- infraestrutura ---
    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            resp = self.http.request(method, self.base_url + path, headers=headers, timeout=self.timeout, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise BackendUnavailable(503, "Não foi possível conectar ao backend") from exc
        if resp.status_code == 401:
            raise Unauthorized(401, _detail(resp))
        if resp.status_code >= 400:
            raise BackendError(resp.status_code, _detail(resp))
        return resp

    # --- autenticação e usuários ---
    def login(self, username: str, password: str) -> str:
        resp = self._request("POST", "/login", json={"username": username, "password": password})
        return resp.json()["access_token"]

    def register(self, username: str, email: str, password: str) -> dict:
        payload = {"username": username, "email": email, "password": password}
        return self._request("POST", "/users", json=payload).json()

    def get_profile(self, username: str) -> dict:
        return self._request("GET", f"/users/{username}/profile").json()

    def get_profile_image(self, username: str) -> requests.Response:
        return self._request("GET", f"/users/{username}/profile/image", stream=True)

    def upload_profile_image(self, username: str, filename: str, stream, mimetype: str) -> dict:
        files = {"image": (filename, stream, mimetype)}
        return self._request("POST", f"/users/{username}/profile/image", files=files).json()

    # --- anotações ---
    def list_notes(self, username: str) -> list[dict]:
        return self._request("GET", f"/users/{username}/notes").json()

    def get_note(self, username: str, note_id: int) -> dict:
        return self._request("GET", f"/users/{username}/notes/{note_id}").json()

    def create_note(self, username: str, description: str) -> dict:
        return self._request("POST", f"/users/{username}/notes", json={"description": description}).json()

    def update_note(self, username: str, note_id: int, description: str) -> dict:
        return self._request("PUT", f"/users/{username}/notes/{note_id}", json={"description": description}).json()

    def delete_note(self, username: str, note_id: int) -> None:
        self._request("DELETE", f"/users/{username}/notes/{note_id}")

    # --- arquivos ---
    def list_files(self, username: str) -> list[dict]:
        return self._request("GET", f"/users/{username}/files").json()

    def get_file(self, username: str, file_id: int) -> dict:
        return self._request("GET", f"/users/{username}/files/{file_id}").json()

    def upload_file(self, username: str, filename: str, stream, mimetype: str) -> dict:
        files = {"file": (filename, stream, mimetype)}
        return self._request("POST", f"/users/{username}/files", files=files).json()

    def get_file_content(self, username: str, file_id: int) -> requests.Response:
        return self._request("GET", f"/users/{username}/files/{file_id}/content", stream=True)

    def delete_file(self, username: str, file_id: int) -> None:
        self._request("DELETE", f"/users/{username}/files/{file_id}")

    # --- gráficos ---
    def timeline(self) -> list[dict]:
        return self._request("GET", "/mytime").json()

    def tasks(self) -> list[dict]:
        return self._request("GET", "/mytasks").json()
