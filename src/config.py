import os
from src.secret import csrf_token_secret

BASE_DIR = os.path.dirname(__file__)

SQLALCHEMY_DATABASE_URI = "sqlite:///{}".format(os.path.join(BASE_DIR, "wallet.db"))

SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = csrf_token_secret

# 비밀번호 최소 길이
MIN_LENGTH_OF_PASSWD = 7

# Seed Node (Server) IP addr
SEED_NODE_IP = "127.0.0.1"

# PORT 정보
PORT_MINING = "39456"

PORT_P2P = "22901"
