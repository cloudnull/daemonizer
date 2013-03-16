# ==============================================================================
# Copyright [2013] [Kevin Carter]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import os
import sys
import time
import traceback
import logging

# For Daemon
import daemon
from daemon import pidfile
import signal
import grp
import errno

# REPLACE THIS WITH YOUR APPLICATION NAME
APP_NAME = 'ExampleDaemonCode'


class NoLogLevelSet(Exception):
    pass


class DaemonDispatch(object):
    def __init__(self, p_args, output, handler):
        """
        The Daemon Processes the input from the application.
        """
        self.log = output
        self.p_args = p_args
        self.handler = handler
        self.log.info('Daemon Dispatch envoked')

    def pid_file(self):
        """
        Sets up the Pid files Location
        """
        # Determine the Pid location
        name = APP_NAME
        if os.path.isdir('/var/run/'):
            self.pid1 = '/var/run/%s.pid' % name
        else:
            import tempfile
            pid_loc = (tempfile.gettempdir(), os.sep, name)
            self.pid1 = '%s%s%s.pid' % pid_loc
        self.log.info('PID File is : %s' % (self.pid1))
        self.p_args['pid1'] = self.pid1
        return self.pid1

    def gracful_exit(self, signum=None, frame=None):
        """
        Exit the system
        """
        self.log.info('Exiting The Daemon Process for %s. '
                      'Signal recieved was %s on %s'
                      % (APP_NAME, signum, frame))
        self.system = False

    def context(self, pid_file):
        """
        pid_file='The full path to the PID'
        The pid name assumes that you are making an appropriate use of locks.

        Example :

        from daemon import pidfile
        pidfile.PIDLockFile(path='/tmp/pidfile.pid', threaded=True)

        Context Creation for the python-daemon module. Default values are for
        Python-daemon > 1.6 This is for Python-Daemon PEP 3143.
        """
        if self.p_args['debug_mode']:
            context = daemon.DaemonContext(
                stderr=sys.stderr,
                stdout=sys.stdout,
                working_directory=os.sep,
                umask=0,
                pidfile=pidfile.PIDLockFile(path=pid_file),
                )
        else:
            context = daemon.DaemonContext(
                working_directory=os.sep,
                umask=0,
                pidfile=pidfile.PIDLockFile(path=pid_file),
                )

        context.signal_map = {
            signal.SIGTERM: 'terminate',
            signal.SIGHUP: self.gracful_exit,
            signal.SIGUSR1: self.gracful_exit}

        _gid = grp.getgrnam('nogroup').gr_gid
        context.gid = _gid
        context.files_preserve = [self.handler.stream]
        return context

    def daemon_main(self):
        """
        This is your MAIN loop, you should change me...
        """
        self.system = True
        while self.system:
            # DO SOME THINGS
            self.log.info('I am a happy daemon')
            time.sleep(20)


class DaemonINIT(object):
    def __init__(self, p_args, output, handler):
        # Bless the daemon dispatch class
        self.d_m = DaemonDispatch(p_args=p_args,
                                  output=output,
                                  handler=handler)
        self.log = output
        self.p_args = p_args
        self.pid_file = self.d_m.pid_file()
        self.status = self.daemon_status()

    def is_pidfile_stale(self, pid):
        """
        Determine whether a PID file is stale.
        Return 'True' if the contents of the PID file are
        valid but do not match the PID of a currently-running process;
        otherwise return 'False'.
        """
        # Method has been inspired fromthe PEP-3143 v1.6 Daemon Library.
        if os.path.isfile(pid):
            with open(pid, 'r') as pid_file_loc:
                proc_id = pid_file_loc.read()
            if proc_id:
                try:
                    os.kill(int(proc_id), signal.SIG_DFL)
                except OSError, exc:
                    if exc.errno == errno.ESRCH:
                        # The specified PID does not exist
                        try:
                            os.remove(pid)
                            print('Found a stale PID file, and I killed it.')
                        except Exception:
                            msg = ('You have a stale PID and I cant break it. '
                                   'So I have quit.  Start Trouble Shooting.'
                                   'The PID file is %s' % pid)
                            self.log.critical(traceback.format_exc())
                            sys.exit(msg)
                except Exception, exp:
                    self.log.critical(traceback.format_exc())
                    sys.exit(exp)
            else:
                os.remove(pid)
                print('Found a stale PID file, but it was empty.'
                      ' so I removed it.')

    def daemon_status(self):
        self.pid = None
        stop_arg_list = (self.p_args['stop'],
                          self.p_args['status'])
        msg_list = []
        pid = self.pid_file
        self.is_pidfile_stale(pid)
        if os.path.isfile(pid):
            with open(pid, 'rb') as f_pid:
                p_id = int(f_pid.read())
            self.pid = True
            msg = ('PID "%s" exists - Process ( %d )' % (pid, p_id))
            msg_list.append(msg)

        elif any(stop_arg_list):
            msg = ('No PID File has been found for "%s".'
                  ' %s is not running.' % (pid, APP_NAME))
            msg_list.append(msg)

        pid_msg = tuple(msg_list)
        return pid_msg

    def daemon_run(self):
        if not self.pid:
            # Start the Daemon with the new Context
            self.log.info('Starting up the listener Daemon')
            with self.d_m.context(self.pid_file):
                try:
                    self.d_m.daemon_main()
                except Exception, exp:
                    self.log.critical(traceback.format_exc())
                    self.log.critical(exp)
        else:
            sys.exit('\n'.join(self.status))

    def daemon_stop(self):
        # Get PID Name and Location
        pid = self.pid_file
        if os.path.isfile(pid):
            with open(pid, 'r') as f_pid:
                p_id = f_pid.read()
            p_id = int(p_id)
            try:
                self.d_m.gracful_exit()
                print('Stopping the %s Application' % APP_NAME)
                os.kill(p_id, signal.SIGTERM)
                if os.path.isfile(pid):
                    os.remove(pid)
            except OSError, exp:
                self.log.critical(exp)
                self.log.critical(traceback.format_exc())
                sys.exit('Something bad happened, begin the '
                         'troubleshooting process.')
            except Exception:
                self.log.critical(traceback.format_exc())
        print('\n'.join(self.status))


def logger_setup(args):
    """
    Setup logging for your application
    """
    logger = logging.getLogger("%s Logging" % APP_NAME)

    # Log Level Arguments
    if args['log_level'].upper() == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    elif args['log_level'].upper() == 'INFO':
        logger.setLevel(logging.INFO)
    elif args['log_level'].upper() == 'WARN':
        logger.setLevel(logging.WARN)
    elif args['log_level'].upper() == 'ERROR':
        logger.setLevel(logging.ERROR)
    else:
        raise NoLogLevelSet('I died because you did not set the log level in'
                            ' your arguments. Here are your Arguments %s'
                            % args)

    # Set Formatting
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s"
                                  " - %(message)s")

    # Create the Log File
    # ==========================================================================
    # IF "/var/log/" does not exist, or you dont have write permissions to
    # "/var/log/" the log file will be in your working directory
    # Check for ROOT user if not log to working directory
    user = os.getuid()
    if not user == 0:
        logfile = '%s.log' % APP_NAME
    else:
        if os.path.isdir('/var/log/'):
            log_loc = '/var/log/%s' % APP_NAME
            if not os.path.isdir('/var/log/%s' % APP_NAME):
                try:
                    os.mkdir('%s' % log_loc)
                    logfile = '%s/%s.log' % (log_loc, APP_NAME)
                except Exception:
                    try:
                        logfile = '%s.log' % log_loc
                    except Exception:
                        logfile = '%s.log' % APP_NAME
            else:
                logfile = '%s/%s.log' % (log_loc, APP_NAME)
        else:
            logfile = '%s.log' % APP_NAME

    # Building Handeler
    handler = logging.FileHandler(logfile)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('Logger Online')
    return logger, handler


def daemon_args(p_args):
    """
    Loads the arguments required to leverage the Daemon

    Arguments to run the daemon need to look something like this :

    p_args = {'start': None,
              'stop': None,
              'status': None,
              'restart': None,
              'log_level': 'info',
              'debug': None}

    Notes for "p_args" :
    * "start, stop, status, restart" uses True, False, or None for its values.
    * "debug, info, warn, error" are the Valid log levels are.
    * "debug_mode" sets the daemon into debug mode which uses stdout / stderror.
    * "debug_mode" SHOULD NOT BE USED FOR NORMAL OPERATION! and can cause
      "error 5" over time
    """
    log_s = logger_setup(args=p_args)
    logger = log_s[0]
    handler = log_s[1]

    # Bless the Daemon Setup / INIT class
    d_i = DaemonINIT(p_args=p_args,
                     output=logger,
                     handler=handler)

    if p_args['start']:
        d_i.daemon_run()

    elif p_args['stop']:
        d_i.daemon_stop()

    elif p_args['status']:
        pid = d_i.daemon_status()
        logger.info(pid[0])
        print(pid[0])

    elif p_args['restart']:
        logger.info('%s is Restarting' % APP_NAME)
        print('%s is Restarting' % APP_NAME)

        # Check the status
        d_i.daemon_status()

        # Stop Daemon
        d_i.daemon_stop()
        time.sleep(2)

        # ReBless the class to start the app post stop
        d_r = DaemonINIT(p_args=p_args,
                         output=logger,
                         handler=handler)
        d_r.daemon_run()


def args():
    """
    ONLY FOR EXAMPLE
    """
    import argparse
    parser = argparse.ArgumentParser(usage='%(prog)s',
                                     description=('Daemonizer app Example'))
    # Setup Sub-Parser
    subparser = parser.add_subparsers(title='Monitoring By Ameba',
                                      metavar='<Commands>\n')
    # Positional Groups being used
    d_control = subparser.add_parser('daemon',
                                  help=('Available Actions when interfacing'
                                        ' with the Daemon mode, Otherwise'
                                        ' known as Server Mode.'))
    d_control.add_argument('--start',
                           default=None,
                           action='store_true')
    d_control.add_argument('--stop',
                           default=None,
                           action='store_true')
    d_control.add_argument('--restart',
                           default=None,
                           action='store_true')
    d_control.add_argument('--status',
                           default=None,
                           action='store_true')

    parser.add_argument('--log-level',
                        metavar='[LogingType]',
                        required=True,
                        choices=['debug', 'info', 'warn', 'error'],
                        help='Sets the Log Level')
    parser.add_argument('--debug-mode',
                        action='store_true',
                        help='Enables Debug Mode')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit('Give me something to do and I will do it')

    p_args = parser.parse_args()
    p_args = vars(p_args)

    # Run the Daemon
    daemon_args(p_args=p_args)


if __name__ == '__main__':
    args()
