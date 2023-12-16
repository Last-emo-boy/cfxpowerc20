# cfxpowerc20

## 项目描述

这是一个 Conflux eSpace 挖矿工具，专门设计用于与 Conflux eSpace 智能合约进行交互以执行挖矿操作。该脚本利用 Web3.py 与 Conflux eSpace 网络进行通信，并通过多线程执行挖矿过程，实现了在找到有效的 nonce 后与智能合约的交互。灵感来自于[PoWERC20项目](https://powerc20.com/)

## 安装指南

要使用此脚本，您需要安装 Python 和所需环境。请按照以下步骤操作：

1. 安装 Python：访问 [Python 官网](https://www.python.org/) 并下载适合您操作系统的版本。
2. 安装所需环境：打开命令行或终端，运行以下命令：

   ```bash
   pip install -r requirements.txt
   ```

## 使用说明

运行挖矿脚本需要以下命令行参数：

```bash
python main.py --private_key YOUR_PRIVATE_KEY --contract_address CONTRACT_ADDRESS --worker_count WORKER_COUNT --log_level LOG_LEVEL
```

参数说明：

- `YOUR_PRIVATE_KEY`: 您的 Conflux eSpace 地址私钥。
- `CONTRACT_ADDRESS`: 智能合约的地址。
- `WORKER_COUNT`: （可选）工作线程数量，默认为 10。
- `LOG_LEVEL`: （可选）日志级别，可以是 "light" 或 "verbose"，默认为 "light"。

## 配置说明

确保您的智能合约地址和私钥正确无误。提供有效的 Conflux eSpace 私钥和智能合约地址是进行挖矿的前提。

## 许可证

本项目采用 GNU General Public License 发布。有关详细信息，请参阅项目中的 `LICENSE` 文件。