.. _tutorial:

********
Tutorial
********

.. contents::
    :local:
    :depth: 2


Use the WPS application comming with Twitcher
=============================================

Make sure twitcher is started with ``make status``:

.. code-block:: sh

    $ make status
    Supervisor status ...
    mongodb                          RUNNING   pid 6863, uptime 0:00:19
    nginx                            RUNNING   pid 6865, uptime 0:00:19
    twitcher                         RUNNING   pid 6864, uptime 0:00:19

Otherwise start the twitcher with ``make start``.

By default the twitcher WPS application is available at the URL https://localhost:38083/ows/wps.

Run a ``GetCapabilities`` request:

.. code-block:: sh

    $ curl -k "https://localhost:38083/ows/wps?service=wps&request=getcapabilities"


Run a ``DescribeProcess`` request:

.. code-block:: sh

    $ curl -k "https://localhost:38083/ows/wps?service=wps&request=describeprocess&identifier=dummyprocess&version=1.0.0"


Run an ``Exceute`` request:

.. code-block:: sh

    $ curl -k "https://localhost:38083/ows/wps?service=wps&request=execute&identifier=dummyprocess&version=1.0.0"

Now you should get an XML error response with a message that you need to provide an access token:


.. code-block:: xml

    <?xml version="1.0" encoding="utf-8"?>
    <ExceptionReport version="1.0.0" xmlns="http://www.opengis.net/ows/1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/ows/1.1 http://schemas.opengis.net/ows/1.1.0/owsExceptionReport.xsd">
        <Exception exceptionCode="NoApplicableCode" locator="AccessForbidden">
            <ExceptionText>Access token is required to access this service.</ExceptionText>
        </Exception>
    </ExceptionReport>

First we need to generate an access token with ``twitcherctl``:

.. code-block:: sh

    $ bin/twitcherctl -k gentoken
    abc123

There are three ways how you can provide the access token:

1. as ``access_token`` HTTP parameter

.. code-block:: sh

    $ curl -k "https://localhost:38083/ows/wps?service=wps&request=execute&identifier=dummyprocess&version=1.0.0&access_token=abc123"


2. as the last part of the HTTP path

.. code-block:: sh

    $ curl -k "https://localhost:38083/ows/wps/abc123?service=wps&request=execute&identifier=dummyprocess&version=1.0.0"

3. as ``Access-Token`` header variable

.. code-block:: sh

   $ curl -k -H Access-Token:abc123 "https://localhost:38083/ows/wps?service=wps&request=execute&identifier=dummyprocess&version=1.0.0"




