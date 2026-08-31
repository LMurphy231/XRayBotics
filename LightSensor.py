import os
import multiprocessing
import threading
import time

import numpy as np
import labquest as lq


class LightSensor:
    def __init__(self, freq=5000):
        self.queue = multiprocessing.Queue()
 
        self.ls = lq.LabQuest()
        self.ls.open()
        self.ls.select_sensors(ch1="lq_sensor")
        self.ls.start(period=int(1/freq*1000))

    def connect(self):
        self.status = self.lq.open()
        self.lq.select_sensors(ch1="lq_sensor")
        return self.status

    def close(self):
        try:
            self.lq.stop()
            self.lq.close()
        except:
            pass

    def start(self, freq=5000):
        self.freq = freq
        self.lq.start(period = int(1/self.freq*1000))
    
    def get_single(self):
        
        if self.status == -1:
            self.connect()
            self.lq.start(period=int(1/self.freq*1000))

        return self.lq.read('ch1')
    
    def get(self, Navg=1):
        '''
        Get sample of size N over avgn readings per sample returned
        '''
        try:
            if self.status == -1:
                self.connect()
                self.lq.start(period=int(1/self.freq*1000))
        except:
            return 0
        
        data = self.lq.read_multi_pt('ch1', Navg)
        data = data if data else np.full(Navg, 0)
        return np.average(data)

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



def start(command_queue:multiprocessing.Queue, return_queue:multiprocessing.Queue, freq=5000):
    ls = lq.LabQuest()
    ls.open()
    ls.select_sensors(ch1="lq_sensor")
    ls.start(period=int(1/freq*1000))
    print('here')
    event = threading.Event()
    light_data = []
    time_data  = []
    thread = threading.Thread(target=lambda:None)
    try:
        while multiprocessing.parent_process().is_alive():
            given = command_queue.get()
            if isinstance(given, (list, tuple)):
                if len(given) == 2:
                    command, args = given
            else:
                command = given

            print(f'Running {command}')
            if command == 'start':
                _end_read(thread, event, return_queue, time_data, light_data)
                thread = threading.Thread(target=_read, args=(ls, event, time_data, light_data))
                thread.start()

            elif command == 'stop':
                _end_read(thread, event, return_queue, time_data, light_data)

            elif command == 'close':
                print('Closing')
                break
            
    finally:
        print('closing connection')
        ls.stop()
        ls.close()


if __name__ == '__main__':
    command_queue = multiprocessing.Queue()
    return_queue = multiprocessing.Queue()
    freq = 5000
    process = multiprocessing.Process(target=start, args=(command_queue, return_queue, freq), daemon=True)
    process.start()
    for i in range(5):
        command_queue.put(('start', None))
        time.sleep(4)
        command_queue.put(('stop', None))   
        time_data, light_data = return_queue.get()
        print(f'Got\ntime: {time_data}\nlight: {light_data}')
    print('Closing process')
    command_queue.put(('close'))
    process.join()
