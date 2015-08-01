Simpact Purple
===============

*Simpact Purple* is a module for agent-based simulations of HIV and other 
sexually transmitted diseases and is part of a suite of HIV modeling tools
known as *Simpact*. It is a useful tool for public health officials and 
epidemiologists which implements a parallelized algorithm based on queue 
theory. 

Installation
-----------

Clone this repository:

```
git clone https://github.com/seanluciotolentino/SimpactPurple.git
```

And install it:

```
python setup.py install
```

Run the test script to make sure that everything worked out okay:

```
python bin/TestRuns.py
```

Examples of how to run simulations are in the bin folder. Each file contains
as short description of what the script is doing. Additional documentation 
on how the algorithm works and how to set variables yourself can be 
found [here] (http://pythonhosted.org/SimpactPurple/).

Parallelism is implemented with the multiprocessing module for running on a
single node (i.e. running on your laptop). 

Distributed / Cluster Computing
--------------

If you want to run distributed versions, scripting is more involved. First you'll
need to have [open-mpi] (http://www.open-mpi.org/) and [mpi4py] (https://pypi.python.org/pypi/mpi4py)
installed. 

The algorithm is the same, the difference now is that openMPI handles the 
creation of extra processes (as opposed to the multiprocessing module). To run
a single community simulation on a cluster environment you would run

```
mpirun -n 16 python my_script.py
```

This allocates 16 slots for your process. The script `my_scripy.py` should test for 
the rank of the process and assign the nodes role accordingly (see documentation
for mpi4py). An example of how to set up a distributed
script is in `bin\ApproximateBayesianComputation\ABCParameterInference.py`. 

Additionally `bin\MigrationExploration.py` is an example of running a simulation
with migration. 

Complete description of the algorithm
---------------

The most complete description of the algorithm is S. Lucio Tolentino's 
dissertation, hosted [here] (http://ir.uiowa.edu/cgi/viewcontent.cgi?article=5516&context=etd).

Chapter 3 details the single node parallel model. Chapter 4 details the distributed
version. And Chapter 5 details the work on migration. 

