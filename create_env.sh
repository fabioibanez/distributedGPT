# get the environment
python3 -m venv demo_dGPT
source demo_dGPT/bin/activate
pip3 install -r requirements.txt
cd MemGPT
pip3 install -e .
pip3 install termcolor
cd ..
cd distributedGPT
