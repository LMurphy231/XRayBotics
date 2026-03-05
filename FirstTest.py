from api.farinoAPI.fairino import Robot





if __name__ == '__main__':
    robot = Robot.RPC()
    print(f'testing{robot.GetSoftwareVersion()}')
    
    robot.CloseRPC()