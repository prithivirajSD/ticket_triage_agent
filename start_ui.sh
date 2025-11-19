#!/bin/bash

# Use the port Render provides (default to 8501 if not set)
PORT=${PORT:-8501}

streamlit run streamlit_app/ui.py --server.port $PORT --server.address 0.0.0.0
