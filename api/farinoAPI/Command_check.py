


if __name__ == "__main__":
    commands = []
    with open('fairino/Robot.py', 'r', encoding='utf-8') as f:
        for line in f.readlines():
            if 'self.robot.' in line:
                command = line.split('self.robot.')[1].split('(')[0]
                if command not in commands:
                    commands.append(command)

    with open('RobotCommands.txt', 'w') as f:
        for index, command in enumerate(commands): 
            print(f'{index}: {command}')
            f.write(f'{command}\n')