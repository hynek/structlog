======================
Logging Best Practices
======================

Logging is not a new concept and in no way special to Python.
Logfiles have existed for decades and there's little reason to reinvent the wheel in our little world.

Therefore let's rely on proven tools as much as possible and do only the absolutely necessary inside of Python\ [*]_.

A simple but powerful approach is to log to unbuffered `standard out`_ and let other tools take care of the rest.
That can be your terminal window while developing, it can be systemd_ redirecting your log entries to syslogd_, or your `cluster manager`_.
It doesn't matter where or how your application is running, it just works.

This is why the popular `twelve-factor app methodology`_ suggests just that.

.. [*] This is obviously a privileged UNIX-centric view but even Windows has tools and means for log management although we won't be able to discuss them here.


Canonical Log Lines
===================

Generally speaking, having as few log entries per request as possible is a good thing.
The less noise, the more insights.

``structlog``'s ability to :ref:`bind data to loggers incrementally <building-ctx>` -- plus :doc:`thread-local context storage <thread-local>` -- can help you to minimize the output to a *single log entry*.

At Stripe, this concept is called `Canonical Log Lines <https://brandur.org/canonical-log-lines>`_.



Centralized Logging
===================

Nowadays you usually don't want your logfiles in compressed archives distributed over dozens -- if not thousands -- of servers or cluster nodes.
You want them in a single location.
Parsed, indexed, and easy to search.


ELK
---

The ELK stack (Elasticsearch_, Logstash_, Kibana_) from Elastic is a great way to store, parse, and search your logs.

The way it works is that you have local log shippers like Filebeat_ that parse your log files and forward the log entries to your Logstash_ server.
Logstash parses the log entries and stores them in Elasticsearch_.
Finally, you can view and search them in Kibana_.

If your log entries consist of a JSON dictionary, this is fairly easy and efficient.
All you have to do is to tell Logstash_ either that your log entries are prepended with a timestamp from `TimeStamper` or the name of your timestamp field.


Graylog
-------

Graylog_ goes one step further.
It not only supports everything those above do (and then some); you can also directly log JSON entries towards it -- optionally even through an AMQP server (like RabbitMQ_) for better reliability.
Additionally, `Graylog's Extended Log Format`_ (GELF) allows for structured data which makes it an obvious choice to use together with ``structlog``.


.. _Graylog: https://www.graylog.org/
.. _Elastic: https://www.elastic.co/
.. _Logstash: https://www.elastic.co/products/logstash
.. _Kibana: https://www.elastic.co/products/kibana
.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _`Graylog's Extended Log Format`: https://docs.graylog.org/en/latest/pages/gelf.html
.. _`standard out`: https://en.wikipedia.org/wiki/Standard_out#Standard_output_.28stdout.29
.. _syslogd: https://en.wikipedia.org/wiki/Syslogd
.. _`twelve-factor app methodology`: https://12factor.net/logs
.. _systemd: https://en.wikipedia.org/wiki/Systemd
.. _`cluster manager`: https://kubernetes.io/docs/concepts/cluster-administration/logging/
.. _Filebeat: https://github.com/elastic/beats/tree/master/filebeat
.. _RabbitMQ: https://www.rabbitmq.com/
