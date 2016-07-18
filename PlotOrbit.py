import numpy as np
import Orbit_Code 
reload(Orbit_Code)

def parseFilename(filename):
   
    parts = filename.split("=")
    args = []
    for l in range(1, len(parts)):
        num = float(parts[l].split(")")[0])
        args.append(num)
    return args
    
    
filename = "C:/Trapped_Orbital_Integrator/tar_master_20/qp_file_1/qp_(m=4)_(th=20)_(t=2)_(CR=8)_(eps=0.3)_(x0=-10.79)_(y0=1.29787)_(vx0=27.5492)_(vy0=-176.19).txt"
a = parseFilename(filename)
orbit = Orbit_Code.Orbit_Calculator(a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],a[8])
data = np.loadtxt(filename,delimiter=" ",dtype= str).astype(float)
t = data[:,0]   #next two lines switch order of t,x,y,vx,vy to x,y,vx,vy,t
data = np.c_[data[:,1:5] ,t] 
orbit.setqp(data)   
orbit.plot(1)