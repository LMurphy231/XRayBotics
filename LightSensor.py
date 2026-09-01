import os
import multiprocessing
import threading
import time
from contextlib import contextmanager

import numpy as np
import labquest as lq


_START = 'start'
_STOP  = 'stop'
_CLOSE = 'close'

_record_lock = threading.Lock()

class SensorManager:
    def __init__(self, freq):
        self.command_queue = multiprocessing.Queue()
        self.return_queue  = multiprocessing.Queue()
        self.process = multiprocessing.Process(target=start, args=(self.command_queue, self.return_queue, freq), daemon=True)
        self.process.start()

    @contextmanager
    def record(self):
        with _record_lock:
            self.command_queue.put(_START)
            yield 
            self.command_queue.put(_STOP)

    def get(self) -> tuple[list, list]: 
        time_data, light_data = self.return_queue.get()
        return time_data, light_data

    def close(self):
        self.command_queue.put(_CLOSE)
        self.process.join()
    
def _read(ls:lq.LabQuest, event:threading.Event, time_data:list, light_data:list):
    while not event.is_set():
        data = ls.read('ch1')
        if data is not None:
            light_data.append(data)
            time_data.append(time.time())

def _end_read(thread:threading.Thread, event:threading.Event, q:multiprocessing.Queue, time_data:list, light_data:list):
    if thread.is_alive():
        event.set()
        thread.join()
        event.clear()
        q.put((np.array(time_data), np.array(light_data)))
        time_data  = []
        light_data = []
    return time_data, light_data

def start(command_queue:multiprocessing.Queue, return_queue:multiprocessing.Queue, freq=5000):
    try:
        ls = lq.LabQuest()
        ls.open()
        ls.select_sensors(ch1="lq_sensor")
        ls.start(period=int(1/freq*1000))

        event = threading.Event()
        light_data = []
        time_data  = []
        thread = threading.Thread(target=lambda:None)
    
        while multiprocessing.parent_process().is_alive():
            given = command_queue.get()
            if isinstance(given, (list, tuple)):
                if len(given) == 2:
                    command, args = given
            else:
                command = given

            print(f'Running {command}')
            if command == _START:
                time_data, light_data = _end_read(thread, event, return_queue, time_data, light_data)
                thread = threading.Thread(target=_read, args=(ls, event, time_data, light_data))
                thread.start()

            elif command == _STOP:
                time_data, light_data = _end_read(thread, event, return_queue, time_data, light_data)

            elif command == _CLOSE:
                time_data, light_data = _end_read(thread, event, return_queue, time_data, light_data)
                break
            
    finally:
        print('closing connection')
        ls.stop()
        ls.close()

