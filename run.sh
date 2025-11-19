#!/bin/bash
# Start FastAPI backend

 # after the uvicorn work then new terminal in vscode and now start Streamlit UI
streamlit run streamlit_app/ui.py

uvicorn app.main:app --reload

# 1. database open a firebase account just signup/login
# 2. create a new project and create a firebase firestore
# 3. then in project overview side the setting icon click -> project setting -> web apps and click on add web app -> 
# then you can copy the details of db and paste it in .env file 

# by Prithiviraj S D  
