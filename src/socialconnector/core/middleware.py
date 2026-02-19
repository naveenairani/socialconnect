from typing import Any, Callable, Coroutine


class MiddlewareChain:
    """Manages the execution of a chain of middleware."""

    def __init__(self) -> None:
        self._middlewares: list[Callable[[dict[str, Any], Callable[[dict[str, Any]], Coroutine[Any, Any, Any]]], Coroutine[Any, Any, Any]]] = []

    def add(self, middleware: Callable[[dict[str, Any], Callable[[dict[str, Any]], Coroutine[Any, Any, Any]]], Coroutine[Any, Any, Any]]) -> None:
        """Add a middleware to the chain."""
        self._middlewares.append(middleware)

    async def execute(self, context: dict[str, Any], final_handler: Callable[[dict[str, Any]], Coroutine[Any, Any, Any]]) -> Any:
        """Execute the middleware chain followed by the final handler."""

        async def _dispatch(index: int, ctx: dict[str, Any]) -> Any:
            if index < len(self._middlewares):
                middleware = self._middlewares[index]

                async def _next(next_ctx: dict[str, Any]) -> Any:
                    return await _dispatch(index + 1, next_ctx)

                return await middleware(ctx, _next)
            return await final_handler(ctx)

        return await _dispatch(0, context)


# Example basic middleware implementations

async def logging_middleware(context: dict[str, Any], next_handler: Callable[[dict[str, Any]], Coroutine[Any, Any, Any]]) -> Any:
    """Logs the message processing context."""
    # Pre-processing
    print(f"Processing: {context.get('action')}")
    result = await next_handler(context)
    # Post-processing
    print(f"Finished: {context.get('action')}")
    return result
