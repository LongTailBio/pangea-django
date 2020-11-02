Python API Client
=================

Pangea includes a python API client to interact with the RESTful API.

Overview
^^^^^^^^

The API client provides an object oriented interface to the RESTful API. Objects (Sample-Groups, Samples, Results, etc..) can be created, fetched, updated and destroyed by manipulating python objects and calling special ``get``, ``save``, and ``delete`` methods. The API client can be used to upload and download data from S3 without additional authentication.

API Documentation
^^^^^^^^^^^^^^^^^

Remote Connection and Caching
-----------------------------

.. autoclass:: pangea_api.remote_object.RemoteObject
    :members:
    :undoc-members:


.. autoclass:: pangea_api.Knex
    :members:
    :undoc-members:


.. autoclass:: pangea_api.file_system_cache.FileSystemCache
    :members:
    :undoc-members:


Objects
-------

.. autoclass:: pangea_api.Organization
    :members:
    :undoc-members:


.. autoclass:: pangea_api.User
    :members:
    :undoc-members:


.. autoclass:: pangea_api.SampleGroup
    :members:
    :undoc-members:


.. autoclass:: pangea_api.Sample
    :members:
    :undoc-members:


.. autoclass:: pangea_api.analysis_result.AnalysisResult
    :members:
    :undoc-members:


.. autoclass:: pangea_api.analysis_result.SampleAnalysisResult
    :members:
    :undoc-members:


.. autoclass:: pangea_api.analysis_result.SampleGroupAnalysisResult
    :members:
    :undoc-members:


.. autoclass:: pangea_api.analysis_result.AnalysisResultField
    :members:
    :undoc-members:


.. autoclass:: pangea_api.analysis_result.SampleAnalysisResultField
    :members:
    :undoc-members:


.. autoclass:: pangea_api.analysis_result.SampleGroupAnalysisResultField
    :members:
    :undoc-members: