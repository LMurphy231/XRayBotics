import os
import time

import numpy as np

import LightSensor as ls

data_folder  = 'TestData'
laser_folder = os.path.join(data_folder, 'Laser Test Data')
col_folder   = os.path.join(data_folder, 'Collimator Test Data')


def new_file_name(dir_, base_name, ext):
    file_name = os.path.join(dir_, base_name+ext)
    i = 1
    while os.path.exists(file_name):
        file_name = os.path.join(dir_, f'{base_name}({i}){ext}')
        i += 1

    return file_name

if __name__ == '__main__':
    lq = ls.SensorManager()

    time_data = []
    light_data = []
    input('Press enter to start recording:')
    if not os.path.isdir(data_folder):
        os.mkdir(data_folder)
    start_time = time.time()
    for i in range(1000):
        t, light_intensity = lq.read()
        time_data.append(start_time-t)
        light_data.append(light_intensity)
        print((start_time-t, light_intensity))
    lq.close()
    print('done...')

    

    if not os.path.exists(laser_folder):
        os.mkdir(laser_folder)

    file_name = new_file_name(laser_folder, 'laser_data', '.dat')
    with open(file_name, 'w') as f:
        for t, light_intensity in zip(time_data, light_data): 
            f.write(f'{t},{light_intensity}\n')