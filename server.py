# import websockets
import asyncio
from websockets.asyncio.server import serve
from web_socket_message_handle import Message_Handler
import ssl
import pathlib
# from websocket_connection_pool import Ws_Pool


async def sub_handle(websocket, path=None):
    try:
        async for message in websocket:
            data = Message_Handler.deserialize_message(message)
            message_type = data.get("type")
            if message_type == 'device_online':
                await Message_Handler.handle_device_online(data, websocket)
            elif message_type == 'device_offline':
                await Message_Handler.handle_device_offline(data)
            elif message_type == 'print_task':
                await Message_Handler.handle_print_task(data)
            elif message_type == 'print_complete':
                await Message_Handler.handle_print_complete(data)
    except Exception as e:
        print(e)
        pass

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
localhost_pem = r'/www/server/panel/vhost/cert/down.slpzb.com/privkey.pem'
ssl_context.load_cert_chain(localhost_pem)


async def main():
    async with serve(sub_handle, "0.0.0.0", 8765, ssl=ssl_context) as server:
        print('server start')
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
