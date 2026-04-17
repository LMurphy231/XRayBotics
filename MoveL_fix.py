def move_tool_x_10cm(ip="192.168.58.2"):
    from api.farinoAPI.fairino.Robot import RPC

    robot = RPC(ip)
    try:
        RPC.is_conect = True
        pose = robot.GetActualTCPPose(0)
        return robot.MoveL(
            desc_pos=pose[1],
            tool=0,
            user=0,
            vel=10.0,
            acc=20.0,
            ovl=100.0,
            blendR=-1.0,
            blendMode=0,
            exaxis_pos=[0.0, 0.0, 0.0, 0.0],
            search=0,
            offset_flag=2,
            offset_pos=[0.0, 0.0, 100.0, 0.0, 0.0, 0.0],
            oacc=20.0,
            velAccParamMode=0,
        )
    finally:
        robot.CloseRPC()


print(move_tool_x_10cm())
