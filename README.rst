structlog: Your ticket to easy structured Python logging.
=========================================================

The purpose of structlog is to make structured logging much easier in Python:

.. code-block:: pycon

   >>> import logging, sys
   >>> from structlog import BoundLog
   >>> logging.basicConfig(stream=sys.stdout, format='%(message)s')
   >>> logger = logging.getLogger('example_logger')
   >>> log = BoundLog.fromLogger(logger).bind(user='anonymous', some_key=23)

Do something else like authentication.
Then:

.. code-block:: pycon

   >>> log = log.bind(user='hynek', another_key=42)
   >>> log.warning('example.event')
   {
       "another_key": 42, 
       "event": "example.event", 
       "some_key": 23, 
       "user": "hynek"
   }

It also offers easy composible log processors:

.. code-block:: pycon

   >>> import datetime
   >>> from structlog import JSONRenderer
   >>> from structlog.stdlib import filter_by_level
   >>> def add_timestamp(_, __, event_dict):
   ...     event_dict['timestamp'] = datetime.datetime(1980, 3, 25, 17, 0, 0)
   ...     return event_dict
   >>> def censor_password(_, __, event_dict):
   ...     pw = event_dict.get('password')
   ...     if pw:
   ...         event_dict['password'] = '***'
   ...     return event_dict
   >>> log = BoundLog.fromLogger(
   ...     logger,
   ...     processors=[
   ...         filter_by_level,
   ...         add_timestamp,
   ...         censor_password,
   ...         JSONRenderer(indent=1)
   ...     ]
   ... )
   >>> log.info('something.filtered')
   >>> log.warning('something.not_filtered', password='secret')
   {
    "timestamp": "datetime.datetime(1980, 3, 25, 17, 0)", 
    "password": "***", 
    "event": "something.not_filtered"
   }


- returning False = don't log
- returning None = error b/c probably accidental


Requirements
------------

Works with Python 2.6, 2.7, 3.2, and 3.3 as well as with PyPy with no additional dependencies.


Caveats
-------

stdlib
++++++

- Doesn’t wrap ``Logger.log`` and ``Logger.exception``.
  The latter one shouldn’t be a problem since you can always add a processor
  that handles the current exception.
