from flask import Blueprint, flash, redirect, render_template, request, url_for

from web.api import BackendError
from web.sessao import backend, current_username, login_required

bp = Blueprint("notes", __name__, url_prefix="/notas")


@bp.route("")
@login_required
def index():
    notes = backend().list_notes(current_username())
    return render_template("notes/list.html", notes=notes)


@bp.route("", methods=["POST"])
@login_required
def create():
    description = request.form.get("description", "").strip()
    if not description:
        flash("Escreva algo antes de salvar a anotação.", "danger")
        return redirect(url_for("notes.index"))
    try:
        backend().create_note(current_username(), description)
    except BackendError as exc:
        if exc.status_code != 422:
            raise
        flash(f"Anotação inválida: {exc.detail}", "danger")
    else:
        flash("Anotação salva.", "success")
    return redirect(url_for("notes.index"))


@bp.route("/<int:note_id>/editar", methods=["GET", "POST"])
@login_required
def edit(note_id: int):
    api, username = backend(), current_username()
    if request.method == "POST":
        description = request.form.get("description", "").strip()
        if not description:
            flash("A anotação não pode ficar vazia.", "danger")
            return redirect(url_for("notes.edit", note_id=note_id))
        api.update_note(username, note_id, description)
        flash("Anotação atualizada.", "success")
        return redirect(url_for("notes.index"))
    note = api.get_note(username, note_id)
    return render_template("notes/edit.html", note=note)


@bp.route("/<int:note_id>/excluir", methods=["POST"])
@login_required
def delete(note_id: int):
    backend().delete_note(current_username(), note_id)
    flash("Anotação excluída.", "success")
    return redirect(url_for("notes.index"))
