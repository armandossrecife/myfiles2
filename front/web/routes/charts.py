import pandas as pd
import plotly.express as px
from flask import Blueprint, render_template

from web.sessao import backend, login_required

bp = Blueprint("charts", __name__, url_prefix="/graficos")


@bp.route("/tempo")
@login_required
def timeline():
    dados = backend().timeline()
    graph_json = None
    if dados:
        fig = px.timeline(pd.DataFrame(dados), x_start="Start", x_end="Finish", y="Task")
        fig.update_yaxes(autorange="reversed")
        graph_json = fig.to_json()
    return render_template("charts/timeline.html", graph_json=graph_json)


@bp.route("/tarefas")
@login_required
def tasks():
    return render_template("charts/tasks.html", tarefas=backend().tasks())
