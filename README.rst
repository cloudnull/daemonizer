PEP-3143 System Daemonizer
##########################
:date: 2013-03-15 09:05
:tags: Daemon, Server, Utility, pep3143
:Authors: Kevin Carter


The Daemonizer allows any LOOP-able application to be used as a Daemon
======================================================================

In using `PEP-3143 Version 1.6`_ for Python. I have found PEP-3143 to be extremely useful, however the module is needing just a bit more to make the daemon function as you would anticipate. Being that the documentation on the PEP is lacking on how this is all accomplished it is left to the user, YOU to figure that out.  As such I have come up with this UTILITY code which sets up the daemon, the pid and a logging.


Here is how you use this
~~~~~~~~~~~~~~~~~~~~~~~~

* To use the Daemonizer you will need to install `PEP-3143 Version 1.6`_
* You will need to change the constant "APP_NAME" to the name of your application. While that is not technically needed, its just good practice.
* You will also need to change / modify or override the method "daemon_main". The "daemon_main" method is your main loop.
* Daemonizer will attempt to put your PID file in "var/run" if this directory does not exist it will put the pid file in your temp directory.
* Daemonizer will attempt to put logs in the directory "/var/log/YOUR_APP_NAME" if this directory does not exist it will put the pid file in your working directory.
* The Daemonizer requires root privileges to run. If your not root you are going to get a stack trace.


Here is an Example for the "daemon_main" :


.. code-block:: python

    self.system = True
    while self.system:
        # DO SOME THINGS
        self.log.info('I am a happy daemon')
        time.sleep(20)


Note that "self.system" is the equivalent of a Boolean value "``True``, ``False``".


.. _PEP-3143 Version 1.6: http://www.python.org/dev/peps/pep-3143/
