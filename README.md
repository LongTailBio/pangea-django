# Pangea

Pangea is a service to store and analyze bioinformatics data. It helps researchhers to share data and keep track of projects and analyses.

This repository contains the code to run a Pangea Web Server as well as a Python-based API to interact with that server.

You can see a running instance of Pangea [here](https://pangeabio.io/)

## Command Line Interface and Python API

To interact with an existing Pangea instance you can use the [Python API and attached CLI](https://github.com/LongTailBio/pangea-django/tree/master/api-client)


## Running a Pangea Server Locally

```sh
pyenv virtualenv 3.8.9 pangea-django
pyenv activate pangea-django
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Documentation may be found [here](https://longtailbio.github.io/pangea-django/).

Built with [Django](https://github.com/django/django).
