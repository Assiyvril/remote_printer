import traceback
from websockets import ConnectionClosedOK, ConnectionClosedError
from send_ntfy import NtfySender

Bug_Report = NtfySender()


class WsConnectionPool:
    """
    websocket连接池，全局只有一个实例，自维护连接
    """

    def __init__(self):
        self.printers = {}
        self.phones = {}

    async def add_printer(self, printer_id, websocket):
        self.printers[printer_id] = websocket

    async def add_phone(self, phone_id, websocket):
        if self.phone_exist(phone_id):
            await self.phones[phone_id].close()
        self.phones[phone_id] = websocket

    async def send_to_printer(self, printer_id, message):
        try:
            await self.printers[printer_id].send(message)
        except ConnectionClosedOK as e:
            await self.remove_printer(printer_id)
        except Exception as e:
            tf = traceback.format_exc()
            title = f'send_to_printer {str(e)}'
            Bug_Report.send_notification(title, tf)

    async def send_to_phone(self, phone_id, message):
        try:
            await self.phones[phone_id].send(message)
        except ConnectionClosedOK as e:
            await self.remove_phone(phone_id)
        except ConnectionClosedError as e:
            await self.remove_phone(phone_id)
        except Exception as e:
            await self.remove_phone(phone_id)
            tf = traceback.format_exc()
            title = f'send_to_phone {str(e)}'
            Bug_Report.send_notification(title, tf)

    async def remove_printer(self, printer_id):
        await self.printers[printer_id].close()
        del self.printers[printer_id]

    async def remove_phone(self, phone_id):
        await self.phones[phone_id].close()
        del self.phones[phone_id]

    def printer_exist(self, printer_id):
        if printer_id in self.printers.keys():
            return True
        return False

    def phone_exist(self, phone_id):
        if phone_id in self.phones.keys():
            return True
        return False

    async def clear_pool(self):
        # 检查连接池中的连接是否还在，不在则清除
        for printer_id, printer in self.printers.items():
            if printer.closed:
                await self.remove_printer(printer_id)

        # 清空连接池
        for printer in self.printers.values():
            await printer.close()
            del printer
        for phone in self.phones.values():
            await phone.close()
            del phone


Ws_Pool = WsConnectionPool()
