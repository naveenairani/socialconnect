from datetime import datetime

import pytest

from socialconnector.core.models import Media, MediaType, Message, UserInfo


def test_message_model_validation():
    user = UserInfo(id="user1", platform="telegram", username="tester")
    msg = Message(id="msg123", platform="telegram", chat_id="chat456", sender=user, text="Hello world")

    assert msg.id == "msg123"
    assert msg.sender.username == "tester"
    assert isinstance(msg.timestamp, datetime)
    assert msg.media == []


def test_media_model():
    media = Media(type=MediaType.IMAGE, url="http://example.com/img.png")
    assert media.type == MediaType.IMAGE
    assert media.url == "http://example.com/img.png"


def test_message_frozen():
    user = UserInfo(id="u1", platform="p1")
    msg = Message(id="m1", platform="p1", chat_id="c1", sender=user)
    with pytest.raises(Exception):
        msg.id = "new_id"
