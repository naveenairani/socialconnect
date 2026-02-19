from collections.abc import Callable, Coroutine
from typing import Any

# Type alias for middleware callables to keep signatures readable
_Ctx = dict[str, Any]
_Handler = Callable[[_Ctx], Coroutine[Any, Any, Any]]
_Middleware = Callable[[_Ctx, _Handler], Coroutine[Any, Any, Any]]


class MiddlewareChain:
    """Manages the execution of a chain of middleware."""

    def __init__(self) -> None:
        self._middlewares: list[_Middleware] = []

    def add(self, middleware: _Middleware) -> None:
        """Add a middleware to the chain."""
        self._middlewares.append(middleware)

    async def execute(self, context: _Ctx, final_handler: _Handler) -> Any:
        """Execute the middleware chain followed by the final handler."""

        async def _dispatch(index: int, ctx: _Ctx) -> Any:
            if index < len(self._middlewares):
                middleware = self._middlewares[index]

                async def _next(next_ctx: _Ctx) -> Any:
                    return await _dispatch(index + 1, next_ctx)

                return await middleware(ctx, _next)
            return await final_handler(ctx)

        return await _dispatch(0, context)


# Example basic middleware implementations


async def logging_middleware(context: _Ctx, next_handler: _Handler) -> Any:
    """Logs the message processing context."""
    # Pre-processing
    print(f"Processing: {context.get('action')}")
    result = await next_handler(context)
    # Post-processing
    print(f"Finished: {context.get('action')}")
    return result
