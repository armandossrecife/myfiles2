#!/bin/bash
echo "Executa a aplicação frontend (http://localhost:5001)"
flask --app main run --host=0.0.0.0 --port=5001
