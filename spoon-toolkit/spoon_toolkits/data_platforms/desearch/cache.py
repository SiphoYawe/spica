import functools
import time
import asyncio
import inspect


def time_cache(max_age_seconds=300, maxsize=128, typed=False):
    """Least-recently-used cache decorator with time-based cache invalidation.

    Args:
        max_age_seconds: Time to live for cached results (in seconds).
        maxsize: Maximum cache size (see `functools.lru_cache`).
        typed: Cache on distinct input types (see `functools.lru_cache`).
    """
    def _decorator(fn):
        # Check if the function is async
        is_async = inspect.iscoroutinefunction(fn)

        if is_async:
            # For async functions, we need to handle caching differently
            # since lru_cache doesn't work with coroutines directly
            cache = {}

            @functools.wraps(fn)
            async def _async_wrapped(*args, **kwargs):
                # Create cache key with proper handling of unhashable types
                time_salt = int(time.time() / max_age_seconds)

                # Convert args to hashable types
                hashable_args = []
                for arg in args:
                    if isinstance(arg, list):
                        hashable_args.append(tuple(arg))
                    elif isinstance(arg, dict):
                        hashable_args.append(tuple(sorted(arg.items())))
                    else:
                        hashable_args.append(arg)

                # Convert kwargs to hashable types
                hashable_kwargs = []
                for k, v in kwargs.items():
                    if isinstance(v, list):
                        hashable_kwargs.append((k, tuple(v)))
                    elif isinstance(v, dict):
                        hashable_kwargs.append((k, tuple(sorted(v.items()))))
                    else:
                        hashable_kwargs.append((k, v))

                cache_key = (tuple(hashable_args), tuple(sorted(hashable_kwargs)), time_salt)

                # Check cache
                if cache_key in cache:
                    return cache[cache_key]

                # Call function and cache result
                result = await fn(*args, **kwargs)

                # Simple cache size management
                if len(cache) >= maxsize:
                    # Remove oldest entries (simple FIFO, not LRU for simplicity)
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]

                cache[cache_key] = result
                return result

            return _async_wrapped
        else:
            # For sync functions, use the original implementation
            @functools.lru_cache(maxsize=maxsize, typed=typed)
            def _new(*args, __time_salt, **kwargs):
                return fn(*args, **kwargs)

            @functools.wraps(fn)
            def _wrapped(*args, **kwargs):
                return _new(*args, **kwargs, __time_salt=int(time.time() / max_age_seconds))

            return _wrapped

    return _decorator