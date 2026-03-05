import os
import multiprocessing

class QueueData:
    def __init__(self, to_process: str, from_process: str, is_request: bool, data_name: str, run_function, data):
        self.to_process = to_process
        self.from_process = from_process
        self.is_request = is_request
        self.data_name = data_name
        self.data = data
    
    def return_data(self, *data):
        self.is_request


if __name__ == '__main__':
    pass