from flask import Blueprint, flash, redirect, render_template, request, url_for

from web.api import BackendError
from web.routes.proxy import stream_response
from web.sessao import backend, current_username, login_required

bp = Blueprint("profile", __name__, url_prefix="/perfil")


@bp.route("")
@login_required
def index():
    profile = backend().get_profile(current_username())
    return render_template("profile.html", profile=profile)


@bp.route("/foto")
@login_required
def photo():
    upstream = backend().get_profile_image(current_username())
    return stream_response(upstream, cache_control="private, no-cache")


@bp.route("/foto", methods=["POST"])
@login_required
def upload_photo():
    image = request.files.get("image")
    if image is None or not image.filename:
        flash("Escolha uma imagem.", "danger")
        return redirect(url_for("profile.index"))
    try:
        backend().upload_profile_image(current_username(), image.filename, image.stream, image.mimetype)
    except BackendError as exc:
        if exc.status_code not in (400, 413, 422):
            raise
        flash(exc.detail, "danger")
    else:
        flash("Foto de perfil atualizada.", "success")
    return redirect(url_for("profile.index"))
