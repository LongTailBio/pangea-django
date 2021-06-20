


def paginated_iterator(knex, initial_url):
    response = knex(initial_url)
    response.raise_for_status()
    result = response.json()
    for blob in result['results']:
        yield blob
    next_page = result.get('next', None)
    if next_page:
        for blob in paginated_iterator(knex, next_page):
            yield blob


def get_project(text):
    text = text.lower()
    for x in ['gcsd2016', 'gcsd2017', 'gcsd2018', 'gcsd2019', 'gcsd2020', 'gcsd2021']:
        if x in text:
            return x
    return 'unknown'
