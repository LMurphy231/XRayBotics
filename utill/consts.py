


# region Communicator
_PASSKEY   = 'I2)&[*G3gpDPS7nai"0H-q9Ro{>M;{i'
_DDNS_SITE = 'xraybotics.ddns.net'
_PORT      = 9000
_HOST      = '0.0.0.0'
_LOCAL_RELAY_IP = '192.168.1.162'
_ENCODING       = 'utf-8'
_DELIMITER      = '/ENDMESSAGE/'
_DIVIDER        = '~'
_ILLEGAL_CHAR   = (_DIVIDER, )
_MAX_PING_MS    = 9999

# Commands
_PING           = 'Ping'
_GET_SERVER     = 'Get Servers'

# Handle message Codes

_REFUSE_CONNECTION = -1
_ACCEPT_CONNECTION = 0
_SEND_SERVER_LIST  = 1
_TRANSMIT_DATA     = 2
_REJOIN_SERVER     = 3
_IGNORE_MESSAGE    = 99


# return messages
_MSG_JOIN_SUCCESS              =  'Successfully joined "{}"'
_MSG_CREATE_SUCCESS            =  'Successfully created "{}"'
_MSG_PASSKEY_ACCEPTED          =  'Passkey Accepted'
_MSG_NO_ACTIVE_SERVERS         =  'No active servers'

# Error messages
_MSG_ILLEGAL_PASSWORD          = f'Password contains illegal character(s) {_ILLEGAL_CHAR}'
_MSG_INCORRECT_PASSWORD        =  'Incorrect Password!'
_MSG_INCORRECT_PASSKEY         =  'Incorrect Passkey!'
_MSG_HOSTNAME_EXISTS_ERROR     =  'Hostname "{}" already exists...'
_MSG_HOSTNAME_NOT_EXISTS_ERROR =  'Hostname "{}" does not exist...'
_MSG_ALREADY_JOINED_ERROR      =  'Already connected to a server...'
_MSG_CONNECTION_REFUSED        =  'Connection refused...'
_MSG_CONNECTION_ERROR          =  'Cannot connect to relay host...'
_MSG_LOST_CONNECTION           =  'Connection lost to relay host...'



class Error:
    def __init__(self, exception: Exception, message: str):
        self.exception = exception
        self.message   = message
    
    def __call__(self, *args, **kwargs):
        args = args if args else ('' for _ in range(max(1, len(self.message.split('{}'))-1)))
        return self.exception(self.message.format(*args))
    
ERROR = {
    _MSG_ILLEGAL_PASSWORD:          Error(ValueError            , _MSG_ILLEGAL_PASSWORD         ),
    _MSG_INCORRECT_PASSKEY:         Error(PermissionError       , _MSG_INCORRECT_PASSKEY        ),
    _MSG_INCORRECT_PASSWORD:        Error(PermissionError       , _MSG_INCORRECT_PASSWORD       ),
    _MSG_HOSTNAME_EXISTS_ERROR:     Error(ValueError            , _MSG_HOSTNAME_EXISTS_ERROR    ),
    _MSG_HOSTNAME_NOT_EXISTS_ERROR: Error(ValueError            , _MSG_HOSTNAME_NOT_EXISTS_ERROR),
    _MSG_ALREADY_JOINED_ERROR:      Error(ConnectionAbortedError, _MSG_ALREADY_JOINED_ERROR     ),
    _MSG_CONNECTION_REFUSED:        Error(ConnectionRefusedError, _MSG_ALREADY_JOINED_ERROR     ),
    _MSG_LOST_CONNECTION:           Error(ConnectionError       , _MSG_LOST_CONNECTION          ),
    _MSG_CONNECTION_ERROR:          Error(ConnectionError       , _MSG_CONNECTION_ERROR         ),
}


def _password_is_allowed(password: str):
    for char in password:
        if char in _ILLEGAL_CHAR:
            return False
    return True

# region plotters
_SCATTER_MARKERS = [('Point', '.'       ),('Pixel', ','        ),('Circle', 'o'       ),
                   ('Triangle Up', '^'  ),('Triangle Down', 'v'),('Triangle Left', '<'),('Triangle Right', '>'),
                   ('Tri Up', '1'       ),('Tri Down', '2'     ),('Tri Left', '3'     ),('Tri Right', '4'),
                   ('Octogon', '8'      ),('Square', 's'       ),('Pentagon', 'p'     ),('Star', '*'),
                   ('Plus (filled)', 'P'),('Plus', '+'         ),('Hexagon 1', 'h'    ),('Hexagon 2', 'H'),
                   ('X', 'x'            ),('X (filled)', 'X'   ),('Diamond', 'D'      ),('Thin Diamond', 'd'),
                   ('vline', '|'        ),('hline', '_'        ),
                   ('Tick Left', 0      ),('Tick Right', 1     ),('Tick Up', 2        ),('Tick Down', 3),
                   ('Care Left', 4      ),('Care Right', 5     ),('Care Up', 6        ),('Care Down', 7),
                   ('Care Left Base', 8 ),('Care Right Base', 9),('Care Up Base', 10  ),('Care Down Base', 11),]