from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from web.api import BackendError, Unauthorized
from web.sessao import backend, start_session

bp = Blueprint("auth", __name__)


def _safe_next(target: str | None) -> str:
    """Só aceita redirecionar para caminhos internos (evita open redirect)."""
    if target and target.startswith("/") and not target.startswith("//") and not urlsplit(target).netloc:
        return target
    return url_for("dashboard.index")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Informe usuário e senha.", "danger")
            return render_template("auth/login.html", username=username), 400
        try:
            token = backend().login(username, password)
        except Unauthorized:
            flash("Usuário ou senha incorretos.", "danger")
            return render_template("auth/login.html", username=username), 401
        start_session(username, token)
        return redirect(_safe_next(request.args.get("next")))
    if "access_token" in session:
        return redirect(url_for("dashboard.index"))
    return render_template("auth/login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in ("username", "email")}
        password = request.form.get("password", "")
        repassword = request.form.get("repassword", "")

        error = None
        if not form["username"]:
            error = "Informe um nome de usuário."
        elif not form["email"]:
            error = "Informe um e-mail."
        elif len(password) < 6:
            error = "A senha precisa ter pelo menos 6 caracteres."
        elif password != repassword:
            error = "As senhas não conferem."

        if error is None:
            try:
                backend().register(form["username"], form["email"], password)
            except BackendError as exc:
                error = exc.detail
            else:
                flash(f"Conta {form['username']} criada. Entre com sua senha.", "success")
                return redirect(url_for("auth.login"))

        flash(error, "danger")
        return render_template("auth/register.html", **form), 400
    return render_template("auth/register.html")


@bp.route("/forgot-password")
def forgot():
    return render_template("auth/forgot_password.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("auth.login"))
