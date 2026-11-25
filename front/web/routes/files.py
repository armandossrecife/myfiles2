from flask import Blueprint, flash, redirect, render_template, request, url_for

from web.api import BackendError
from web.routes.proxy import stream_response
from web.sessao import backend, current_username, login_required

bp = Blueprint("files", __name__, url_prefix="/arquivos")

ACCEPT = ".jpg,.jpeg,.png,.mp4,.mp3"


@bp.route("")
@login_required
def index():
    files = backend().list_files(current_username())
    return render_template("files/list.html", files=files, accept=ACCEPT)


@bp.route("", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    if file is None or not file.filename:
        flash("Escolha um arquivo para enviar.", "danger")
        return redirect(url_for("files.index"))
    try:
        meta = backend().upload_file(current_username(), file.filename, file.stream, file.mimetype)
    except BackendError as exc:
        if exc.status_code not in (400, 413, 422):
            raise
        flash(exc.detail, "danger")
        return redirect(url_for("files.index"))
    flash(f"Arquivo {meta['original_name']} enviado.", "success")
    return redirect(url_for("files.view", file_id=meta["id"]))


@bp.route("/<int:file_id>")
@login_required
def view(file_id: int):
    meta = backend().get_file(current_username(), file_id)
    kind = meta["media_type"].split("/", 1)[0]  # image | video | audio
    return render_template("files/view.html", file=meta, kind=kind)


@bp.route("/<int:file_id>/conteudo")
@login_required
def content(file_id: int):
    upstream = backend().get_file_content(current_username(), file_id)
    return stream_response(upstream)


@bp.route("/<int:file_id>/excluir", methods=["POST"])
@login_required
def delete(file_id: int):
    backend().delete_file(current_username(), file_id)
    flash("Arquivo excluído.", "success")
    return redirect(url_for("files.index"))
