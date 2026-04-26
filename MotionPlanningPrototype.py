import numpy as np
import numpy

from api.farinoAPI.fairino.Robot import RPC
from Manager import SharedData

import multiprocessing
import dataclasses
import inspect
import time
import queue
from GUI import RobotCommunicator as RC

TIME = 0
LIGHT_SCAN = 1
RPCX = 2
RPCY = 3
RPCZ = 4

@dataclasses.dataclass(frozen=True)
class State:
    init = 0
    scan = 1
    move = 2
    complete = 3

@dataclasses.dataclass(frozen=True)
class Processes:
    main = 'MainProcess'

PROCESSES = Processes()
STATE = State()


def check_queue():
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

def request_data(request: SharedData, wait=True):
    start_time = time.time()
    q.put(request)
 
    requests:list[SharedData] = []
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
            print(f'{multiprocessing.current_process().name}: time to get data: {time.time()-start_time}')
            break
 
        waiting = wait
        counter += 1

def check_requests():
    requests = check_queue(q)
    for request in requests:
        if request.is_request:
            solve_request(q, request)
        else:
            open_requested_data(request)

def open_requested_data(request: SharedData):
    print(f'{multiprocessing.current_process().name} to {request.to_process} from {request.from_process} data_name {request.data_name} data: {request.data}')

def solve_request(request: SharedData):
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
   

def dmove(dx, dy, dz):
    request = SharedData(PROCESSES.main, multiprocessing.current_process().name, 1, True, 'dmove', dx, dy, dz, function=RC._incriment_move)
    request_data(request, False)

def move(x, y, z):
    request = SharedData(PROCESSES.main, multiprocessing.current_process().name, 1, True, 'move', x, y, z, function=RC._position_move)
    request_data(request, False)


def __init__(Q: multiprocessing.Queue, shared_arr:bytearray[float]):
    global inputarr
    global q
    inputarr = shared_arr
    q = Q


def get_light_scan():
    return inputarr[TIME], inputarr[LIGHT_SCAN]

def get_pos():
    #return numpy.array([inputarr[RPCX], inputarr[RPCY], inputarr[RPCZ]])
    return np.array([inputarr[RPCX], inputarr[RPCY], inputarr[RPCZ]])

def run(state):
    if state == STATE.init:
        print("Starting Gravity Test...")
        arm_position = [0,0,0] #STC

        print(f"Returning to Initial Pose: {arm_position}")
        state = STATE.scan

    elif state == STATE.scan:
        print("Scanning Light for Laser...")
        curr_pos = get_pos()
        curr_light = get_light_scan()
        print(f"Current Position: {curr_pos}, Current Light Intensity: {curr_light}")

        #test_iso = [5,5,5] #STC (mm)
        test_iso = numpy.array([numpy.random.randint(1, 50), numpy.random.randint(1, 50), numpy.random.randint(1, 50)])
        print(f"Moving to Found Isocenter: {test_iso}")

        #Move To Isocenter (mm) From Initial Pose
        #idx = test_iso[0] - curr_pos[0]
        #idy = test_iso[1] - curr_pos[1]
        #idz = test_iso[2] - curr_pos[2]
        iso_move = test_iso - curr_pos
        #iso_move = idx, idy, idz
        print(f"Vector (Isocenter - Initial): {iso_move}")
        move(*iso_move)
        curr_pos = test_iso
        print(f"Current Position (curr_pos): {curr_pos}")

        #Move in Square
        #Square Dimensions (mm) Use Even Dimensions for Now
        x = 5 #STC
        y = 10 #STC
        z = 0 #STC
        
        #Movement Deltas STC
        delta_x = 1
        delta_y = 1
        #delta_z = 1

        #1. Move in +x
        for i in range(x):
            next_move = (delta_x, 0, 0) #Define Next Movement
            print(f"Next Move Distances: {next_move}") 

            move(*next_move) #Call Move
            position = get_pos()
            print(f"Current Position (arm.position): {position}")

            dx = position[0] - curr_pos[0]  #Find Difference in Moved Distance
            print(f"dx: {dx}")

            vect = (dx, 0, 0) #Make Distance Vector
            print(f"Vector Movement: {vect}") #Show Distance Vector
            curr_pos = numpy.array([curr_pos[0]+dx, curr_pos[1], curr_pos[2]])

            curr_light = get_light_scan()
            print(f"Current Light Value: {curr_light}")

            if curr_light > final_light:
                final_light = curr_light
                light_pos = curr_pos.copy()
                print(f"New Light Value: {final_light}")
                print(f"New Light Position: {light_pos}")

        #2. Move in +y


        final_pos = iso_move
        state = STATE.complete
            
    elif state == STATE.complete:
        print("GRAVITY Test Complete")
        print(f"Final Position (At Isocenter): {final_pos}")
        #print(f"Best Light: {final_light}")
        return True


def grav_test_step(arm, movement, sensor, step, length):

    print("Starting Gravity-Laser Test...")

    data = []  # (position, intensity)

    start_pos = arm.position.copy()
    print(f"\n[Initialization] Start Position: {start_pos}")

    n_steps = int(length / step) #Number of steps to move per side
    print(f"\n[CONFIGURATION] Step = {step}, Length = {length} mm, Steps per Side = {n_steps}")

    #Movement Directions
    pos_x = np.array([step, 0, 0])
    neg_x = np.array([-step, 0, 0])

    pos_y = np.array([0, step, 0])
    neg_y = np.array([0, -step, 0])

    pos_z = np.array([0, 0, step])
    neg_z = np.array([0, 0, -step])

    #STC
    directions = [pos_x, pos_z, neg_x, neg_z]
    print(f"\n[DIRECTIONS] Possible Directions: {directions}")

    for side_index, direction in enumerate(directions):

        print(f"\nSIDE: {side_index + 1} --> ")
        print(f"Direction: {direction}")

        total_dist = 0.0 #Track how much distance moved in one side

        for step_index in range(n_steps):
            arm.move_vec(direction)

            total_dist += step

            curr_pos = np.copy(arm.position)
            intensity = sensor.read(curr_pos)

            data.append((curr_pos, intensity))

            print(f"Step: {step_index+1}")
            #print(f"Distance Moved: {total_dist}")
            #print(f"Current Position: {curr_pos}")
            #print(f"Current Intensity: {intensity}")
        
        print(f"\nDistance Traveled for Side {side_index+1}: {total_dist}")
        print(f"\nPosition After Side {side_index+1} Complete: {curr_pos}")

    #Return to intial pose
    home_vec = start_pos - arm.position
    print(f"\n[RETURN] Moving back by {home_vec}")
    arm.move_vec(start_pos - arm.position)

    print(f"[FINAL] Final Position: {arm.position}")
    print("\n=== TEST COMPLETE =====\n")

    return data






def MotionPlanningMain(Q: multiprocessing.Queue, shared_arr:bytearray):
    __init__(Q, shared_arr)
    done = False
    state = STATE.init
    while not done:
        done = run(state)



