# Activate local environment
source .venv/Scripts/activate

# Start App
streamlit run app.py

# Requirements automatisch generieren
pip freeze>requirements.txt