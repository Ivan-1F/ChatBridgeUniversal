from chat_bridge_universal.core.server import ChatBridgeUniversalServer

if __name__ == '__main__':
    server = ChatBridgeUniversalServer('./server_config.json')
    server.start()
