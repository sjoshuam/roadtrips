## start
source ~/env/roadtrips/bin/activate

## initialize
python3.12 -m venv ~/env/roadtrips
pip install --upgrade pip
pip install pandas==2.2.2 plotly==5.22.0 scikit-learn==1.5.1 pyproj==3.6.1 openpyxl==3.1.5

echo ".*
io_mid/*
__pycache__" > .gitignore

## DEPRECIATED - CONDA BASED ROUTE
#source ~/.zshrc
#conda update --all -y
#conda create --name rpy python=3.12 numpy=1.26 pandas=2.1 plotly=5.18 scikit-learn openpyxl python-kaleido pyproj -c conda-forge -y
#echo 'alias rpy=~/miniconda/envs/rpy/bin/python3.12' >> ~/.zshrc
#source ~/.zshrc
#conda activate rpy
#echo '*.' > .gitignore
#echo 'io_mid/*' >> .gitignore
#echo '__pycache__/*' >> .gitignore