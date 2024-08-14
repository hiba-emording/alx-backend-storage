#!/usr/bin/env python3
"""
A module for interacting with Redis, a NoSQL key-value store,
providing functionality to store, retrieve, and track the usage of data.
"""
import uuid
import redis
from functools import wraps
from typing import Any, Callable, Union


def count_calls(method: Callable) -> Callable:
    """
    Decorator that counts the number of times a method of
    the Cache class is called.

    Args:
        method (Callable): The method to be decorated.

    Returns:
        Callable: The wrapped method with call counting functionality.
    """
    @wraps(method)
    def invoker(self, *args, **kwargs) -> Any:
        """
        Wraps the method to increment its call counter and then execute it.

        Args:
            self: The instance of the Cache class.
            *args: Positional arguments passed to the method.
            **kwargs: Keyword arguments passed to the method.

        Returns:
            Any: The result of the decorated method.
        """
        if isinstance(self._redis, redis.Redis):
            self._redis.incr(method.__qualname__)
        return method(self, *args, **kwargs)
    return invoker


def call_history(method: Callable) -> Callable:
    """
    Decorator that records the history of inputs and
    outputs for a method of the Cache class.

    Args:
        method (Callable): The method to be decorated.

    Returns:
        Callable: The wrapped method with call history tracking functionality.
    """
    @wraps(method)
    def invoker(self, *args, **kwargs) -> Any:
        """
        Wraps the method to log its inputs and outputs in Redis.

        Args:
            self: The instance of the Cache class.
            *args: Positional arguments passed to the method.
            **kwargs: Keyword arguments passed to the method.

        Returns:
            Any: The result of the decorated method.
        """
        in_key = '{}:inputs'.format(method.__qualname__)
        out_key = '{}:outputs'.format(method.__qualname__)
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(in_key, str(args))
        output = method(self, *args, **kwargs)
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(out_key, output)
        return output
    return invoker


def replay(fn: Callable) -> None:
    """
    Displays the recorded call history of a Cache class method.

    Args:
        fn (Callable): The method whose call history should be displayed.
    """
    if fn is None or not hasattr(fn, '__self__'):
        return
    redis_store = getattr(fn.__self__, '_redis', None)
    if not isinstance(redis_store, redis.Redis):
        return
    fxn_name = fn.__qualname__
    in_key = '{}:inputs'.format(fxn_name)
    out_key = '{}:outputs'.format(fxn_name)
    fxn_call_count = 0
    if redis_store.exists(fxn_name) != 0:
        fxn_call_count = int(redis_store.get(fxn_name))
    print('{} was called {} times:'.format(fxn_name, fxn_call_count))
    fxn_inputs = redis_store.lrange(in_key, 0, -1)
    fxn_outputs = redis_store.lrange(out_key, 0, -1)
    for fxn_input, fxn_output in zip(fxn_inputs, fxn_outputs):
        print('{}(*{}) -> {}'.format(
            fxn_name,
            fxn_input.decode("utf-8"),
            fxn_output,
        ))


class Cache:
    """
    A class for interacting with a Redis data store,
    providing methods to store and retrieve data,
    as well as track method calls and their histories.
    """
    def __init__(self) -> None:
        """
        Initializes the Cache instance with a Redis connection.
        """
        self._redis = redis.Redis()
        self._redis.flushdb(True)

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Stores a value in the Redis data store and returns a unique key.

        Args:
            data (Union[str, bytes, int, float]):
            The data to be stored in Redis.

        Returns:
            str: The unique key associated with the stored data.
        """
        data_key = str(uuid.uuid4())
        self._redis.set(data_key, data)
        return data_key

    def get(
            self,
            key: str,
            fn: Callable = None,
            ) -> Union[str, bytes, int, float]:
        """
        Retrieves a value from Redis by its key and applies
        an optional transformation.

        Args:
            key (str): The key associated with the value to retrieve.
            fn (Callable, optional): A function to apply to
            the retrieved value
            If not provided, the raw value is returned.

        Returns:
            Union[str, bytes, int, float]: The retrieved value,
            optionally transformed by the provided function.
        """
        data = self._redis.get(key)
        return fn(data) if fn is not None else data

    def get_str(self, key: str) -> str:
        """
        Retrieves a string value from Redis by its key.

        Args:
            key (str): The key associated with the value to retrieve.

        Returns:
            str: The retrieved string value.
        """
        return self.get(key, lambda x: x.decode('utf-8'))

    def get_int(self, key: str) -> int:
        """
        Retrieves an integer value from Redis by its key.

        Args:
            key (str): The key associated with the value to retrieve.

        Returns:
            int: The retrieved integer value.
        """
        return self.get(key, lambda x: int(x))
