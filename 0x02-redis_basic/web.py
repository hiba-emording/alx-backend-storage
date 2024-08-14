#!/usr/bin/env python3
"""
A module providing tools for request caching and tracking 
using Redis as the backend.
"""
import redis
import requests
from functools import wraps
from typing import Callable


redis_store = redis.Redis()


def data_cacher(method: Callable[[str], str]) -> Callable[[str], str]:
    """
    Decorator that caches the output of fetched data and tracks access counts.

    This decorator caches the result of a URL request and increments a counter
    to track how many times the URL has been accessed. The cached result is 
    stored with an expiration time of 10 seconds.

    Args:
        method (Callable[[str], str]): The function to be decorated.

    Returns:
        Callable[[str], str]: The wrapped function with caching and tracking.
    """
    @wraps(method)
    def invoker(url: str) -> str:
        """
        Wrapper function for caching output and tracking access counts.

        Args:
            url (str): The URL to fetch and cache.

        Returns:
            str: The content of the URL, either from the cache or fetched fresh.
        """
        redis_store.incr(f'count:{url}')
        
        result = redis_store.get(f'result:{url}')
        if result:
            return result.decode('utf-8')
        
        result = method(url)
        redis_store.setex(f'result:{url}', 10, result)
        return result
    
    return invoker


@data_cacher
def get_page(url: str) -> str:
    """
    Fetches the content of a URL, caches the response, and tracks access.

    Args:
        url (str): The URL to fetch.

    Returns:
        str: The content of the URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"Error fetching the URL: {e}"
