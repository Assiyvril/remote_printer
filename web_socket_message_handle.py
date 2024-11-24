import json
from websocket_connection_pool import Ws_Pool
from enum import Enum


class SystemMessage(Enum):
    """
    定义系统消息类型
    """
    # 握手成功
    HAND_SHAKE_SUCCESS = {
        "type": "hand_shake_success",
        "status": "success",
        "message": "连接成功，设备就绪",
        "device_type": "system",
        "device_id": "system"
    }
    # 等待打印机连接
    WAITING_PRINTER = {
        "type": "waiting_printer",
        "status": "info",
        "message": "等待打印机连接",
        "device_type": "system",
        "device_id": "system"
    }
    # 等待手机连接
    WAITING_PHONE = {
        "type": "waiting_phone",
        "status": "info",
        "message": "等待手机连接",
        "device_type": "system",
        "device_id": "system"
    }
    # 打印机掉线 向打印机发送指令失败时，给手机发送此消息
    PRINTER_OFFLINE = {
        "type": "printer_offline",
        "status": "error",
        "message": "打印机掉线",
        "device_type": "system",
        "device_id": "system"
    }
    # 手机掉线后 ， 向打印机发送此消息
    PHONE_OFFLINE = {
        "type": "phone_offline",
        "status": "error",
        "message": "手机掉线",
        "device_type": "system",
        "device_id": "system"
    }


class WsMessageHandle:
    """
    websocket消息处理类，处理：
    1，设备上线  {"type": "device_online", "device_id": "xxxx", "device_type": "printer"}
    2，设备下线  {"type": "device_offline", "device_id": "xxxx", "device_type": "printer"}
    3, 手机发送打印任务 {"type": "print_task", "device_id": "xxxx", "device_type": "phone", "data": "xxxx"}
    4, 打印机打印完成 {"type": "print_complete", "device_id": "xxxx", "device_type": "printer"}
    """

    def __init__(self, ws_pool):
        self.ws_pool = ws_pool

    def serialize_message(self, message):
        """
        序列化消息，将字典转换为json字符串, 以便发送给设备
        """
        return json.dumps(message)

    def deserialize_message(self, message):
        """
        反序列化消息，将设备发送的json字符串转换为字典
        """
        return json.loads(message)

    async def handle_device_online(self, message, websocket):
        device_id = message.get("device_id")
        device_type = message.get("device_type")
        if device_type == "printer":
            await self.ws_pool.add_printer(device_id, websocket)
            if self.ws_pool.phone_exist(device_id):
                # 手机也在线，则握手成功
                await self.ws_pool.send_to_phone(device_id, self.serialize_message(SystemMessage.HAND_SHAKE_SUCCESS.value))
                await self.ws_pool.send_to_printer(device_id, self.serialize_message(SystemMessage.HAND_SHAKE_SUCCESS.value))
            else:
                # 手机不在线，则等待手机连接
                await self.ws_pool.send_to_printer(device_id, self.serialize_message(SystemMessage.WAITING_PHONE.value))
        elif device_type == "phone":
            await self.ws_pool.add_phone(device_id, websocket)
            if self.ws_pool.printer_exist(device_id):
                # 打印机也在线，则握手成功
                await self.ws_pool.send_to_printer(device_id, self.serialize_message(SystemMessage.HAND_SHAKE_SUCCESS.value))
                await self.ws_pool.send_to_phone(device_id, self.serialize_message(SystemMessage.HAND_SHAKE_SUCCESS.value))
            else:
                # 打印机不在线，则等待打印机连接
                await self.ws_pool.send_to_phone(device_id, self.serialize_message(SystemMessage.WAITING_PRINTER.value))

    async def handle_device_offline(self, message):
        device_id = message.get("device_id")
        device_type = message.get("device_type")
        if device_type == "printer":
            # 打印机下线
            await self.ws_pool.remove_printer(device_id)
            if self.ws_pool.phone_exist(device_id):
                # 手机在线，则通知手机
                await self.ws_pool.send_to_phone(device_id, self.serialize_message(SystemMessage.PRINTER_OFFLINE.value))
        elif device_type == "phone":
            # 手机下线
            await self.ws_pool.remove_phone(device_id)
            if self.ws_pool.printer_exist(device_id):
                # 打印机在线，则通知打印机
                await self.ws_pool.send_to_printer(device_id, self.serialize_message(SystemMessage.PHONE_OFFLINE.value))

    async def handle_print_task(self, message):
        # 手机发来的打印任务
        device_id = message.get("device_id")
        if self.ws_pool.printer_exist(device_id):
            await self.ws_pool.send_to_printer(device_id, self.serialize_message(message))
        else:
            # 打印机不在线
            await self.ws_pool.send_to_phone(device_id, self.serialize_message(SystemMessage.PRINTER_OFFLINE.value))

    async def handle_print_complete(self, message):
        # 打印机打印完成后 回执
        device_id = message.get("device_id")
        if self.ws_pool.phone_exist(device_id):
            await self.ws_pool.send_to_phone(device_id, self.serialize_message(message))

    def remove_devices(self, device_id):
        """ 移除打印机和手机 """
        if self.ws_pool.printer_exist(device_id):
            self.ws_pool.remove_printer(device_id)
        if self.ws_pool.phone_exist(device_id):
            self.ws_pool.remove_phone(device_id)


Message_Handler = WsMessageHandle(Ws_Pool)
