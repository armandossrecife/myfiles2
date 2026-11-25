"""Dados de demonstração para os gráficos do dashboard (Plotly no frontend)."""
from dataclasses import dataclass
from datetime import date, timedelta

from fastapi import APIRouter, Depends

from api import entidades, modelos, seguranca

router = APIRouter(tags=["gráficos"])


@dataclass
class Tarefa:
    descricao: str
    data_expiracao: date
    prioridade: int
    concluida: bool = False

    def to_dict(self) -> dict:
        return {
            "descricao": self.descricao,
            "data_expiracao": self.data_expiracao.strftime("%d/%m/%Y"),
            "prioridade": self.prioridade,
            "concluida": self.concluida,
        }


@router.get("/mytime", response_model=list[entidades.TimelineItem])
def timeline(_: modelos.UserDB = Depends(seguranca.get_current_user)):
    return [
        {"Task": "Job A", "Start": "2009-01-01", "Finish": "2009-02-28"},
        {"Task": "Job B", "Start": "2009-03-05", "Finish": "2009-04-15"},
        {"Task": "Job C", "Start": "2009-02-20", "Finish": "2009-05-30"},
    ]


@router.get("/mytasks", response_model=list[entidades.TaskOut])
def tasks(_: modelos.UserDB = Depends(seguranca.get_current_user)):
    hoje = date.today()
    tarefas = [
        Tarefa("Tarefa 1", hoje + timedelta(days=5), 1),
        Tarefa("Tarefa 2", hoje + timedelta(days=10), 2),
        Tarefa("Tarefa 3", hoje + timedelta(days=3), 3),
    ]
    return [t.to_dict() for t in tarefas]
