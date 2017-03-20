import os
import sys
import signal
import asyncio
import logging
from functools import partial
try:
    import ssl
except ImportError:
    ssl = None

import uvloop
import gunicorn.workers.base as base

from sanic import Sanic
from sanic.server import trigger_events, HttpProtocol, Signal, update_current_time
try:
    from sanic.websocket import WebSocketProtocol
except ImportError:
    WebSocketProtocol = None


__version__ = '0.1.2'
__all__ = ['Worker']


class Worker(base.Worker):

    def __init__(self, *args, **kw):  # pragma: no cover
        super().__init__(*args, **kw)
        cfg = self.cfg
        if cfg.is_ssl:
            self.ssl_context = self._create_ssl_context(cfg)
        else:
            self.ssl_context = None
        self.servers = []
        self.connections = set()
        self.exit_code = 0
        self.signal = Signal()

    def init_process(self):
        # create new event_loop after fork
        asyncio.get_event_loop().close()

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        super().init_process()

    @classmethod
    def check_config(cls, cfg, log):
        if type(Sanic.__call__) == type(object.__call__):  # NOQA
            Sanic.__call__ = lambda self: self

    def run(self):
        is_debug = self.log.loglevel == logging.DEBUG
        protocol = (WebSocketProtocol if WebSocketProtocol and self.app.callable.websocket_enabled
                    else HttpProtocol)
        self._server_settings = self.app.callable._helper(
            host=None,
            port=None,
            loop=self.loop,
            debug=is_debug,
            protocol=protocol,
            ssl=self.ssl_context,
            run_async=True
        )
        self._server_settings.pop('sock')
        trigger_events(self._server_settings.get('before_start', []),
                       self.loop)

        self._runner = asyncio.ensure_future(self._run(), loop=self.loop)
        try:
            self.loop.run_until_complete(self._runner)
            self.app.callable.is_running = True
            trigger_events(self._server_settings.get('after_start', []),
                           self.loop)
            self.loop.run_until_complete(self._check_alive())
            trigger_events(self._server_settings.get('before_stop', []),
                           self.loop)
            self.loop.run_until_complete(self.close())
        finally:
            trigger_events(self._server_settings.get('after_stop', []),
                           self.loop)
            self.loop.close()

        sys.exit(self.exit_code)

    async def close(self):
        if self.servers:
            # stop accepting connections
            self.log.info("Stopping server: %s, connections: %s",
                          self.pid, len(self.connections))
            for server in self.servers:
                server.close()
                await server.wait_closed()
            self.servers.clear()

            # prepare connections for closing
            self.signal.stopped = True
            for conn in self.connections:
                conn.close_if_idle()

            while self.connections:
                await asyncio.sleep(0.1)

    def serve(self, sock, request_handler, error_handler, debug=False,
              request_timeout=60, ssl=None, request_max_size=None,
              reuse_port=False, loop=None, protocol=HttpProtocol,
              backlog=100, **kwargs):
        """Start asynchronous HTTP Server on an individual process.

        :param request_handler: Sanic request handler with middleware
        :param error_handler: Sanic error handler with middleware
        :param debug: enables debug output (slows server)
        :param request_timeout: time in seconds
        :param ssl: SSLContext
        :param sock: Socket for the server to accept connections from
        :param request_max_size: size in bytes, `None` for no limit
        :param reuse_port: `True` for multiple workers
        :param loop: asyncio compatible event loop
        :param protocol: subclass of asyncio protocol class
        :return: Nothing
        """
        if debug:
            loop.set_debug(debug)

        server = partial(
            protocol,
            loop=loop,
            connections=self.connections,
            signal=self.signal,
            request_handler=request_handler,
            error_handler=error_handler,
            request_timeout=request_timeout,
            request_max_size=request_max_size,
        )

        server_coroutine = loop.create_server(
            server,
            host=None,
            port=None,
            ssl=ssl,
            reuse_port=reuse_port,
            sock=sock,
            backlog=backlog
        )
        # Instead of pulling time at the end of every request,
        # pull it once per minute
        loop.call_soon(partial(update_current_time, loop))
        return server_coroutine

    async def _run(self):
        for sock in self.sockets:
            self.servers.append(await self.serve(
                sock=sock,
                **self._server_settings
            ))

    async def _check_alive(self):
        # If our parent changed then we shut down.
        pid = os.getpid()
        try:
            while self.alive:
                self.notify()

                if pid == os.getpid() and self.ppid != os.getppid():
                    self.alive = False
                    self.log.info("Parent changed, shutting down: %s", self)
                else:
                    await asyncio.sleep(1.0, loop=self.loop)
        except (Exception, BaseException, GeneratorExit, KeyboardInterrupt):
            pass

    @staticmethod
    def _create_ssl_context(cfg):
        """ Creates SSLContext instance for usage in asyncio.create_server.
        See ssl.SSLSocket.__init__ for more details.
        """
        ctx = ssl.SSLContext(cfg.ssl_version)
        ctx.load_cert_chain(cfg.certfile, cfg.keyfile)
        ctx.verify_mode = cfg.cert_reqs
        if cfg.ca_certs:
            ctx.load_verify_locations(cfg.ca_certs)
        if cfg.ciphers:
            ctx.set_ciphers(cfg.ciphers)
        return ctx

    def init_signals(self):
        # Set up signals through the event loop API.

        self.loop.add_signal_handler(signal.SIGQUIT, self.handle_quit,
                                     signal.SIGQUIT, None)

        self.loop.add_signal_handler(signal.SIGTERM, self.handle_exit,
                                     signal.SIGTERM, None)

        self.loop.add_signal_handler(signal.SIGINT, self.handle_quit,
                                     signal.SIGINT, None)

        self.loop.add_signal_handler(signal.SIGWINCH, self.handle_winch,
                                     signal.SIGWINCH, None)

        self.loop.add_signal_handler(signal.SIGUSR1, self.handle_usr1,
                                     signal.SIGUSR1, None)

        self.loop.add_signal_handler(signal.SIGABRT, self.handle_abort,
                                     signal.SIGABRT, None)

        # Don't let SIGTERM and SIGUSR1 disturb active requests
        # by interrupting system calls
        signal.siginterrupt(signal.SIGTERM, False)
        signal.siginterrupt(signal.SIGUSR1, False)

    def handle_quit(self, sig, frame):
        self.alive = False
        self.cfg.worker_int(self)

    def handle_abort(self, sig, frame):
        self.alive = False
        self.exit_code = 1
        self.cfg.worker_abort(self)
