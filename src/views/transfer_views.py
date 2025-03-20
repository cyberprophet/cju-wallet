import time
import requests

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
)
from flask_wtf.csrf import generate_csrf
from src import db
from src.forms import TransferForm
from src.utils import p2p_utils
from src.wallet import Wallet
from src.config import PORT_P2P, SEED_NODE_IP, PORT_MINING

bp = Blueprint("transfer", __name__, url_prefix="/")


@bp.route("/transfer/", methods=["GET", "POST"])
def transfer():
    """코인 지갑 화면"""
    form = TransferForm()

    if request.method == "POST":
        data_dic = request.form.to_dict()
        print(f"data_dic: {data_dic}")

        send_blockchain_addr = data_dic.get("send_addr")
        amount = data_dic.get("amount")
        if not amount:
            return jsonify(
                {"status": "fail", "reason": "이체할 코인 수량을 입력해야 합니다."}
            )

        send_private_key = data_dic.get("private_key")
        if not send_private_key:
            return jsonify(
                {
                    "status": "fail",
                    "reason": "이체를 위해서는 반드시 본인의 비밀키를 입력해야 합니다.",
                }
            )

        send_public_key = data_dic.get("public_key")
        if not send_public_key:
            return jsonify(
                {
                    "status": "fail",
                    "reason": "이체를 위해서는 반드시 본인의 공개키를 입력해야 합니다.",
                }
            )

        recv_blockchain_addr = data_dic.get("recv_addr")
        if not recv_blockchain_addr:
            return jsonify(
                {"status": "fail", "reason": "받는사람 지갑 주소가 없습니다.."}
            )

        # 이체할 금액이 잔액보다 크다면 이체 중지
        blockchain_seed_node = f"http://{SEED_NODE_IP}:{PORT_MINING}/coin_amount"
        json_data = {"blockchain_addr": send_blockchain_addr}
        response = requests.post(blockchain_seed_node, json=json_data)
        data = response.json()
        current_amout = float(data["content"])
        print(f"tran amount: {amount}")
        print(f"current amount: {current_amout}")
        if float(amount) > current_amout:
            return jsonify({"status": "fail", "amount": "not_enough"})

        # Singnature 생성
        signature = Wallet.generate_signature(
            send_blockchain_addr=send_blockchain_addr,
            recv_blockchain_addr=recv_blockchain_addr,
            send_private_key=send_private_key,
            amount=float(amount),
        )
        # 보낼 정보 만들어서 blockchain node에게 전송
        json_data = {
            "send_public_key": send_public_key,
            "send_blockchain_addr": send_blockchain_addr,
            "recv_blockchain_addr": recv_blockchain_addr,
            "amount": float(amount),
            "signature": signature,
        }
        headers = {"X-CSRFToken": generate_csrf()}

        blockchain_seed_node = f"http://{SEED_NODE_IP}:{PORT_P2P}/neighbors"

        resp = requests.get(blockchain_seed_node)

        neighbors_dic = resp.json()

        for neighbor in neighbors_dic.values():
            ip, port = neighbor["ip"], neighbor["port"]

            node = p2p_utils.check_node_exist(ip, port)

            if not node:
                p2p_utils.add_new_node(ip, port)

            else:
                node.timestamp = time.time()

        neighbor_in_db = p2p_utils.get_all_nodes()

        for neighbor in neighbor_in_db:
            resp = requests.get(f"http://{neighbor.ip}:{PORT_MINING}/is_mining_active")

            resp_dic = resp.json()

            if resp_dic["status"] == "mining_active":
                neighbor_url = f"http://{neighbor.ip}:{PORT_MINING}/transactions"

                response = requests.post(
                    neighbor_url,
                    json=json_data,
                    headers=headers,
                )
                if response.status_code == 201:
                    neighbor.timestamp = time.time()

                    db.session.commit()

                    return jsonify({"status": "success", "amount": amount}), 201

        return (
            jsonify({"status": "fail", "reason": "블록체인 서버 연결에 실패했습니다."}),
            400,
        )

    return render_template(
        "transfer.html",
        form=form,
    )


@bp.route("/get_coin_amount/", methods=["GET"])
def get_coin_amount():
    blockchain_addr = request.args.get("blockchain_addr")
    print(f"blockchain_addr in get_coin_amount: {blockchain_addr}")

    if not blockchain_addr:
        return jsonify({"status": "fail"}), 400

    # Seed Node에게 우선 요청
    seed_node_url = f"http://{SEED_NODE_IP}:{PORT_MINING}/coin_amount"

    json_data = {"blockchain_addr": blockchain_addr}

    response = requests.post(
        url=seed_node_url,
        json=json_data,
    )
    data = response.json()

    if response.status_code == 201:
        return jsonify({"status": "success", "amount": data["content"]}), 200

    else:
        neighbors_in_db = p2p_utils.get_all_nodes()

        for neighbor in neighbors_in_db:
            if neighbor.id == SEED_NODE_IP:
                continue

            resp = requests.get(f"http://{neighbor.ip}:{PORT_MINING}/is_mining_active")

            resp_dic = resp.json()

            if resp_dic["status"] == "mining_active":
                neighbor_url = f"http://{neighbor.ip}:{PORT_MINING}/coin_amount"

                json_data = {
                    "blockchain_addr": blockchain_addr,
                }
                resp_coin_amount = requests.post(neighbor_url, json=json_data)

                if resp_coin_amount.status_code == 201:
                    data = resp_coin_amount.json()

                    neighbor.timestamp = time.time()

                    db.session.commit()
                    return (
                        jsonify({"status": "success", "amount": data["content"]}),
                        201,
                    )

        return (
            jsonify(
                {"status": "fail", "content": "블록체인 노드와 연결에 실패했습니다."}
            ),
            400,
        )
