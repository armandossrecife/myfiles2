#!/bin/bash
echo "Executa a aplicação backend (http://localhost:8000/docs)"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
