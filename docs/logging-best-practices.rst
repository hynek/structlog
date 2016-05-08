Logging Best Practices
======================

The best practice for you depends very much on your context.
To give you some pointers nevertheless, here are a few scenarios that may be applicable to you.

Pull requests for further interesting approaches as well as refinements and more complete examples are very welcome.


Common Ideas
------------

Logging is not a new concept and in no way special to Python.
Logfiles have existed for decades and there's little reason to reinvent the wheel in our little world.

There are several concepts that are very well-solved in general and especially in heterogeneous environments, using special tooling for Python applications does more harm than good and makes the operations staff build dart board with your pictures.

Therefore let's rely on proven tools as much as possible and do only the absolutely necessary inside of Python\ [*]_.
A very nice approach is to simply log to `standard out`_ and let other tools take care of the rest.

runit
^^^^^

One runner that makes this very easy is the venerable runit_ project which made it a part of its design: server processes don't detach but log to standard out instead.
There it gets processed by other software -- potentially by one of its own tools: svlogd_.
We use it extensively and it has proven itself extremely robust and capable; check out `this tutorial`_ if you'd like to try it.

If you're not quite convinced and want an overview on running daemons, have a look at cue's `daemon showdown`_ that discusses the most common ones.


Local Logging
-------------

There are basically two common ways to log to local logfiles: writing yourself into files and syslog.

Syslog
^^^^^^

The simplest approach to logging is to forward your entries to the syslogd_.
Twisted, uwsgi, and runit support it directly.
It will happily add a timestamp and write wherever you tell it in its configuration.
You can also log from multiple processes into a single file and use your system's logrotate_ for log rotation.

The only downside is that syslog has some quirks that show itself under high load like rate limits (`they can be switched off`_) and lost log entries.


runit's svlogd
^^^^^^^^^^^^^^

If you'll choose runit for running your daemons, svlogd_ is a nicer approach.
It receives the log entries via a UNIX pipe and acts on them which includes adding of parse-friendly timestamps in tai64n_ as well as filtering and log rotation.


Centralized Logging
-------------------

Nowadays you usually don't want your logfiles in compressed archives distributed over dozens -- if not thousands -- servers.
You want them at a single location; parsed and easy to query.


Syslog (Again!)
^^^^^^^^^^^^^^^

The widely deployed syslog implementation rsyslog_ supports remote logging out-of-the-box.
Have a look at `this post`_ by Revolution Systems on the how.

Since syslog is such a widespread solution, there are also ways to use it with basically any centralized product.


Logstash with logstash-forwarder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Logstash_ is a great way to parse, save, and search your logs.

The general modus operandi is that you have log shippers that parse your log files and forward the log entries to your Logstash server and store is in elasticsearch_.
If your log entries consist of a JSON dictionary (and perhaps a tai64n_ timestamp), this is pretty easy and efficient.

If you can't decide on a log shipper, logstash-forwarder_ (formerly known as Lumberjack) works really well.
When Logstash's ``lumberjack`` input is configured to use ``codec => "json"``, having ``structlog`` output JSON is all you need.
See the documentation on the :doc:`standard-library` for an example configuration.


Graylog2
^^^^^^^^

Graylog_ goes one step further.
It not only supports everything those above do (and then some); you can also log directly JSON entries towards it -- optionally even through an AMQP server (like RabbitMQ_) for better reliability.
Additionally, `Graylog's Extended Log Format`_ (GELF) allows for structured data which makes it an obvious choice to use together with ``structlog``.


.. [*] This is obviously a privileged UNIX-centric view but even Windows has tools and means for log management although we won't be able to discuss them here.

.. _Graylog: http://graylog2.org
.. _Logstash: https://www.elastic.co/products/logstash
.. _logstash-forwarder: https://github.com/elastic/logstash-forwarder
.. _RabbitMQ: http://www.rabbitmq.com
.. _`Graylog's Extended Log Format`: http://docs.graylog.org/en/latest/pages/gelf.html
.. _`daemon showdown`: https://web.archive.org/web/20130907200323/http://tech.cueup.com/blog/2013/03/08/running-daemons/
.. _`standard out`: https://en.wikipedia.org/wiki/Standard_out#Standard_output_.28stdout.29
.. _`they can be switched off`: http://blog.abhijeetr.com/2013/01/disable-rate-limiting-in-rsyslog-v5.html
.. _`this post`: http://www.revsys.com/blog/2010/aug/26/centralized-logging-fun-and-profit/
.. _`this tutorial`: https://rubyists.github.io/2011/05/02/runit-for-ruby-and-everything-else.html
.. _logrotate: http://manpages.ubuntu.com/manpages/xenial/en/man8/logrotate.8.html
.. _rsyslog: http://www.rsyslog.com
.. _runit: http://smarden.org/runit/
.. _svlogd: http://smarden.org/runit/svlogd.8.html
.. _syslogd: https://en.wikipedia.org/wiki/Syslogd
.. _tai64n: http://cr.yp.to/daemontools/tai64n.html
.. _elasticsearch: https://www.elastic.co/products/elasticsearch
