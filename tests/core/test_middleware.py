import pytest
import asyncio
from socialconnector.core.middleware import MiddlewareChain

@pytest.mark.asyncio
async def test_middleware_onion_model():
    chain = MiddlewareChain()
    order = []
    
    async def middleware1(ctx, next_handler):
        order.append("m1_pre")
        res = await next_handler(ctx)
        order.append("m1_post")
        return res
        
    async def middleware2(ctx, next_handler):
        order.append("m2_pre")
        res = await next_handler(ctx)
        order.append("m2_post")
        return res
        
    async def final_handler(ctx):
        order.append("final")
        return "result"
        
    chain.add(middleware1)
    chain.add(middleware2)
    
    res = await chain.execute({}, final_handler)
    
    assert res == "result"
    assert order == ["m1_pre", "m2_pre", "final", "m2_post", "m1_post"]

@pytest.mark.asyncio
async def test_middleware_context_modification():
    chain = MiddlewareChain()
    
    async def middleware(ctx, next_handler):
        ctx["modified"] = True
        return await next_handler(ctx)
        
    async def final_handler(ctx):
        return ctx.get("modified")
        
    chain.add(middleware)
    res = await chain.execute({}, final_handler)
    assert res is True
