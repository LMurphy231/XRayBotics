try:
    from api.farinoAPI.fairino.Robot import *
except:
    from Robot import RPC
    
from labquest import LabQuest 
try:
    import GUI
    #from GUI import RobotCommunicator, LightSensor, TestData
except:
    pass

def initializeRobot():
    #Objects for Classes
    if fr5 is None:
        fr5 = GUI.RobotCommunicator()

    if testData is None:
        sensor = GUI.LightSensor() 
        testData = GUI.TestData(fr5, sensor)

def returnToHomePosition(fr5):
    #Home Position
    homePosition = fr5.HOME
    print(f"\n[Initialization] Start Position: {homePosition}")
    fr5.home()