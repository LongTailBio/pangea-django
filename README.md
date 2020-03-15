# Pangea

Built with [Django](https://github.com/django/django).

## Getting Started

```sh
pyenv virtualenv 3.8.9 pangea-django
pyenv activate pangea-django
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Developing

### Changes to Dependencies

Changes to Python dependencies should be committed using the following:

```sh
pip freeze > requirements.txt
```

### Creating a `contrib` Module

Use the Django CLI to create the module:

```sh
mkdir ./pangea/contrib/mymodule
python manage.py startapp mymodule ./pangea/contrib/mymodule
```
