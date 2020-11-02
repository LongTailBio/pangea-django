.. Pangea documentation master file, created by
   sphinx-quickstart on Sun Nov  1 12:12:45 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Pangea
======

Pangea is a Content Mangement System designed specifically for the Life Sciences. It is designed to help researchers manage projects, track data and metadata, and to find new interesting patterns in their data. Pangea integrates cloud storage services (like Amazon S3) with High Performance Compute Systems to allow researchers to manage and process their data across its full lifecycle.

Pangea Key Features:

- Organize Biological Data and Projects
- Low Cost Storage of Petabytes of Data
- Search, Visualize, and Compare Datasets

At its core Pangea employs a simple flexible data model which can support a wide variety of project types. Individual samples contain both raw data and analyses. Samples can be grouped together to form Sample Groups which may also contain data and analyses relevant to all the samples together. Organizations control samples and groups and Users may belong to organizations.

Documentation for the RESTful API may be found `here <https://app.swaggerhub.com/apis/dcdanko/Pangea/beta#/>`_.

Source Code may be found on GitHub `here <https://github.com/LongTailBio/pangea-django>`_.

A running example of Pangea may be found `here <https://pangea.gimmebio.com>`_.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Architecture and Design <architecture>
   Python API Client <python_client>
   License <license>



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
