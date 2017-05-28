import threading
import subprocess
import json
import sys
import traceback
import io

from gi.repository import GLib

class MapController:
    def __init__(self, click_callback=None):
        self.process = None
        self.click_callback = click_callback

        self.ensure_process()


    def send_command(self, **kwargs):
        proc = self.ensure_process()
        json.dump(kwargs, self.process_stdin)
        print(file=self.process_stdin, flush=True)

    def send_command_if_open(self, **kwargs):
        with self.start_lock:
            if self.process:
                self.send_command(**kwargs)

    def ensure_process(self):
        if not self.process:
            self.process = subprocess.Popen(
                [sys.executable, '-m', 'map'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            self.process_stdin = io.TextIOWrapper(self.process.stdin)
            self.process_stdout = io.TextIOWrapper(self.process.stdout)

            self.start_lock = threading.Lock()
            self.start_lock.acquire()

            thread = threading.Thread(target=self.input_thread)
            thread.daemon = True
            thread.start()

            self.start_lock.acquire()
            self.start_lock.release()

        return self.process

    def input_thread(self):
        self.ensure_process()
        self.start_lock.release()
        try:
            while True:
                try:
                    line = self.process_stdout.readline()
                    if not line:
                        return
                except (BrokenPipeError, EOFError):
                    return
                try:
                    data = json.loads(line)
                    cmd = data['cmd']
                    if cmd == 'point_selected':
                        if self.click_callback:
                            GLib.idle_add(self.click_callback, data['row'])
                    else:
                        print('controller: ignoring line:', data)
                except Exception:
                    traceback.print_exc()
        finally:
            self.process = None
