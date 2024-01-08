source ~/.zshrc
conda update --all -y
conda create --name rpy python=3.12 numpy=1.26 pandas=2.1 plotly=5.18 scikit-learn openpyxl python-kaleido pyproj -c conda-forge -y
echo 'alias rpy=~/miniconda/envs/rpy/bin/python3.12' >> ~/.zshrc
source ~/.zshrc
conda activate rpy
echo '*.' > .gitignore
echo 'io_mid/*' >> .gitignore
echo '__pycache__/*' >> .gitignore