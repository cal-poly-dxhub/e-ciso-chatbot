cd /home/ec2-user/eciso-poc
source .venv/bin/activate
streamlit run src/lit.py > /home/ec2-user/eciso-poc/logs/output.log  2> /home/ec2-user/eciso-poc/logs/error.log  < /dev/null &
