def test_crud_completo_de_anotacoes(client, alice):
    base = "/users/alice/notes"
    assert client.get(base, headers=alice).json() == []

    criada = client.post(base, json={"description": "Primeira nota"}, headers=alice)
    assert criada.status_code == 201
    note_id = criada.json()["id"]

    assert client.get(f"{base}/{note_id}", headers=alice).json()["description"] == "Primeira nota"

    editada = client.put(f"{base}/{note_id}", json={"description": "Nota editada"}, headers=alice)
    assert editada.status_code == 200
    assert editada.json()["description"] == "Nota editada"

    lista = client.get(base, headers=alice).json()
    assert [n["description"] for n in lista] == ["Nota editada"]

    assert client.delete(f"{base}/{note_id}", headers=alice).status_code == 204
    assert client.get(f"{base}/{note_id}", headers=alice).status_code == 404
    assert client.get(base, headers=alice).json() == []


def test_descricao_vazia_ou_longa_demais_devolve_422(client, alice):
    base = "/users/alice/notes"
    assert client.post(base, json={"description": ""}, headers=alice).status_code == 422
    assert client.post(base, json={"description": "x" * 1025}, headers=alice).status_code == 422


def test_nota_inexistente_devolve_404(client, alice):
    base = "/users/alice/notes"
    assert client.get(f"{base}/999", headers=alice).status_code == 404
    assert client.put(f"{base}/999", json={"description": "x"}, headers=alice).status_code == 404
    assert client.delete(f"{base}/999", headers=alice).status_code == 404


def test_usuario_nao_acessa_notas_de_outro(client, alice, bob):
    note_id = client.post("/users/alice/notes", json={"description": "privada"}, headers=alice).json()["id"]

    # pela URL do outro usuário: 403
    assert client.get("/users/alice/notes", headers=bob).status_code == 403
    assert client.post("/users/alice/notes", json={"description": "x"}, headers=bob).status_code == 403
    # pela própria URL, usando o id da nota alheia: 404
    assert client.get(f"/users/bob/notes/{note_id}", headers=bob).status_code == 404
    assert client.put(f"/users/bob/notes/{note_id}", json={"description": "hack"}, headers=bob).status_code == 404
    assert client.delete(f"/users/bob/notes/{note_id}", headers=bob).status_code == 404

    assert client.get(f"/users/alice/notes/{note_id}", headers=alice).json()["description"] == "privada"


def test_notas_sem_token_devolve_401(client):
    assert client.get("/users/alice/notes").status_code == 401
