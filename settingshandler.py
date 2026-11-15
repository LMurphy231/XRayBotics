import collections
import configparser
import dataclasses
import os
import typing
import tkinter as tk
from tkinter import ttk

@dataclasses.dataclass
class Option:
    _root          : configparser.ConfigParser
    section        : str
    name           : str
    default        : typing.Any
    var            : tk.Variable
    values         : list[str] = None
    min_value      : float = None
    max_value      : float = None
    display_name   : str = None
    units          : str = None
    description    : str = None
    ini            : str = None

    @property
    def value(self):
        return self.var.get()

    def set_default(self):
        self._root.setdefault(self.section, {})
        self._root[self.section][self.name] = str(self.value)
        if self.ini:
            with open(self.ini, 'w') as f:
                self._root.write(f)

    def load_user_default(self):
        value = self._root.get(self.section, self.name, fallback=self.default)
        self.set(value)

    def set(self, value):
        self.var.set(value)

    def reset(self):
        self.var.set(self.default)

    @property
    def units_str(self):
        return f'[{self.units}]' if self.units else ''

    @property
    def display_unit_name(self):
        return f'{self.display_name} {self.units_str}'.strip() 

class OptionDict(collections.UserDict):
    def __init__(self, ini=None, defaults={}):
        self.ini = ini
        self._opts = configparser.ConfigParser()
        if ini and os.path.exists(self.ini):
            self._opts.read(self.ini)

        self.sections = set()

        super().__init__(defaults)
        self.data: dict[str, Option]

    def add_option(self, section, name, default, var:tk.Variable=None, values:list[str]=None, min_value:float=None, max_value:float=None, display_name=None, units=None, description=None):
        section_data = self._create_section(section) 
        self.sections.add(section)
        if name not in section_data:
            section_data[name] = Option(self._opts, section,  name, default, var, values, min_value=min_value, max_value=max_value, display_name=display_name, units=units, description=description, ini=self.ini)
        section_data[name].load_user_default()
        return section_data[name]
    
    def get(self, section, name):
        section_data = self._get_section(section)
        if name not in section_data:
            raise KeyError(f'Variable "{name}" not found in section "{section}"!')
        return section_data[name]

    def options(self, section):
        section_data = self._get_section(section)
        return list(section_data.keys())
    
    def _get_section_list(self, section):
        return section.split('.')

    def _create_section(self, section):
        sections = self._get_section_list(section)
        section_data = self.data
        for sect in sections:
            section_data.setdefault(sect, {})
            section_data = section_data[sect] 
        return section_data
    
    def _get_section(self, section):
        sections = self._get_section_list(section)
        section_data = self.data
        for sect in sections:
            section_data = section_data[sect] 
        if not isinstance(section_data, dict):
            raise KeyError(f'Key "{section}" is not a section!')
        return section_data

    def save(self, *sections):
        for section in sections:
            section_data = self._get_section(section)
            for section, option in self._section_options(section, section_data):
                option.set_default()
        if self.ini:
            with open(self.ini, 'w') as f:
                self._opts.write(f)

    def _section_options(self, section, opt_dict):
        for sect, obj in opt_dict.items():
            if isinstance(obj, (collections.UserDict, dict)):
                data = self._section_options('.'.join([section, sect]), obj)
                for item in data:
                    yield item
            else:
                yield '.'.join([section, sect]), obj

    def print(self):
        for section in self.sections:
            #print(f'{section}:')
            for option in self.options(section):
                opt = self.get(section, option)
                print(f'{opt.display_name}:{opt.units}:{opt.description}')

@dataclasses.dataclass
class TreeColumn:
    name        : str
    display_name: str
    minsize     : int  = 25
    initial_size: int  = 25
    state       : bool = False


class OptionTree:
    def __init__(self, root:tk.Frame, opts:OptionDict, sections=None, show='tree headings', open=True):

        self.root = root
        self.opts = opts
        self.columns = {obj.name: obj for obj in (
                TreeColumn('default'        , 'Default'    , minsize=50, initial_size= 50 , state=False),
                TreeColumn('value'          , 'Set Value'  , minsize=50, initial_size= 150, state=True),
                TreeColumn('description'    , 'Description', minsize=50, initial_size= 350, state=False),
                #TreeColumn('save'           , '☐'           , minsize=50, initial_size= 50 , state=False),
            )
        }
        self.sections = sections if not sections or isinstance(sections, (tuple, list)) else (sections,)

        self.tree = ttk.Treeview(root, columns=tuple([obj.name for obj in self.columns.values()]), show=show)

        self.tree.heading("#0", text="Option", anchor="w")
        self.tree.column("#0", minwidth=200)
        for i, obj in enumerate(self.columns.values()):
            self.tree.heading(obj.name, text=obj.display_name)
            self.tree.column(i, width=obj.initial_size, minwidth=obj.minsize)

        self.tree.pack(expand=True, fill=tk.BOTH)
        #self.tree.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=10)

        # Bind double-click event to trigger editing
        self.tree.bind("<Double-1>", self.on_double_click)
        self._build(open)
        active_trees.append(self)

    def _is_alive(self):
        try:
            self.root.grid_info()
            return True
        except:
            return False

    @property
    def _displayed_sections(self):
        section_keys = []
        if self.sections:
            for section in self.sections:
                if section:
                    section_keys.append(section.split('.'))
        else:
            return [[]]
        return section_keys
    
    def _format_option(self, obj:Option):
        values = []
        for attr in self.columns.keys():
            if not hasattr(obj, attr):
                continue
            value = getattr(obj, attr)
            values.append(str(value) if value is not None else '')
        return values

    def _update(self):
        for row_id, (section_name, option) in self.vars.items():
            obj = self.opts.get(section_name, option)
            self.tree.item(row_id, values=self._format_option(obj))

    def _build(self, open=True):
        def add_section(opt_dict:dict[str, Option], prev_sections, base_sections=[], prev_id=''):
            if tuple(prev_sections) not in self.sections_ids:
                section = prev_sections[-1]
                self.sections_ids[tuple(prev_sections)] = self.tree.insert('', tk.END, text=section.capitalize(), open=open)

            
            for name, obj in opt_dict.items():
                if isinstance(obj, dict):
                    new_id = self.tree.insert(prev_id, tk.END, text=name.capitalize(), open=open)
                    self.sections_ids[tuple(prev_sections+[name,])] = new_id
                    add_section(obj, prev_sections+[name,], base_sections, new_id)
                else:
                    index = self.tree.insert(prev_id, tk.END, text=obj.display_unit_name, values=self._format_option(obj), open=open)
                    self.vars[index] = ('.'.join(base_sections+prev_sections), name)

        self.sections_ids = {(): ''}
        self.vars = {}
        for section_key in self._displayed_sections:
            opt_dict = self.opts
            section = ''
            prev_id = ''
            set_section_key = section_key

            for section in section_key:
                opt_dict = opt_dict[section]

            if section:
                prev_id =  self.tree.insert('', tk.END, text=section.capitalize(), open=open)
                self.sections_ids[tuple([section,])] = prev_id

            prev_sections = []
            add_section(opt_dict, prev_sections, set_section_key, prev_id)
            
        self._update()

    def on_double_click(self, event):
        # Identify the exact region clicked
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        # Find the row ID and column name
        row_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if row_id not in self.vars:
            return
        (section_name, option_name) = self.vars[row_id]
        option = self.opts.get(section_name, option_name)
        
        # Determine numerical column index (e.g., '#1' -> 0)
        col_index = int(column.replace("#", "")) - 1

        column_obj = list(self.columns.values())[col_index]
        if not column_obj.state:
            return
        
        # Get bounding box coordinates of the targeted cell
        x, y, width, height = self.tree.bbox(row_id, column)

        if col_index >= len(self.tree.item(row_id, "values")):
            return

        # Create and overlay the temporary Entry widget
        if option.values is not None:
            widget = ttk.OptionMenu(self.tree, option.var, option.var.get(), *option.values, command=lambda event=None: save_edit(widget, event, option.var))
        else:
            widget = ttk.Entry(self.tree, textvariable=option.var)
            widget.icursor(tk.END)
            widget.select_range(0, tk.END)
            

        widget.place(x=x, y=y, width=width, height=height)

        

        widget.focus()
        

        # Inner function to save the new value
        def save_edit(widget, event_obj:tk.Event=None, var:tk.Variable=None):
            if isinstance(widget, ttk.OptionMenu):
                new_val = var.get()
            else:
                new_val = widget.get()
            (section_name, option_name) = self.vars[row_id]

            _option = self.opts.get(section_name, option_name)
            _option.set(new_val)

            # Fetch all current values for this row
            row_values = list(self.tree.item(row_id, "values"))
            # Update the specific column value
            row_values[col_index] = _option.value
            # Apply changes back to the tree row
            self.tree.item(row_id, values=row_values)

            _update_trees()

            # Skip deleting widget if user scrolls on a combobox 
            if isinstance(widget, ttk.Combobox) and str(event_obj.type) == '35':
                return
            
            widget.destroy()
            self.tree.unbind("<MouseWheel>")
            

        def reposition(widget:tk.Widget):
            widget.place_forget()

            if self.tree.bbox(row_id, column):
                x, y, width, height = self.tree.bbox(row_id, column)
                widget.place(x=x, y=y, width=width, height=height)
                widget.focus()

        def _on_focus_out(widget):
            row_values = list(self.tree.item(row_id, "values"))

            # Update the specific column value
            option.set(row_values[col_index]) 
            widget.destroy()
            self.tree.unbind("<MouseWheel>")

        
        # Bind lifecycle events to the temporary widget
        self.tree.bind("<MouseWheel>", lambda *args: self.tree.after('idle', reposition, widget))
        widget.bind("<Return>", lambda e: save_edit(widget))
        widget.bind("<FocusOut>", lambda e: _on_focus_out(widget))
    
    def save(self):
        self.opts.save(*self.sections)

    def load(self):
        for section in self.sections:
            for sect in self.opts.sections:
                if not sect.startswith(section):
                    continue
                for option in self.opts.options(sect):
                    self.opts.get(sect, option).load_user_default()
        self._update()

global active_trees
active_trees: list[OptionTree] = []

def _update_trees():
    for tree in active_trees:
        if tree._is_alive():
            tree._update()

if __name__ == '__main__':

    section = 'robot.move.gravity'
    opts = OptionDict()
    tk.Tk()
    opts.add_option(section, 'tool', 0   , tk.IntVar()   , display_name='Tool'    , description='Tool number')
    opts.add_option(section, 'user', 0   , tk.IntVar()   , display_name='User'    , description='Artifact number')
    opts.add_option(section, 'vel' , 10.0, tk.DoubleVar(), display_name='Velocity', units='%%', description='Percentage of speed')
    
    for section in opts.sections:
        print(section)
        for option in opts.options(section):
            print(option)