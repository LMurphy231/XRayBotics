import api.farinoAPI.fairino.Robot as Robot
import multiprocessing 
import threading
import os
import ctypes
import time
import queue
import random
import inspect

import numpy
import adafruit_vl53l4cd

stop = False

class SharedData:
    def __init__(self, to_process, from_process, priority, is_request, data_name, *data, function=None):
        self.to_process   = to_process
        self.from_process = from_process
        self.priority     = priority
        self.is_request   = is_request
        self.data_name    = data_name
        self.data         = data
        self.function     = function

    def return_data(self, *data):
        self.to_process, self.from_process = self.from_process, self.to_process
        self.data = data
        self.is_request = False
        return self 

    def __str__(self):
        return f'{self.to_process}, {self.from_process}, {self.priority}, {self.is_request}, {self.data_name}, {self.data}, {self.function}'


def ptask(q: multiprocessing.Queue, arr_):

    global arr
    arr = arr_
    while not stop:
        to_process = f'{random.randint(0,4)} process'
        while to_process == multiprocessing.current_process().name:
            to_process = f'{random.randint(0,4)} process'
        request = SharedData(to_process, multiprocessing.current_process().name, random.randint(0,55), True, random.randint(0,4), function=random.choice([None, f, SharedData.demo_class_function]))
        request_data(q, request)

 

def request_data(q: multiprocessing.Queue, request: SharedData, wait=True):
    start_time = time.time()
    q.put(request)
 
    requests = []
    waiting=True
    counter=0
    while waiting:
        requests = check_queue(q)

        request_found = False
        requests.sort(key=lambda x: x.priority)
        for qrequest in requests:
            if qrequest.is_request:
                solve_request(q, qrequest)
            else:
                open_requested_data(qrequest)

                request_found = True
 

        if request_found:
            x,y,z = get_pos()
            print(f'{multiprocessing.current_process().name}: time to get data: {time.time()-start_time}')
            break
 
        waiting = wait
        counter += 1

       

def check_requests(q: multiprocessing.Queue):
    requests = check_queue(q)
    for request in requests:
        if request.is_request:
            solve_request(q, request)
        else:
            open_requested_data(request)

   

def open_requested_data(request: SharedData):
    print(f'{multiprocessing.current_process().name} to {request.to_process} from {request.from_process} data_name {request.data_name} data: {request.data}')

def solve_request(q: multiprocessing.Queue, request: SharedData):
    if request.function is None:
        if request.data_name == 0:
            q.put(request.return_data('zero',multiprocessing.current_process().name))
        elif request.data_name == 1:
            q.put(request.return_data('one',multiprocessing.current_process().name))
        elif request.data_name == 2:
            q.put(request.return_data('two',multiprocessing.current_process().name))
        elif request.data_name == 3:
            q.put(request.return_data('three',multiprocessing.current_process().name))
        else:
            q.put(request.return_data(None))
    elif request.function in inspect.getmembers(SharedData, predicate=inspect.isfunction):
        q.put(request.return_data(request.function(request, request.data_name),multiprocessing.current_process().name))

    else:
        q.put(request.return_data(request.function(request.data_name),multiprocessing.current_process().name))
 

def get_pos():
    x, y, z = tuple(arr[:])
    return x,y,z

def check_queue(q: multiprocessing.Queue):
    requests = []
    ret_requests = []
    while True:
        try:
            request = q.get(block=False)
            if multiprocessing.current_process().name == request.to_process:
                requests.append(request)
            else:
                ret_requests.append(request)
        except queue.Empty:
            for request in ret_requests:
                q.put(request)
            return requests

def init(shared_arr_):
    global shared_arr
    shared_arr = shared_arr_ # must be inherited, not passed as an argument

def sensor(q: multiprocessing.Queue, position):
    pass

def pathfinding(q: multiprocessing.Queue, position):
    pass

def start_subsystems(q: multiprocessing.Queue, position):
    processes: list[multiprocessing.Process] = []
    for process_name in [('Sensors', sensor), ('Pathfinding', pathfinding)]:
        p = multiprocessing.Process(target=ptask, args=(q,arr), name = process_name)
        processes.append(p)

    for p in processes:
        p.start()


def update_thread(event: threading.Event, position, robot:Robot.RPC):
    print(event.is_set())
    while not event.is_set():
        position[:] = robot.GetActualJointPosRadian()[1]
        print(f'Threading: {position[:]}, {event.is_set()}')
        
if __name__ == '__main__':
    counter = [0]
    threads = []
    processes = []
    ARRAY_SIZE = 6
    robot = Robot.RPC()
    q = multiprocessing.Queue()
    arr = multiprocessing.Array(ctypes.c_float, ARRAY_SIZE)
    lock = multiprocessing.Lock()
    
    #start_subsystems(q, arr)
    start_time = time.time()
    event = threading.Event()
    t = threading.Thread(target=update_thread, args=(event, arr, robot))
    t.start()
    while time.time() - start_time <= 5:
        print(f'Main Thread: {robot.GetActualJointAccDegree()}')
    event.set()
