import pytest
import asyncio
from socialconnector.core.events import EventBus
from socialconnector.core.models import Event, EventType

@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    bus = EventBus()
    received = []
    
    async def handler(event: Event):
        received.append(event)
        
    bus.subscribe(EventType.MESSAGE_RECEIVED, handler)
    
    event = Event(type=EventType.MESSAGE_RECEIVED, platform="test")
    await bus.emit(EventType.MESSAGE_RECEIVED, event)
    
    assert len(received) == 1
    assert received[0].type == EventType.MESSAGE_RECEIVED

@pytest.mark.asyncio
async def test_event_bus_wildcard():
    bus = EventBus()
    received = []
    
    async def handler(event: Event):
        received.append(event)
        
    bus.subscribe("*", handler)
    
    event1 = Event(type=EventType.MESSAGE_RECEIVED, platform="test")
    event2 = Event(type=EventType.USER_JOINED, platform="test")
    
    await bus.emit(EventType.MESSAGE_RECEIVED, event1)
    await bus.emit(EventType.USER_JOINED, event2)
    
    assert len(received) == 2

@pytest.mark.asyncio
async def test_event_bus_unsubscribe():
    bus = EventBus()
    received = []
    
    async def handler(event: Event):
        received.append(event)
        
    bus.subscribe(EventType.MESSAGE_RECEIVED, handler)
    bus.unsubscribe(EventType.MESSAGE_RECEIVED, handler)
    
    event = Event(type=EventType.MESSAGE_RECEIVED, platform="test")
    await bus.emit(EventType.MESSAGE_RECEIVED, event)
    
    assert len(received) == 0
