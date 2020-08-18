
def paginated_iterator(knex, initial_url):
    result = knex.get(initial_url)
    for blob in result['results']:
        yield blob
    next_page = result.get('next', None)
    if next_page:
        for blob in paginated_iterator(knex, next_page):
            yield blob
