@echo off
cd C:\Users\olayi\Desktop\construction_spec_analyzer
call venv\Scripts\activate
start http://localhost:8501
streamlit run app.py
