import Table_Helper as tableMaker
reload(tableMaker)
import numpy as np
from timeit import default_timer

start = default_timer()
print("Calculating...")

filepath = "C:/Trapped_Orbital_Integrator/tar_master_20/" #filepath to tar files
tableMaker.unTar(filepath) #untar the files
table = tableMaker.genTable(filepath) #make table of analysis stuff

duration = default_timer() - start
print "time: %s s" % str(duration) 

dataFilePath = "C:/Users/Noah/Documents/GitHub/Trapped_Orbital_Integrator/table_20.txt"
np.savetxt(dataFilePath, table.astype(str), delimiter = " ",fmt='%s')