"""Frontend do MyFiles (Flask): interface web que consome a API do backend."""
import logging

import requests
from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect
from plotly.offline import get_plotlyjs
from werkzeug.exceptions import RequestEntityTooLarge

from web.api import BackendError, BackendUnavailable, Unauthorized
from web.config import DEFAULT_SECRET, Config

csrf = CSRFProtect()
logger = logging.getLogger("myfiles.web")


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)
    if app.config["SECRET_KEY"] == DEFAULT_SECRET and not app.testing:
        logger.warning("MY_SECRET_KEY não definida: usando chave de desenvolvimento.")

    csrf.init_app(app)
    # Sessão HTTP reaproveitada (pool de conexões com o backend)
    app.extensions["myfiles_http"] = requests.Session()

    from web.routes import auth, charts, dashboard, files, notes, profile

    for module in (auth, dashboard, notes, files, profile, charts):
        app.register_blueprint(module.bp)

    @app.route("/health")
    def health():
        """Verificação de saúde do container (não depende do backend)."""
        return {"status": "ok"}

    # plotly.js servido pelo próprio frontend (vem dentro do pacote plotly): sem depender de CDN
    @app.route("/vendor/plotly.min.js")
    def plotly_js():
        return Response(get_plotlyjs(), mimetype="application/javascript",
                        headers={"Cache-Control": "public, max-age=86400"})

    @app.context_processor
    def inject_globals():
        return {"current_user": session.get("username")}

    @app.template_filter("tamanho")
    def tamanho(num: int) -> str:
        for unidade in ("B", "KB", "MB"):
            if num < 1024:
                return f"{num:.0f} {unidade}" if unidade == "B" else f"{num:.1f} {unidade}"
            num /= 1024
        return f"{num:.1f} GB"

    @app.template_filter("data")
    def data(valor: str) -> str:
        # "2026-11-25T14:03:00..." -> "25/11/2026 14:03"
        if not valor or len(valor) < 16:
            return valor or ""
        return f"{valor[8:10]}/{valor[5:7]}/{valor[0:4]} {valor[11:16]}"

    @app.errorhandler(Unauthorized)
    def handle_unauthorized(_):
        session.clear()
        flash("Sua sessão expirou. Entre novamente.", "warning")
        return redirect(url_for("auth.login"))

    @app.errorhandler(BackendUnavailable)
    def handle_unavailable(exc):
        return render_template("error.html", status=503, message=exc.detail), 503

    @app.errorhandler(BackendError)
    def handle_backend_error(exc):
        status = exc.status_code if exc.status_code in (403, 404) else 502
        return render_template("error.html", status=status, message=exc.detail), status

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(_):
        limite = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024) - 1
        flash(f"Arquivo maior que o limite de {limite} MB.", "danger")
        return redirect(request.referrer or url_for("files.index"))

    @app.errorhandler(CSRFError)
    def handle_csrf(_):
        message = "O formulário expirou ou é inválido. Volte, recarregue a página e tente de novo."
        return render_template("error.html", status=400, message=message), 400

    @app.errorhandler(404)
    def handle_404(_):
        return render_template("error.html", status=404, message="Página não encontrada"), 404

    return app
