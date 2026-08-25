import threading
import ctypes
import time
import multiprocessing
import queue
import random
import inspect
import os

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

    def demo_class_function(self, *data):
        print(f'showing off demo {data}')
        return self

    def __str__(self):
        return f'{self.to_process}, {self.from_process}, {self.priority}, {self.is_request}, {self.data_name}, {self.data}, {self.function}'

def task(name, counter):
    while not stop:
        print(f'{name}: {counter[-1]}')
        time.sleep(0.01)
    print(f'{name}: {counter}')

def f(data):
    return data*2
 

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

 

if __name__ == '__main__':
    counter = [0]
    threads = []
    processes = []
    ARRAY_SIZE = 3

    q = multiprocessing.Queue()

    arr = multiprocessing.Array(ctypes.c_float, ARRAY_SIZE)

    for i in range(5):
        #t = threading.Thread(target=task, args=(f'{i}',counter))
        #threads.append(t)
        p = multiprocessing.Process(target=ptask, args=(q,arr), name = f'{i} process')
        processes.append(p)
       

    for t in threads:
        t.start()

    for p in processes:
        p.start()

    for i in range(100):
        arr[:] = [random.random(),random.random(),random.random()]
        time.sleep(0.01)
    print(counter)
    stop = True

    for t in threads:
        t.join()
 

    for child in multiprocessing.active_children():
        child.terminate()
        child.join()
    print('Done')

   
    print(os.__file__)