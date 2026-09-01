import os

import numpy as np
import xlsxwriter
import matplotlib.pyplot as plt

os.chdir(os.path.dirname(__file__))

C = 3E8
E = 8.85e-12

class antenna:
    def __init__(self, z0:float, zn: float, f: int, r:float, N:int):
        
        self.radius = r
        self.N = N
        self.L = zn-z0
        self.dz = self.L/self.N
        self.feed = self.N // 2 
        self.z = np.linspace(z0 + self.dz/2, zn - self.dz/2, self.N)
        self.update_freq(f)
        
        
        print('Zmn')
        for m in range(self.N):
            print(f'({m},0) :{self.Z[m,0]}')

        print(f'\nInput impedence: {self.Zin} @ {self.frequency} Hz\n')

        for n in range(self.N):
            print(f'{n}: {self.I[n]}')
        print('\n|F|')
        for theta in (0, 10, 20, 30, 40, 50, 60, 70, 80, 90):
            print(f'{theta}: {abs(self.F_theta(theta))/abs(self.F_theta(90))}')
        
    def update_freq(self, freq):
        self.frequency = freq
        self.lambd = C/self.frequency
        self.beta = 2*np.pi/self.lambd
        self.Z = self.get_Z()

    def Zmn(self, m, n):
        dzmn = self.z[m] - self.z[n]
        R = np.sqrt(dzmn**2 + self.radius**2)
        kernel = ((1+1j*self.beta*R)*(2*R**2-3*self.radius**2)+self.beta**2*R**2*self.radius**2)*np.exp(-1j*self.beta*R)/R**5
        return kernel * self.dz / (4*np.pi*1j * 2 * np.pi * self.frequency * E)


    def get_Z(self):
        Z = np.zeros((self.N, self.N), dtype=complex)
        for m in range(self.N):
            for n in range(self.N):
                Z[m,n] = self.Zmn(m,n)
        return Z

    @property
    def V(self):
        V = np.zeros(self.N, dtype=complex)
        V[self.feed] = 1.0                 # 1 Volt source
        return V
    
    @property
    def I(self):
        return np.linalg.solve(self.Z, -self.V)

    @property
    def Zin(self):
        return self.V[self.feed] / self.I[self.feed]
    
    def Lambda(self, zn):
        return np.exp(1j*self.beta*zn)
    
    def F_theta(self, theta):
        f_theta = 0.0
        for n in range(self.N):
            f_theta += self.I[n]*self.Lambda(self.z[n]*np.cos(np.deg2rad(theta)))
        return f_theta * np.sin(np.deg2rad(theta))

def normalize_dB(pattern):
    power = np.abs(pattern)**2
    return 10 * np.log10(power / np.max(power) + 1e-6)

def show_radiation_pattern(ant:antenna, phi):
    th = np.radians(np.linspace(-180, 180, 360))
    rad_pattern = normalize_dB(np.array([ant.F_theta(theta) for theta in th]))
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='polar')
    ax.plot(th, rad_pattern, label='E-plane ($\phi=0^{\circ}$)'if phi==0 else 'H-plane ($\phi=90^{\circ}$)')
    ax.set_theta_zero_location('N') # Set 0 degrees to North
    ax.set_theta_direction(-1)      # Clockwise
    ax.set_ylim(-30, 0)             # dB scale
    plt.legend()
    plt.title(f'Antenna Radiation Pattern ({"E Plane" if phi==0 else "H Plane"})')
    plt.show()

def write_xlsx(name, ant: antenna):
    wb = xlsxwriter.Workbook(name)
    ws = wb.add_worksheet('Antenna results')
    col = 0
    row = 0
    ws.write_row(row,col, data=['n','Im[I_m] (A)'])
    for n in range(ant.N):
        row += 1
        ws.write_row(row, col, data=[n+1, ant.I[n].imag])

    col = 4
    row = 0
    ws.write_row(row,col, data=['\\theta','|F|'])
    for theta in (0, 10, 20, 30, 40, 50, 60, 70, 80, 90):
        row += 1
        ws.write_row(row, col, data=[theta, abs(ant.F_theta(theta))/abs(ant.F_theta(90))])

    col = 7
    row = 0
    ws.write_row(row, col, data=['Freq (MHz)','Zin (\Omega)'])
    for freq in (200e6, 250e6, 300e6, 350e6, 400e6):
        row += 1
        at.update_freq(freq)
        ws.write_row(row, col, data=[ant.frequency/1e6, f'{ant.Zin}'])
   
    
    
    wb.close()
    

if __name__ == '__main__':
    #f = 1e9
    #lambd = 2*np.pi/f
    #L = 0.48*lambd
    #at = antenna(-L/2, L/2, f, 0.005*lambd,  11)
    at = antenna(-0.25, 0.25, 300e6, 0.006,  11)
    show_radiation_pattern(at, 0)
    write_xlsx('Project1_S26.xlsx', at)
    #at = antenna(-0.25, 0.25, 300e6, 0.006,  11)
    #print(f'\nZin')
    #for freq in (200e6, 250e6, 300e6, 350e6, 400e6):
    #    at.update_freq(freq)
    #    print(f'{int(freq/1e6)} MHz: {at.Zin}')
    