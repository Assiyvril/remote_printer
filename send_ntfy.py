import json
import requests


class NtfySender(object):

    HOST = "https://ntfy.sh/"
    TOPIC = "zjyutest009jkl"

    @classmethod
    def build_post_data(cls, title, message, tags=None):
        if tags is None:
            tags = ["x", "bug"]
        data = json.dumps({
            "topic": cls.TOPIC,
            "title": '坪洲WsRP: ' + title,
            "message": message,
            "tags": tags,
        })
        return data

    def send_notification(self, title, message, tags=None):
        data = self.build_post_data(title, message, tags)
        requests.post(self.HOST, data=data)
