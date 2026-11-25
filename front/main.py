"""Ponto de entrada: flask --app main run --host=0.0.0.0 --port=5001"""
from web import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
