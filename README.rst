dry-rest-permissions
======================================

|build-status-image| |pypi-version|

Overview
--------

Rules based permissions for the Django Rest Framework.

This framework is a perfect fit for apps that have many tables and relationships between them. It provides a framework that allows you to define, for each action or groups of actions, who has permission based on existing data in your database.

What does DRY Rest Permissions provide?
---------------------------------------

1. A framework for defining for defining global and object level permissions per action.
  a. Support for broadly defining permissions by grouping actions into safe and unsafe types.
  b. Support for defining only global (table level) permissions or only object (row level) permissions.
  c. Support for custom list and detail actions.
2. A serializer field that will return permissions for an object to your client app. This is DRY and works with your existing permission definitions.
3. A framework for limiting list requests based on permissions
  a. Support for custom list actions
  
Why is DRY Rest Permissions different than other DRF permission packages?
-------------------------------------------------------------------------

Most other DRF permissions are based on django-guardian. Django-gaurdian is an explicit approach to permissions that requires data to be saved in tables that explicitly grants permissions for certain actions. For apps that have many ways for a user to be given permission to certain actions, this approach can be very hard to maintain.

For example: you may have an app which lets you create and modify projects if you are an admin of an association that owns the project. This means that a user's permission will be granted or revoked based on many possabilities including ownership of the project transering to a different association, the user's admin status in the association changing and the user entering or leaving the association. This would need a lot of triggers that would key off of these actions and explicitly change permissions.

DRY Rest Permissions allows developers to easily describe what gives someone permission using the current data in an implicit way.

Requirements
------------

-  Python (2.7)
-  Django (1.7, 1.8)
-  Django REST Framework (3.0, 3.1)

Installation
------------

Install using ``pip``\ …

.. code:: bash

    $ pip install dry-rest-permissions

Example
-------

TODO: Write example.

Testing
-------

Install testing requirements.

.. code:: bash

    $ pip install -r requirements.txt

Run with runtests.

.. code:: bash

    $ ./runtests.py

You can also use the excellent `tox`_ testing tool to run the tests
against all supported versions of Python and Django. Install tox
globally, and then simply run:

.. code:: bash

    $ tox

Documentation
-------------

To build the documentation, you’ll need to install ``mkdocs``.

.. code:: bash

    $ pip install mkdocs

To preview the documentation:

.. code:: bash

    $ mkdocs serve
    Running at: http://127.0.0.1:8000/

To build the documentation:

.. code:: bash

    $ mkdocs build

.. _tox: http://tox.readthedocs.org/en/latest/

.. |build-status-image| image:: https://api.travis-ci.org/Helioscene/dry-rest-permissions.svg?branch=master
   :target: http://travis-ci.org/Helioscene/dry-rest-permissions?branch=master
.. |pypi-version| image:: https://img.shields.io/pypi/v/dry-rest-permissions.svg
   :target: https://pypi.python.org/pypi/dry-rest-permissions
