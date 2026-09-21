import configparser
import dataclasses
import typing


@dataclasses.dataclass
class ProgramOption:
    _root          : configparser.ConfigParser
    section        : str
    name           : str
    default        : typing.Any
    program_default: typing.Any
    display_name   : str = None
    units          : str = None
    description    : str = None

    def set(self, default=None, display_name=None, units=None, description=None):
        if default     : self.default      = str(default)
        if display_name: self.display_name = str(display_name)
        if units       : self.units        = str(units)
        if description : self.description  = str(description)

        self._root[f'{self.section}.user_default'][self.name] = self.default
        self._root[self.section][self.name]                   = self.display_name
        self._root[f'{self.section}.units'][self.name]        = self.units
        self._root[f'{self.section}.description'][self.name]  = self.description

    @property
    def units_str(self):
        return f'[{self.units}]' if self.units else ''

    @property
    def display_unit_name(self):
        return f'{self.display_name} {self.units_str}'.strip() 
    
def add_default(opts:configparser.ConfigParser, section, name, default, display_name=None, units=None, description=None):
    section_list = section.split('.')
    current_section = []
    for sect in section_list:
        if current_section:
            
            current_section_name = '.'.join(current_section)+'.'
            opts.setdefault(current_section_name, {})
            opts[current_section_name].setdefault(sect, '')
        current_section.append(sect)

    opts.setdefault(section, {})
    opts[section].setdefault(name, display_name if display_name else name)

    # Used for program defined defaults
    program_default_section = '.'.join(current_section+['program_default'])
    opts.setdefault(program_default_section, {})
    opts[program_default_section][name] = str(default)

    # Used for user defined defaults
    user_default_section = '.'.join(current_section+['default'])
    opts.setdefault(user_default_section, {})
    opts[user_default_section].setdefault(name, str(default))

    # Add item units if one was given
    if units:
        units_section = '.'.join(current_section+['units'])
        opts.setdefault(units_section, {})
        opts[units_section].setdefault(name, units)

    # Add item description if one was given
    if description:
        desc_section = '.'.join(current_section+['description'])
        opts.setdefault(desc_section, {})
        opts[desc_section].setdefault(name, description)

def get_option(opts:configparser.ConfigParser, section, name):
    assert section in opts.sections(), f'Section "{section}" not found'
    assert name in opts.options(section), f'Item "{name}" not found in "{section}"'
    return ProgramOption(
        _root           = opts,
        section         = section,
        name            = name,
        default         = _convert_type(opts.get(f'{section}.default'        , name, fallback=None)),
        program_default = _convert_type(opts.get(f'{section}.program_default', name, fallback=None)),
        display_name    = opts.get(f'{section}'                , name, fallback=None),
        units           = opts.get(f'{section}.units'          , name, fallback=None),
        description     = opts.get(f'{section}.description'    , name, fallback=None),
    )

def get_display_name(opts:configparser.ConfigParser, section, name):
    return get_option(opts, section, name).display_name

def get_description(opts:configparser.ConfigParser, section, name):
    return get_option(opts, section, name).description

def get_default(opts:configparser.ConfigParser, section, name):
    return get_option(opts, section, name).default

def get_program_default(opts:configparser.ConfigParser, section, name):
    return get_option(opts, section, name).program_default

def _convert_type(value:str):
    try:
        return int(value, base=0)
    except ValueError:
        return float(value)
    except ValueError:
        return value
    
def sections(opts:configparser.ConfigParser, section=None):
    if section is None:
        for section in opts.sections():
            if section.count('.') == 1 and section.endswith('.'):
                yield section[:-1]
    else:
        for section in opts.options(f'{section}.'):
            yield section

def get_opt_dict(opts:configparser.ConfigParser):
    
    def get_section(opt_dict, prev_sections, current_section):
        next_section = prev_sections + [current_section,]
        for section in sections(opts, '.'.join(next_section)):
            opt_dict.setdefault(section, {})
            if '.'.join(next_section+[section,])+'.' not in opts.sections():
                for variable in opts.options('.'.join(next_section+[section,])):
                    opt_dict[section][variable] = get_option(opts, '.'.join(next_section+[section,]), variable)
            else:
                get_section(opt_dict[section], next_section, section)
                        
                            
    opt_dict:dict[str, ProgramOption] = {}
    for section in sections(opts):
        prev_sections = []
        opt_dict.setdefault(section, {})
        get_section(opt_dict[section], prev_sections, section)

    return opt_dict

if __name__ == '__main__':
    opts = configparser.ConfigParser()
    section = 'robot.move.gravity'
    add_default(opts, section, 'tool', 0   , display_name='Tool'    , description='Tool number')
    add_default(opts, section, 'user', 0   , display_name='User'    , description='Artifact number')
    add_default(opts, section, 'vel' , 10.0, display_name='Velocity', units='%%', description='Percentage of speed')

    #for section in opts.sections():
    #    print(f'\n[{section}]')
    #    for option in opts.options(section):
    #        print(f'{option} = {opts.get(section, option)}')

    #option = get_option(opts, section, 'tool')
    opt = get_opt_dict(opts)
    print(opt)