"""Sessão do usuário logado e acesso ao cliente do backend."""
from functools import wraps

from flask import current_app, flash, redirect, request, session, url_for

from web.api import BackendClient


def backend() -> BackendClient:
    return BackendClient(
        current_app.config["BACKEND_URL"],
        token=session.get("access_token"),
        timeout=current_app.config["BACKEND_TIMEOUT"],
        http=current_app.extensions["myfiles_http"],
    )


def current_username() -> str:
    return session["username"]


def start_session(username: str, token: str) -> None:
    session.clear()
    session["username"] = username
    session["access_token"] = token


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "access_token" not in session:
            flash("Entre na sua conta para continuar.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapper
