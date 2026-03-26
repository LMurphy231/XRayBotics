from api.farinoAPI.fairino import Robot

import time




if __name__ == '__main__':
    robot = Robot.RPC()
    for i in range(1000):
        start_time = time.time()
        print(f'testing {robot.GetActualJointPosRadian(flag=1)}')
        print(f'time to get data {time.time()-start_time}\n')
    robot.CloseRPC()