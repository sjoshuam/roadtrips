## run at the start of each session
source ~/env/roadtrips/bin/activate

## run initially to set up virtual environment
python3.12 -m venv ~/env/roadtrips
pip install --upgrade pip
pip install pandas==2.2.2 plotly==5.22.0 scikit-learn==1.5.1 pyproj==3.6.1 openpyxl==3.1.5

echo ".*
io_mid/*
__pycache__" > .gitignore
