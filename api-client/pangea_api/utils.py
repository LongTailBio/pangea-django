
from .file_system_cache import FileSystemCache


def paginated_iterator(knex, initial_url):
    cache = FileSystemCache()
    result = cache.get_cached_blob(initial_url)
    if not result:
        result = knex.get(initial_url)
        cache.cache_blob(initial_url, result)
    for blob in result['results']:
        yield blob
    next_page = result.get('next', None)
    if next_page:
        for blob in paginated_iterator(knex, next_page):
            yield blob
