import atexit
import os
import multiprocessing
import threading
import time
from contextlib import contextmanager

import numpy as np
import labquest as lq


_RECORD = 'record'
_STOP   = 'stop'
_CLOSE  = 'close'
_SINGLE = 'single'

_record_lock = threading.Lock()


class SensorManager:
    def __init__(self, freq=5000):
        self.command_queue = multiprocessing.Queue()
        self.return_queue  = multiprocessing.Queue()
        self.ready_flag    = multiprocessing.Event()
        self.process = multiprocessing.Process(target=_lq_process, args=(self.command_queue, self.return_queue, self.ready_flag, freq), daemon=True)
        self.process.start()

    @property
    def _ready(self):
        while not self.ready_flag.is_set():
            time.sleep(1e-6)
        
    
    @contextmanager
    def record(self):
        self._ready
        light_data = []
        time_data  = []
        with _record_lock:
            self.command_queue.put(_RECORD)
            yield light_data, time_data
            self.command_queue.put(_STOP)
        td, ld = self.get()
        time_data[:]  = td[:]
        light_data[:] = ld[:]
        
 
    def get(self) -> tuple[list, list]: 
        time_data, light_data = self.return_queue.get()
        return time_data, light_data

    def read(self, navg=1):
        self._ready
        with _record_lock:
            self.command_queue.put((_SINGLE, navg))

        time_data, light_data = self.return_queue.get()
        if light_data:
            with np.errstate(all='ignore'):
                return time_data, float(np.average(light_data))
        else:
            return time_data, light_data


    def close(self):
        self.command_queue.put(_CLOSE)
        self.process.join()
    
@contextmanager
def open_labquest():
    try:
        ls = lq.LabQuest()
        ls.open()
        ls.select_sensors(ch1="lq_sensor")
        ls.start(period = 0.01)
        yield ls
    finally:
        ls.stop()
        ls.close()

def _lq_process(command_queue:multiprocessing.Queue, return_queue:multiprocessing.Queue, ready_flag:threading.Event, freq=5000):
    with open_labquest() as ls:
        command = None
        light_data = []
        time_data  = []
        ready_flag.set()
        while multiprocessing.parent_process().is_alive():
            navg = 1
            if command is None or not command_queue.empty():
                given = command_queue.get()
                if isinstance(given, (list, tuple)):
                    if len(given) == 2:
                        command, navg = given
                else:
                    command = given

            if command == _RECORD:
                data = ls.read_multi_pt('ch1', navg)
                light_data.append(float(np.average(data)) if data else None)
                time_data.append(time.time())

            elif command == _STOP:
                return_queue.put((time_data, light_data))
                light_data = []
                time_data  = []
                command = None

            elif command == _SINGLE:
                return_queue.put((time.time(), ls.read_multi_pt('ch1', navg) or []))
                command = None

            elif command == _CLOSE:
                break

if __name__ == '__main__':
    sm = SensorManager()
    try:
        
        for i in range(5):
            start_time = time.time()
            print(sm.read(1), time.time()-start_time)

        with sm.record() as (gravity_time, gravity_light):
            time.sleep(0.01)
            
            # logic...

        gravity_time, gravity_light = sm.record()
        
        with sm.record() as (square_time, square_light):
            time.sleep(0.01)
            
            # logic...


    finally:
        sm.close()