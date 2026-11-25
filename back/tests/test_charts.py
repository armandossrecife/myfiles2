def test_mytime(client, alice):
    dados = client.get("/mytime", headers=alice).json()
    assert isinstance(dados, list) and len(dados) == 3
    assert set(dados[0]) == {"Task", "Start", "Finish"}


def test_mytasks(client, alice):
    dados = client.get("/mytasks", headers=alice).json()
    assert [t["prioridade"] for t in dados] == [1, 2, 3]
    assert all(t["concluida"] is False for t in dados)


def test_graficos_exigem_login(client):
    assert client.get("/mytime").status_code == 401
    assert client.get("/mytasks").status_code == 401
