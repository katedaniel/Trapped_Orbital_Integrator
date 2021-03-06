'''
Authors: Luke Barbano and Noah Lifset
Description: 
    This file implements the Orbit_Calculator class, which performs all of the 
calculations associated with numerically simulating a star's orbit about the 
center of a spiral galaxy and plots the results. 
    The class takes in various parameters relating to the spiral as well as the 
star's initial conditions. It can then calculate the positions of the star's 
orbit for some time interval, plot the results in the non-rotating frame, 
translate the positions to the rotating frame of the spiral, plot the orbit in 
the rotating frame, and save the position/velocity information from the non-
rotating frame to a dump file in a specified file path. The accompanying file 
"OrbitDemonstration.py" provides a walkthrough of how to use this class.  
    As an aside, this class is not super well written by computer science standards
given its reliance on global variables in lieu of assigning attributes to the 
instance of the class; however, this class implementation best salvaged the 
previous version of the code and might be slightly faster since the self instance 
of the class doesn't have to constanly access the many, frequently used variables. 
Note: If any changes are made to the Orbit_Calculator class, make sure to restart the 
kernel so the changes will be implemented when using the class.
Class Summary:
    
--------------------------------------------------------------------------------
class Orbit_Calculator(__builtin__.object)
       
Constructor:     
     __init__(self, m, IntTime, CR, epsilon, x0, y0, vx0, vy0)
        m = number of spiral arms
        IntTime = Duration of simulation (units implicit gigayears)
        CR = Corotation radius (units implicit kiloparsecs)
        epsilon = epsilon of spiral
        x0,y0,vx0,vy0 = intial x,y,vx,and vy of star (implicit units kpc and km/s respectively)
    
Public (Callable) Methods:
    
    --makeOrbit(self)
        -calculates the orbit
        -creates global numpy arrays for qp and qpR
    --getqp(self)
        -returns numpy array qp
        
    --getqpR(self)
        -returns numpy array qpR        
                       
    --saveData(self)  
        -save qp to a file in a designated filepath 
        
    --plot(self, plotOption)
        -plots the orbit
        -if plotOption == 0, plots in the non-rotating frame
        -if plotOption is anything but 0, plots in the rotating frame
         
    --doAllThings(self)
        -calls makeOrbit(), saveData(), and plot(1)
        -calculates the orbit, saves qp, and plot orbit in rotating frame
    
    --findEj(self)
        -calculates Ej (Jacobi Integral)
        -returns numpy array Ej
        
    --Capture(self)
        -calculates capture criteria for guiding center
        -returns numpy array of lambdas (capture criteria) 
    
_______________________________________________________________________________    
'''
import astropy.units as u
import astropy.constants as const
import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
from timeit import default_timer
from numpy import arange
from numpy import meshgrid

################################################################################
# Defining some constants
################################################################################
pi = np.pi
G = const.G

################################################################################
# Defining model dependent constants
################################################################################
      
#Disk parameters (You can toggle these)
vc = 220 *u.km /u.s             # Circular velocity of the disk
RSun = 8 *u.kpc                 # Solar galactocentric radius
SigmaSun = 50 *u.Msun /u.pc**2  # Surface density at the solar radius
Rd = 2.5 *u.kpc                 # Scale length of the disk 
  

class Orbit_Calculator(object):

################################################################################
#Constructor
################################################################################

    def __init__(self,m1,theta1,IntTime1,CR1,epsilon1,x01,y01,vx01,vy01):
        
        #The arguments given are assigned to global variables.
        #This is obviously not the best way to use global variables in a class,
        #but in doing so the original code is more easily salvaged.
        
        global m
        global IntTime
        global CR
        global epsilon
        global x0
        global y0
        global vx0
        global vy0
        global IntTimeUnitless   
        global StepTime      
        global NSteps                  
        global T
        global OmegaCR
        global theta 
        
        #Assign global variables
        m = int(m1)
        theta = theta1*u.degree
        IntTime = IntTime1*u.Gyr
        CR = CR1*u.kpc
        epsilon = epsilon1
        x0 = x01
        y0 = y01
        vx0 = vx01
        vy0 = vy01 
        OmegaCR = vc/CR
        
        #Some time related stuff
        StepTime = 100000.*u.yr                          #Time between each calculation   
        IntTimeUnitless = (IntTime/u.yr).decompose()     #Simulation time
        NSteps = np.rint((IntTime/StepTime).decompose()) #Integer number of total steps to take
        T = np.linspace(0,IntTimeUnitless,NSteps)        #Time values
        
        self.__findalpha()
        self.__findhcr()
# Note: 
# All methods preceded by "__" are private functions that can't be called
# outside of the class 
            
################################################################################
# Method for Disk Parameters
################################################################################

# Calculates the surface density of the disk at any radius
    def __findSurfaceDensity(self,R): 
        
        Sigma0 = SigmaSun *np.exp(RSun/Rd)
        SigmaR = Sigma0 *np.exp(-R/Rd)
        return SigmaR


################################################################################        
# Methods for spiral parameters
################################################################################

# Calculates parameter alpha
    def __findalpha(self): 
        
        global alpha
        alpha = m/np.tan(theta)
        
# Calculates amplitude of spiral perturbation
    def __findA(self,R): 
        Sigma = self.__findSurfaceDensity(R)
        A = 2. *pi *G *Sigma*epsilon*R/alpha
        return A
        
# Calculates hcr, Jacobi integral for a star at corotation with no spirals
    def __findhcr(self):
        disk_potential = (vc**2)*np.log(CR/u.kpc)
        E_tot = disk_potential + 0.5*(vc**2)
        L_z = CR*vc
        global hcr
        hcr = (E_tot - OmegaCR*L_z) #units of (km/s)^2     
        
                
################################################################################
#Private Calculation Methods
################################################################################    

# Calculates the acceleration in this potential at coordinate x-y
    def __dvdt(self,qp,tnow):         
        
        x = qp[0] *u.kpc
        y = qp[1] *u.kpc
        time = tnow *u.yr
        R = (x**2 + y**2)
        A = self.__findA(np.sqrt(R))
        
        # Find acceleration from logarithmic disk
        dvxD = vc**2 *x/R
        dvyD = vc**2 *y/R
        
        # Find acceleration from spiral
        var1 = (m *time *vc /CR)*u.rad -m *np.arctan(y/x) -alpha *np.log(np.sqrt(R)/CR)*u.rad
        var2 = (-alpha-(1-np.sqrt(R)/Rd)*(np.tan(var1)**-1))
        dvSFront = -A *np.sin(var1)/(R)
        dvxS = dvSFront *(m*y + var2*x)
        dvyS = dvSFront *(-m*x + var2*y)
    
        # Find total acceleration
        dvxdt = ((dvxD + dvxS)/(u.km /u.s**2))
        dvydt = ((dvyD + dvyS)/(u.km /u.s**2))
        return np.array([dvxdt,dvydt])
                     
# Perform a single leapstep (t+dt), using kick-drift-kick method
    def __leapstep(self,qpnow,tnow): 
        
        dt = (StepTime/u.year)*3.15576e+07 #convert to seconds/remove units
        x = qpnow[0]
        y = qpnow[1]
        vx = qpnow[2]
        vy = qpnow[3]
        # Note: x and y are in kpc, vx and vy are in km/s
        
        a = self.__dvdt(qpnow,tnow)      # Find acceleration at this coordinate
        vx = vx -0.5 *dt *a[0]           # Advance v_x by half step
        vy = vy -0.5 *dt *a[1]           # Advance v_y by half step
        x = x +(dt*vx*3.24077928947e-17) # Advance x by full step, while converting v*dt from km to kpc
        y = y +(dt*vy*3.24077928947e-17) # Advance y by full step, while converting v*dt from km to kpc
        # x and y are in kpc, vx and vy are in km/s
        
        qpmid = np.array([x,y,vx,vy])
        a  = self.__dvdt(qpmid,tnow)     # Find a at new position and complete the velocity step
        vx = vx -0.5 *dt *a[0]           # Complete v_x step
        vy = vy -0.5 *dt *a[1]           # Complete v_y step
        
        return np.array([x,y,vx,vy,tnow]) 
        
# Helper function to plot the spiral arms, arm points calcualted in polar 
# coordinates and then converted to rectangular for plotting  
    def __plotArms(self,ax):
        
        points = 20                     #Number of points of each arm to plot
        radius = np.zeros(points)       #empty array for arm radii
        t = np.linspace(pi/24,pi/2+pi/16,points)  #array of angles 
        for i in xrange(0,m):
            radius = (CR/u.kpc)*np.exp((-m*(t)+np.pi)/alpha)
            ax.plot(radius*np.cos(t+2*np.pi*i/m),radius*np.sin(t+2*np.pi*i/m), color="purple",ls='dotted')   
        return
          
# Convert coordinates from non-rotating frame to rotating frame
    def __toRframe(self,qpl):  
        
        # Pull out cartesian non-rotating info
        x = qpl[:,0]
        y = qpl[:,1]
        vx = qpl[:,2]
        vy = qpl[:,3]
        t = qpl[:,4]*u.yr
        # Calculate polar rotating coordinates for position
        R = np.sqrt(x**2 + y**2)
        phi = np.arctan2(y,x)*u.rad
        phiR= phi - (t*OmegaCR).decompose() *u.rad
        xR = R *np.cos(phiR)
        yR = R *np.sin(phiR)
        # Calculate polar rotating coordinates for velocity
        v_tot = np.sqrt(vx**2 + vy**2)
        theta = np.arctan2(vy,vx)*u.rad #angle between velocity vector and x-axis
        alph = theta - phi # angle between position and velocity vectors
        vr = v_tot*np.cos(alph)
        vphi = v_tot*np.sin(alph)
        vphiR = vphi - ((OmegaCR*R*u.kpc)/(u.km/u.s))
        vxR = vr *np.cos(phiR) + vphiR*np.sin(phiR)
        vyR = vr *np.sin(phiR) + vphiR*np.cos(phiR)
        # Put it all back into a new array for rotating frame
        qpR = np.transpose(np.array([xR,yR,vxR,vyR,vr,vphi,vphiR]))
        return qpR
        
                                            
################################################################################
#Public Methods (Callable)
################################################################################  
    
# Calls the previously defined functions to calculate the orbit in both frames  
    def makeOrbit(self):
        
        start = default_timer()
    
        qp0 = np.array([x0,y0,vx0,vy0,T[0]])
        self.qp = np.zeros(shape=(len(T),5))
        self.qp[0] = qp0
        print "Steps: %s" %str(NSteps)
        for i in range(len(T)):
            qpstep = qp0 = self.__leapstep(qp0,T[i])
            self.qp[i] = qpstep
            
        global qpR
        qpR =  self.__toRframe(self.qp) 
          
        duration = default_timer() - start 
        print "time: %s s" % str(duration)
        return

# Returns qp                 
    def getqp(self):
        return self.qp
        
# Returns qpR        
    def getqpR(self):
        return self.qpR

# Returns NSteps                 
    def getNSteps(self):
        return NSteps
        
# Sets qp                 
    def setqp(self,qps):
        self.qp = qps
        self.qpR = self.__toRframe(self.qp)
        return
        
# Saves data from non-rotating frame in dump file  
# Remember that each computer has a different file path    
    def saveData(self,filepath,):
        filename = "qp_(m=%s)_(th=%s)_(t=%s)_(CR=%s)_(eps=%s)_(x0=%s)_(y0=%s)_(vx0=%s)_(vy0=%s)" %(str(m),
        str(theta/u.degree),str(IntTime/u.Gyr),str(CR/u.kpc),str(epsilon),str(x0),str(y0),str(vx0),str(vy0))
        np.save(filepath + filename,self.qp) 
        return
        
# Plots the orbit  
# For plot of orbit in non-rotating frame, enter 0 as the plot option
# For plot of orbit in rotating frame, enter 1 as the plot option (recomended)
    def plot(self,plotOption):
        
        plt.close('all')         #close old plots still up
        
        fig = plt.figure(1)      #setting up the basic figure with axes and labels
        ax = fig.add_subplot(1,1,1)
        ax.set_xlabel(r'$x$ (kpc)')
        ax.set_ylabel(r'$y$ (kpc)')
        plt.axis([-20,20,-20,20])
        ax.set_aspect('equal', 'datalim')
        
        #calculate Lindlbad Resonance radii
        R_1o = (m+np.sqrt(2))*vc/(m*OmegaCR)
        R_1i = (m-np.sqrt(2))*vc/(m*OmegaCR)
        #calculate ultraharmonic resonance radii
        R_2o = ((2*m)+np.sqrt(2))*vc/((2*m)*OmegaCR)
        R_2i = ((2*m)-np.sqrt(2))*vc/((2*m)*OmegaCR)
        #plot the lindblad radii
        lind1 = plt.Circle((0,0), (R_1o/u.kpc), color='g', fill=False,ls = 'dashed')
        lind2 = plt.Circle((0,0), (R_1i/u.kpc), color='g', fill=False,ls = 'dashed')
        lind1uh = plt.Circle((0,0), (R_2o/u.kpc), color='g', fill=False,ls = 'dotted')
        lind2uh = plt.Circle((0,0), (R_2i/u.kpc), color='g', fill=False,ls = 'dotted')
        ax.add_patch(lind1)
        ax.add_patch(lind2)
        ax.add_patch(lind1uh)
        ax.add_patch(lind2uh)
        
        self.__plotArms(ax)
        plt.show()
        
        #Plot corotation radius
        circ = plt.Circle((0,0), (CR/u.kpc), color='g', fill=False) #plotting CR radius
        ax.add_patch(circ)
        
        #Plot the capture region
        if plotOption != 0:
            delta = 0.025
            x_range = arange(-13.0, 13.0, delta)
            y_range = arange(-13.0, 13.0, delta)
            X, Y = meshgrid(x_range,y_range)
            R = np.sqrt((X**2) + (Y**2))
            phi = np.arctan2(Y,X)
            #find Phi_eff_min
            A_CR = self.__findA(CR).to((u.km/u.s)**2)
            phi_min = (hcr - A_CR)/((u.km/u.s)**2)
            phi_max = (hcr + A_CR)/((u.km/u.s)**2)
            #defining the contour equation
            A = self.__findA(R*u.kpc).to((u.km/u.s)**2)
            spiral_potential = A*np.cos(-alpha*np.log(R*u.kpc/CR)*u.rad -m*phi*u.rad)
            disk_potential = (vc**2)*np.log(R)
            potential = spiral_potential + disk_potential
            func = (0.5*(OmegaCR**2)*(CR**2) - (OmegaCR**2)*CR*(R*u.kpc) + potential)/((u.km/u.s)**2)
            #plotting contour
            plt.contourf(X,Y,func,[phi_min,phi_max],colors='gray',alpha=0.3)
            
        if plotOption==0:  #this plots in the inertial frame (rarely used)
            self.qps = self.qp
        elif plotOption==1:  #this plots in the rotatig frame (usually used)
            self.qps = self.qpR
            [Rgx,Rgy] = self.findRg()
            plt.plot(Rgx,Rgy,color="black", markevery=500, marker='.', ms=8)
        else:   #This is primarily used for aimation stuff (plots just circles and arms)
            return fig, ax  
        plt.plot(self.qps[:,0],self.qps[:,1], color="SlateBlue", markevery=500, marker='.', ms=8) 
        
        return fig, ax
        
    ###Creates a plot of orbital properties over time for an individual qp
    #shows lambda, normalized random energy, and normalized radius (for star and guiding center)
    def plot_prop(self):
        
        plt.close('all')         #close old plots still up
        
        fig = plt.figure(1)      #setting up the basic figure with axes and labels
        ax1 = fig.add_subplot(3,1,1)
        ax2 = fig.add_subplot(3,1,2, sharex = ax1)
        ax3 = fig.add_subplot(3,1,3)
        fig.subplots_adjust(hspace=0.)
        
        ax1.set_ylabel(r'$\Lambda_{nc,2} (t)$', size=18)
        ax2.set_ylabel(r'$\frac{E_{ran} (t)}{E_{ran,0}}$', size=22)
        ax3.set_ylabel(r'$\frac{R_{L} (t) - R_{CR}}{kpc}$', size=20)
        ax3.set_xlabel(r't ($10^8$ years)')
        
        ax1.set_ylim([-1.3,1.3])
        ax2.set_ylim([-0.5,5.9])
        ax3.set_ylim([-2.9,2.9])
        
        ax1.set_xticklabels([])
        ax2.set_xticklabels([])
        ax1.axhline(y=1,c='0.5')
        ax1.axhline(y=-1,c='0.5')
        ax2.axhline(y=1,c='0.5')
        
        #calculate Lindlbad Resonance radius
        R_1o = ((m+np.sqrt(2))*vc/(m*OmegaCR)).to(u.kpc) - CR
        R_1i = ((m-np.sqrt(2))*vc/(m*OmegaCR)).to(u.kpc) - CR
        #calculate ultraharmonic resonance radius
        R_2o = (((2*m)+np.sqrt(2))*vc/((2*m)*OmegaCR)).to(u.kpc) - CR
        R_2i = (((2*m)-np.sqrt(2))*vc/((2*m)*OmegaCR)).to(u.kpc) - CR
        #plot these radii
        ax3.axhline(y=0,c='0.9')
        ax3.axhline(y=R_1o/u.kpc, ls='dashed',c='0.5')
        ax3.axhline(y=R_1i/u.kpc, ls='dashed',c='0.5') 
        ax3.axhline(y=R_2o/u.kpc, ls='dotted',c='0.5')
        ax3.axhline(y=R_2i/u.kpc, ls='dotted',c='0.5')       
        
        data = self.findLam()     #pulling the orbital data
        Lam = data[0]
        E_ran = data[5]
        
        x = self.qp[:,0]*u.kpc    #pulling data from qp
        y = self.qp[:,1]*u.kpc
        vx = self.qp[:,2]*u.km/u.s
        vy = self.qp[:,3]*u.km/u.s
        t = self.qp[:,4]*u.yr
        R = np.sqrt(x**2 + y**2)
        phi = np.arctan2(y,x)
        vphi = -np.sqrt(vx**2 + vy**2)*np.sin(phi - np.arctan2(vy,vx))
        R_g = (R*vphi/vc).to(u.kpc)
        
        E_ran_var = E_ran/(E_ran[0])   #calculating final stuff for the plot
        R_var = R - CR
        R_g_var = R_g - CR
        
        ax1.plot(t, Lam, c='purple')
        ax2.plot(t, E_ran_var, c='b')
        ax3.plot(t, R_var, c='r', ls='dashed')
        ax3.plot(t, R_g_var, c='black')
        
        plt.show()    


# Calculates position of guiding center radius in rotating frame        
    def findRg(self):
        #pulling info out of qp
        x = self.qp[:,0]*u.kpc
        y = self.qp[:,1]*u.kpc
        vx = self.qp[:,2]*u.km/u.s
        vy = self.qp[:,3]*u.km/u.s
        t = self.qp[:,4]*u.yr
        R_g = (np.sqrt(x**2 + y**2)*-np.sqrt(vx**2 + vy**2)*np.sin(np.arctan2(y,x) - np.arctan2(vy,vx))/vc)
        phi = np.arctan2(y,x)
        phiR= phi - (t*OmegaCR).decompose() *u.rad
        xR = R_g *np.cos(phiR)
        yR = R_g *np.sin(phiR)
        return np.array([xR,yR])
        
#this function makes an x/vx poincare map using a spline for the discretized qp
#it has not been used for anything and might need some fixing         
    def Poincare(self):
        plt.close('all')
        yspline = interpolate.splrep(self.qp[:,4], self.qpR[:,1], s=0)
        roots = interpolate.sproot(yspline)
        if len(roots)==0:
            return 
        xspline = interpolate.splrep(self.qp[:,4], self.qpR[:,0], s=0)
        vxspline = interpolate.splrep(self.qp[:,4], self.qpR[:,2], s=0)
        x = interpolate.splev(roots, xspline)
        vx = interpolate.splev(roots, vxspline)
        plt.scatter(x,vx)
        plt.show()
        return
        
###This function calculates a few important physical values for a given qp
#it calculates lambda, E_j, effective potential, angmom, total energy, and random energy at every discretized step
    def findLam(self):
        #pulling qp data
        x = self.qp[:,0]*u.kpc
        y = self.qp[:,1]*u.kpc
        vx = self.qp[:,2]*u.km/u.s
        vy = self.qp[:,3]*u.km/u.s
        t = self.qp[:,4]*u.yr
        #finding some preliminary variables
        R = np.sqrt(x**2 + y**2)
        phi = np.arctan2(y,x)
        vphi = np.sqrt(vx**2 + vy**2)*np.sin(np.arctan2(vy,vx) - phi)
        R_g = (R*vphi/vc).to(u.kpc)
        A = self.__findA(R).to((u.km/u.s)**2)
        A_CR = self.__findA(CR).to((u.km/u.s)**2)
        A_g = self.__findA(R_g).to((u.km/u.s)**2)
        #finding potentials of the star and the guiding center
        disk_potential = (vc**2)*np.log(R/u.kpc)
        disk_potential_g = (vc**2)*np.log(R_g/u.kpc)
        spiral_potential = A*np.cos(-alpha*np.log(R/CR)*u.rad + (m*OmegaCR*t)*u.rad -m*phi)
        spiral_potential_g = A_g*np.cos(-alpha*np.log(R_g/CR)*u.rad + (m*OmegaCR*t)*u.rad -m*phi)
        potential = disk_potential + spiral_potential
        potential_g = disk_potential_g + spiral_potential_g
        #finding total energy for the star and the guiding center
        E_tot = potential + 0.5*(vx**2 + vy**2)
        E_tot_g = potential_g + 0.5*(vc**2)
        #finding E_j
        L_z = R*vphi
        E_j = (E_tot - OmegaCR*L_z).to((u.km/u.s)**2)
        #finding E_ran
        E_ran = E_tot - E_tot_g
        #finding Lambda
        Lam_c = (E_j[0] - hcr)/A_CR
        Lam_nc2 = Lam_c - ((R_g/CR)*(E_ran/A_CR))
        #finding effective potential
        phi_eff = potential - 0.5*(OmegaCR*R)**2
        #return array of all the important physical values
        return np.array([Lam_nc2, E_j, phi_eff, L_z, E_tot, E_ran])

###This function calculates a special lambda value representing its trapped orbit evolution
    def Lam_special(self):
        #use find_lam function to pull physical data
        phys_dat = self.findLam()
        Lam = phys_dat[0]
        if np.absolute(Lam[0]) < 1.:  #starts trapped
            if np.absolute(Lam[-1]) < 1.:  #ends trapped
                if (np.absolute(Lam) < 1.).sum() == Lam.size: #always trapped
                    lam_spec  = 0 #ALWAYS TRAPPED
                else:
                    lam_spec  = 1 #TRAPPED AT BEGINNING AND END, BUT NOT MIDDLE
            else:
                lam_spec  = 2 #TRAPPED AT BEGINNING BUT NOT END
        if np.absolute(Lam[0]) >= 1.: #starts free
            if np.absolute(Lam[-1]) >= 1.: #ends free
                if (np.absolute(Lam) < 1.).sum() > 0: #trapped at any point
                    lam_spec  = 3 #FREE AT BEGINNING AND END, BUT NOT MIDDLE
                else:
                    lam_spec  = 4 #ALWAYS FREE
            else:
                lam_spec  = 5 #FREE AT BEGINNING BUT NOT END
        return lam_spec    

###This function calculates angmom for a qp at 5 spaced out times       
    def findLz(self):
        #use find_lam function to pull angmom data
        phys_dat = self.findLam()
        Lz = phys_dat[3]
        size = Lz.size
        Lz_0 = Lz[0]        #initial angmom
        Lz_1 = Lz[(size/4.)]   #angmom after a quarter of the time
        Lz_2 = Lz[(size/2.)]   #angmom after half the time
        Lz_3 = Lz[(3.*size/4.)]  #angmom after three quarters time
        Lz_4 = Lz[(size-1)]     #final angmom
        return np.array([Lz_0,Lz_1,Lz_2,Lz_3,Lz_4])
