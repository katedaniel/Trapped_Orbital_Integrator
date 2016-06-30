#!/bin/csh

git clone https://github.com/katedaniel/Trapped_Orbital_Integrator.git
cd Trapped_Orbital_Integrator
#chmod +x /MC_fnew.py
#chmod +x /LF_L4.cpp

#module load python
#module load all-pkgs
#module load AstroPy

module load gcc
g++ LF_L4.cpp -o LF_L4
chmod +x /LF_L4

condor_submit filenamesubmit
condor_q kjdaniel
