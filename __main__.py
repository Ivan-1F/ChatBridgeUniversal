from chat_bridge_universal.core.server import CBUServer

if __name__ == '__main__':
    server = CBUServer('./server_config.json')
    server.start()
