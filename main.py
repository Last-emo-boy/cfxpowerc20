from web3 import Web3
from web3 import Account
from web3.middleware import geth_poa_middleware
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import argparse
import logging
import random

# from tqdm import tqdm


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# 合约定义
contract_abi = [
  {
    "constant": True,
    "inputs": [],
    "name": "challenge",
    "outputs": [{"name": "", "type": "uint256"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function"
  },
  {
    "constant": True,
    "inputs": [],
    "name": "difficulty",
    "outputs": [{"name": "", "type": "uint256"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function"
  },
  {
    "constant": True,
    "inputs": [{"name": "account", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "", "type": "uint256"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function"
  },
  {
    "constant": False,
    "inputs": [{"name": "nonce", "type": "uint256"}],
    "name": "mine",
    "outputs": [],
    "payable": False,
    "stateMutability": "nonpayable",
    "type": "function"
  }
]


class Miner:
    def __init__(self, private_key, contract_address, worker_count=10, log_level='light'):
        self.log_level = log_level
        self.w3 = Web3(Web3.HTTPProvider('https://evmtestnet.confluxrpc.com'))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        checksum_address = Web3.to_checksum_address(contract_address)
        self.contract = self.w3.eth.contract(address=checksum_address, abi=contract_abi)
        self.worker_count = worker_count
        self.stop_signal = False  # 添加一个标志来控制线程的停止
        self.stop_event = threading.Event()  # 创建一个 Event 对象


        # 打印当前的难度和挑战值
        self.print_current_difficulty_and_challenge()

    def print_current_difficulty_and_challenge(self):
        challenge = self.contract.functions.challenge().call()
        difficulty = self.contract.functions.difficulty().call()
        logging.info(f"Current Challenge: {challenge}")
        logging.info(f"Current Difficulty: {difficulty}")

    def get_challenge_and_difficulty(self):
        challenge = self.contract.functions.challenge().call()
        difficulty = self.contract.functions.difficulty().call()
        return challenge, difficulty

    def mine(self, worker_id, challenge, difficulty, target):
        count = 0
        start_time = time.time()
        system_random = random.SystemRandom()
        while not self.stop_event.is_set():
            # nonce = os.urandom(256)
            nonce = system_random.randint(0, 2**256 - 1)
            # nonce_int = int.from_bytes(nonce, byteorder='big')

            # 使用 keccak256 算法并按照合约中的方式组合数据
            data = Web3.solidity_keccak(['uint256', 'address', 'uint256'], [challenge, self.account.address, nonce])

            hash_value = int.from_bytes(data, byteorder='big')
            count += 1

            if self.difficulty != difficulty:
                # 如果难度发生变化，更新目标值
                logging.info(f"Difficulty changed: {self.difficulty}")
                target = self.target
                difficulty = self.difficulty

            # 'verbose' 模式下的详细日志记录
            if self.log_level == 'verbose' and count % 1000 == 0:
                elapsed_time = time.time() - start_time
                hashes_per_second = count / elapsed_time
                logging.info(f"Worker {worker_id}: {hashes_per_second:.2f} hashes/sec, Current Hash: {hash_value}, Count: {count}")

            # 'light' 模式下的简洁日志记录
            elif self.log_level == 'light' and count == 1:
                logging.info(f"Worker {worker_id} started mining.")

            if hash_value < target:
                # 发现有效 nonce，处理并发送交易
                self.handle_nonce(worker_id, nonce, start_time, count)

                # 重新获取挑战值和难度，继续挖矿
                challenge, difficulty = self.get_challenge_and_difficulty()
                target = (2**256 - 1) >> difficulty
                count = 0
                start_time = time.time()
    def handle_nonce(self, worker_id, nonce, start_time, count):
        if self.log_level == 'light':
            elapsed_time = time.time() - start_time
            hashes_per_second = count / elapsed_time
            logging.info(f"Worker {worker_id}: Total {count} hashes at {hashes_per_second:.2f} hashes/sec")
        logging.info(f"Worker {worker_id}: Nonce found - {hex(nonce)}")
        # 发送交易
        tx_receipt = self.send_transaction(nonce)
        logging.info(f"Transaction receipt: {tx_receipt}")


    def start_mining(self):
        challenge, difficulty = self.get_challenge_and_difficulty()
        target = (2**256 - 1) >> difficulty
        self.stop_signal = False

        threading.Thread(target=self.listen_for_difficulty_adjustment, daemon=True).start()

        try:
            with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
                futures = [executor.submit(self.mine, i, challenge, difficulty, target) for i in range(self.worker_count)]
                for future in as_completed(futures):
                    nonce = future.result()
                    tx_receipt = self.send_transaction(nonce)
                    logging.info(f"Transaction receipt: {tx_receipt}")
        except KeyboardInterrupt:
            self.stop_event.set()  # 设置事件，通知线程停止
            logging.info("Stopping mining process...")
            # 注意：不需要显式调用 executor.shutdown(wait=False)，因为 with 代码块结束时会自动调用


    def send_transaction(self, nonce):
        # 将 nonce 从 bytes 转换为 int
        nonce_int = Web3.to_int(nonce)

        # 构建事务
        tx = self.contract.functions.mine(nonce_int).build_transaction({
            'chainId': 71, # 主网为 1，对于测试网可能需要更改
            'gas': 2000000,
            'gasPrice': self.w3.to_wei('50', 'gwei'),
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })

         # 签署并发送事务
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)


        # 等待事务被挖掘
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        # if self.log_level == 'light':
            # logging.info(f"Transaction confirmed: {tx_receipt.transactionHash.hex()} in block {tx_receipt.blockNumber}")
        # 输出链上信息
        logging.info(f"Transaction Hash: {tx_receipt.transactionHash.hex()}")
        logging.info(f"Block Number: {tx_receipt.blockNumber}")
        logging.info(f"From: {tx_receipt['from']}")
        return tx_receipt

    def listen_for_difficulty_adjustment(self):
        event_filter = self.contract.events.DifficultyAdjusted.createFilter(fromBlock='latest')
        while not self.stop_signal:
            for event in event_filter.get_new_entries():
                new_difficulty = event['args']['newDifficulty']
                logging.info(f"Difficulty adjusted: {new_difficulty}")
                self.difficulty = new_difficulty
                self.target = (2**256 - 1) >> self.difficulty
            time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="Ethereum Miner")
    parser.add_argument('--private_key', required=True, help='Your Ethereum private key')
    parser.add_argument('--contract_address', required=True, help='Smart contract address')
    parser.add_argument('--worker_count', type=int, default=10, help='Number of worker threads (default: 10)')
    parser.add_argument('--log_level', choices=['light', 'verbose'], default='light', help='Set the logging level (light or verbose)')


    args = parser.parse_args()
    log_level = args.log_level

    
    try:
        miner = Miner(private_key=args.private_key, contract_address=args.contract_address, worker_count=args.worker_count, log_level=args.log_level)
        # 创建 Miner 实例并开始挖矿
        miner.start_mining()
    except KeyboardInterrupt:
        logging.info("程序被用户中断")

if __name__ == "__main__":
    main()
