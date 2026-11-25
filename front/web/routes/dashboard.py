from flask import Blueprint, redirect, render_template, session, url_for

from web.sessao import backend, current_username, login_required

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def root():
    return redirect(url_for("dashboard.index" if "access_token" in session else "auth.login"))


@bp.route("/dashboard")
@login_required
def index():
    api, username = backend(), current_username()
    profile = api.get_profile(username)
    notes = api.list_notes(username)
    files = api.list_files(username)
    return render_template(
        "dashboard.html",
        profile=profile,
        notes_count=len(notes),
        files_count=len(files),
        recent_notes=list(reversed(notes))[:3],
        recent_files=list(reversed(files))[:5],
    )
