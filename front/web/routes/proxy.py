"""Repassa ao navegador um conteúdo binário vindo do backend.

Assim o navegador só fala com o frontend: o backend não precisa ficar exposto
e o token JWT nunca vai para o HTML.
"""
from flask import Response, stream_with_context

PASS_HEADERS = ("Content-Type", "Content-Length", "Content-Disposition", "Last-Modified", "ETag")


def stream_response(upstream, cache_control: str = "private, max-age=0") -> Response:
    def generate():
        try:
            yield from upstream.iter_content(chunk_size=64 * 1024)
        finally:
            upstream.close()

    headers = {h: upstream.headers[h] for h in PASS_HEADERS if h in upstream.headers}
    headers["Cache-Control"] = cache_control
    return Response(stream_with_context(generate()), status=200, headers=headers)
