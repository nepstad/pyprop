import commands
import pyprop.utilities.submitpbs as submit

cm_to_inch = 1./2.5

#-----------------------------------------------------------------
#            Parse input files
#-----------------------------------------------------------------

def LoadEigenstates(**args):
	inputfile = GetInputFile(**args)

	conf = SetupConfig(**args)
	c = conf.RadialRepresentation
	dr = (c.rank0[1] - c.rank0[0]) / float(c.rank0[2])

	f = tables.openFile(inputfile, "r")
	try:
		E1 = f.root.complete.binding.eigenvalues[:]
		V1 = conj(f.root.complete.binding.eigenstates[:].transpose())
		E2 = f.root.complete.unbinding.eigenvalues[:]
		V2 = conj(f.root.complete.unbinding.eigenstates[:].transpose())
	finally:
		f.close()

	return E1, V1*dr, E2, V2*dr

def LoadBoundEigenstates(**args):	
	threshold = -0.5
	E1, V1, E2, V2 = LoadEigenstates(**args)

	thresholdIndex = max(where(E1<=threshold)[0])
	E1 = E1[:thresholdIndex]
	V1 = V1[:thresholdIndex,:]

	return E1, V1

def LoadContinuumEigenstates(**args):
	threshold = -0.5
	upperThreshold = 0.0

	E1, V1, E2, V2 = LoadEigenstates(**args)
	
	maxIndex1 = max(where(E1<=upperThreshold)[0]) + 1
	thresholdIndex = max(where(E1<=threshold)[0])
	E1 = E1[thresholdIndex:maxIndex1]
	V1 = V1[thresholdIndex:maxIndex1, :]

	maxIndex2 = max(where(E2<=upperThreshold)[0]) + 1
	E2 = E2[:maxIndex2]
	V2 = V2[:maxIndex2, :]

	return E1, V1, E2, V2

def MakeDelayScanPlots(save=False):
	interactive = rcParams["interactive"]
	rcParams["interactive"] = False
	size = 16 * cm_to_inch

	def Plot(filename):
		t, c = GetScanDelayCorrelation(outputfile=filename, partitionCount=8)
		figure(figsize=(size,size*3./4.))
		ionization = 1 - sum(c[:,:20], axis=1)
		plot(t, ionization, label="Ionization")
		for i in range(10):
			if i < 5:
				label = "$n = %i$" % i
			else:
				label = "_nolegend_"
			plot(t, c[:,i], label=label)
		axis([20, 100, 0,  0.8])
		legend()
		xlabel("Pulse Delay")
		ylabel("Proabability")

	def PlotEnergy(molecule, filename):
		t, E, c = GetScanDelayEnergyDistribution(molecule=molecule, outputfile=filename, partitionCount=8)
		figure(figsize=(size, size*3./4))
		pcolormesh(t, (E+0.5)/2./eV_to_au, sum(c, axis=1).transpose(), shading="flat")
		xlabel("Pulse Delay")
		ylabel("Energy")

		
	PlotEnergy("hd+", "outputfiles/hd+/delay_%i.h5")
	title("$HD^+$")
	Plot("outputfiles/hd+/delay_%i.h5")
	title("$HD^+$")
	if save:
		pylab.savefig("doc/fig/delay_scan_hdp.eps")
	
	PlotEnergy("h2+", "outputfiles/h2+/delay_%i.h5")
	title("$H_2^+$")
	Plot("outputfiles/h2+/delay_%i.h5")
	title("$H_2^+$")
	if save:
		pylab.savefig("doc/fig/delay_scan_h2p.eps")
	
	PlotEnergy("d2+", "outputfiles/d2+/delay_%i.h5")
	title("$D_2^+$")
	Plot("outputfiles/d2+/delay_%i.h5")
	title("$D_2^+$")
	if save:
		pylab.savefig("doc/fig/delay_scan_d2p.eps")
	
	#Plot("outputfiles/hd+/nodipole_delay_%i.h5")
	#title("$HD^+$ without static dipole moment")
	#if save:
	#	pylab.savefig("doc/fig/delay_scan_hdp_nodipole.eps")
	#
	##Plot the difference between HD+ with and without the static dipole term
	#figure(figsize=(size,size*3./4.))
	#t, c = GetScanDelayCorrelation(outputfile="outputfiles/hd+/delay_%i.h5", partitionCount=1)
	#t2, c2 = GetScanDelayCorrelation(outputfile="outputfiles/hd+/nodipole_delay_%i.h5", partitionCount=1)
	#plot(t, c - c2)
	#ax = axis()
	#ax[0] = 20
	#ax[1] = 100
	#axis(ax)
	#title("Difference between HD+ with and without\nstatic dipole moment")
	#xlabel("Pulse Delay")
	#ylabel("Proabability difference")
	#if save:
	#	pylab.savefig("doc/fig/delay_scan_nodipole_diff.eps")


	#restore previous interactive setting
	rcParams["interactive"] = interactive
	show()


#------------------------------------------------------------------------------	
#                Parse output files
#------------------------------------------------------------------------------	

def IterateScanNodes(outputfile, partitionCount):
	"""
	Iterate through all HDF files
		[outputfile % i for i in range(partitionCount)]

	For each file list through all root-level nodes that
	starts with "delay_", and yield that node along with the
	number behind the "delay_"

	This function is used to iterate through all outputfiles
	generated by SubmitScanDelay
	"""

	for i in range(partitionCount):
		filename = outputfile % i
		f = tables.openFile(filename, "r")
		try:
			for node in f.listNodes(f.root):
				name = node._v_name
				if name.startswith("delay_"):
					try:
						t = float(name[len("delay_"):])
						yield t, node
					except:
						print "Could not process %s" % name
		finally:
			f.close()



def GetScanDelayEnergyDistribution(**args):
	"""
	Uses IterateScanNodes to iterate through all outputfiles, and calculates
	the energy distribution of the last wavefunction at each delay time

	It returns three variables
	1) delay times
	2) energy values
	3) probability[delay, energy]

	"""
	molecule = args["molecule"]
	outputfile = args["outputfile"]
	partitionCount = args["partitionCount"]

	E1, V1, E2, V2 = LoadContinuumEigenstates(**args)

	recalculate = False
	if "recalculate" in args:
		recalculate = args["recalculate"]

	#To add up the energies we must interpolate the values from 
	#the E1 and E2 grids to a common E-grid
	dE = average(diff(E2))
	E = r_[-0.5:0:dE]

	projList = []
	timeList = []

	for t, node in IterateScanNodes(outputfile, partitionCount):
		if recalculate:
			psi = node.wavefunction[-1,:,:]
			proj1, proj2 = CalculateEnergyDistribution(psi, E, E1, V1, E2, V2) 
		else:
			proj1 = node.energyDistribution[-1,0,:]
			proj2 = node.energyDistribution[-1,1,:]

		projList.append([proj1, proj2])
		timeList.append(t)

	sortedIndex = argsort(timeList)
	time = array(timeList)[sortedIndex]
	proj= array(projList)[sortedIndex,:]

	return time, E, proj


def CalculateEnergyDistribution(psi, outputEnergies, E1, V1, E2, V2):
	"""
	Calculates the energy distribution of the array psi, by projecting 
	on to the basis function sets V1 and V2.
	V1 is the eigenstates for the binding potential
	V2 is the eigenstates for the unbinding potential

	the energy distribution is then interpolated (with cubic splines)
	over outputEnergies
	"""
	proj1 = dot(V1, psi[:,0])
	proj2 = dot(V2, psi[:,1])

	interp1 = spline.Interpolator(E1, abs(proj1)**2)
	interp2 = spline.Interpolator(E2, abs(proj2)**2)

	outDistrib1 = array([interp1.Evaluate(e) for e in outputEnergies])
	outDistrib2 = array([interp2.Evaluate(e) for e in outputEnergies])

	return outDistrib1, outDistrib2



def RepackDelayScan(**args):
	outputfile = args["outputfile"]
	partitionCount = args["partitionCount"]
	repackFile = args["repackFile"]
	
	print "Repacking correlation"
	time, proj = GetScanDelayCorrelation(**args)
	print "Repacking energy distribution"
	t, E, corr = GetScanDelayEnergyDistribution(**args)
	print "Repacking norm"
	t, norm = GetScanDelayNorm(**args)

	
	output = tables.openFile(repackFile, "w")
	try:
		SaveArray(output, "/", "pulse_delay", time)
		SaveArray(output, "/", "energy", E)

		SaveArray(output, "/", "final_correlation", proj)
		SaveArray(output, "/", "energy_distribution", corr)
		SaveArray(output, "/", "norm", norm)

	finally:
		output.close()

	
def GetScanDelayCorrelation(**args):
	outputfile = args["outputfile"]
	partitionCount = args["partitionCount"]

	projList = []
	timeList = []

	for t, node in IterateScanNodes(outputfile, partitionCount):
		proj = node.eigenstateProjection[-1,:]
		projList.append(proj)
		timeList.append(t)

	sortedIndex = argsort(timeList)
	time = array(timeList)[sortedIndex]
	proj= array(projList)[sortedIndex]

	return time, proj

def GetScanDelayNorm(**args):
	outputfile = args["outputfile"]
	partitionCount = args["partitionCount"]

	projList = []
	timeList = []

	for t, node in IterateScanNodes(outputfile, partitionCount):
		proj = node.norm[-1]
		projList.append(proj)
		timeList.append(t)

	sortedIndex = argsort(timeList)
	time = array(timeList)[sortedIndex]
	proj= array(projList)[sortedIndex]

	return time, proj


#------------------------------------------------------------------------------	
#                Submit scan delay jobs
#------------------------------------------------------------------------------	

#ipython1:
DefaultControllerHost = "localhost"
DefaultControllerPort = 61001

try:
	import ipython1.kernel.api as kernel
except:
	print "Could not load IPython1, fancy submitting wil be unavailable"

def GetStalloEngineCount():
	controllerHost = DefaultControllerHost
	controllerPort = DefaultControllerPort

	#Create connection to stallo
	rc = kernel.RemoteController((controllerHost, controllerPort))
	return rc.getIDs()


def SubmitDelayScanStallo(**args):
	delayList = args["delayList"]
	outputfile = args["outputfile"]
	molecule = args["molecule"]

	controllerHost = DefaultControllerHost
	controllerPort = DefaultControllerPort
	if "controllerHost" in args:
		controllerHost = args["controllerHost"]
	if "controllerPort" in args:
		controllerPort = args["controllerPort"]

	#Create connection to stallo
	rc = kernel.RemoteController((controllerHost, controllerPort))
	partitionCount = len(rc.getIDs())

	if partitionCount == 0:
		raise Exception("No engines connected to controller @ stallo.")

	rc.executeAll('import os')
	rc.executeAll('os.environ["PYPROP_SINGLEPROC"] = "1"')
	rc.runAll('example.py')
	rc.scatterAll("delayList", delayList)
	rc.scatterAll("partitionId", r_[:partitionCount])
	rc.pushAll(args=args)
	rc.executeAll('args["delayList"] = delayList')
	rc.executeAll('args["outputfile"] = args["outputfile"] % partitionId[0]')
	rc.executeAll('RunDelayScan(**args)')
	
	

def SubmitDelayScan(**args):
	delayList = args["delayList"]
	outputfile = args["outputfile"]
	molecule = args["molecule"]
	partitionCount = args["partitionCount"]

	partitionSize = int(ceil(len(delayList)/float(partitionCount)))

	plist = []
	
	for i in range(partitionCount):
		args["delayList"] = delayList[i*partitionSize:(i+1)*partitionSize]
		args["outputfile"] = outputfile % i

		executable = './run_delay_scan.py %s > /dev/null' % commands.mkarg(repr(args))  
		plist.append(os.popen(executable))

	while len(plist) > 0:
		for p in plist:
			try: 
				print p.next()
			except StopIteration:
				print p.close()
				plist.remove(p)
				break


#------------------------------------------------------------------------------	
#                Propagate scan delay
#------------------------------------------------------------------------------	

def RunDelayScan(**args):
	#Required parameters
	delayList = args["delayList"]
	outputfile = args["outputfile"]
	molecule = args["molecule"]

	print "USING OUTPUTFILE ", outputfile

	for delay in delayList:
		args["pulseDelay"] = delay*femtosec_to_au
		args["outputpath"] = "/delay_%i" % (delay)
		print "Propagating %s with pulse delay %ifs" % (molecule, delay)
		PropagateDelayScan(**args)

def PropagateDelayScan(**args):
	"""
	Propagates one run for the scan pulse delay experiment, and
	saves the result to disk.

	The following arguments are required
	molecule: The molecule to simulate "hd+" or "d2+" or "h2+"
	outputfile: The hdf5 file to save the results to (i.e. pulsedelay_30.h5)
	outputpath: The group inside outputfile where (i.e. "/delay_30fs")

	"""	
	args['config'] = "config.ini"
	args['imtime'] = False
	inputfile = GetInputFile(**args)
	outputfile = args["outputfile"]
	outputpath = args["outputpath"]

	conf = SetupConfig(**args)
	prop = SetupProblem(**args)

	f = tables.openFile(inputfile, "r")
	try:
		#Setup initial state
		prop.psi.GetData()[:,0] = f.root.initial_state[:]
		prop.psi.GetData()[:,1] = 0
		initPsi = prop.psi.Copy()

		#Load eigenstates
		eigenstates = conj(f.root.eigenstates[:])
		f.close()
	finally:
		f.close()
	del f

	if len(eigenstates.shape) != 2:
		raise Exception("Please implement for Rank!=2")
	eigenstateSize = len(eigenstates[0,:])

	boundE, boundV = LoadBoundEigenstates(**args)
	contE1, contV1, contE2, contV2 = LoadContinuumEigenstates(**args)

	r = prop.psi.GetRepresentation().GetLocalGrid(0)
	timeList = []
	initCorrList = []
	corrList = []
	normList = []
	psiTimeList = []
	timeList = []
	energyDistribution = []

	dE = average(diff(contE2))
	E = r_[-0.5:0:dE]

	pulseStart = conf.ElectronicCoupling.delay
	pulseDuration = conf.ElectronicCoupling.duration
	
	output = tables.openFile(outputfile, "a")
	try:
		RemoveNodeIfExists(output, outputpath, "wavefunction")
		atom = tables.ComplexAtom(16)
		shape = (0,) + prop.psi.GetData().shape
		psiList = output.createEArray(outputpath, "wavefunction", atom, shape, createparents=True)
		
		def checkpoint():
			timeList.append(prop.PropagatedTime)
			initCorrList.append(prop.psi.InnerProduct(initPsi))
			normList.append(prop.psi.GetNorm())
			psiTimeList.append(prop.PropagatedTime)
			psiList.append(prop.psi.GetData().reshape((1,) + prop.psi.GetData().shape))
			energyDistribution.append(array(CalculateEnergyDistribution(prop.psi.GetData(), E, contE1, contV1, contE2, contV2)))
			corrList.append(abs(dot(boundV, prop.psi.GetData()[:,0]))**2)

		#0) Store the initial packet
		checkpoint()

		#1) Propagate until the pulse starts
		prop.Duration = pulseStart - 2*pulseDuration
		for t in prop.Advance(minimum(20, prop.Duration)): 
			#checkpoint()
			pass
		
		#1a) Save the wavepacket before the pulse to see how much has flowed out
		checkpoint()	
		
		#2) Propagate until the end of the pulse
		prop.Duration = pulseStart + 2*pulseDuration
		index = 0
		for t in prop.Advance(True):
			#checkpoint()
			pass
		
		#2a) Save the wavepacket at the end 
		checkpoint()
		
		SaveArray(output, outputpath, "time", array(timeList))
		SaveArray(output, outputpath, "eigenstateProjection", array(corrList))
		SaveArray(output, outputpath, "initstateProjection", array(initCorrList))
		SaveArray(output, outputpath, "norm", array(normList))
		SaveArray(output, outputpath, "timeWavefunction", array(psiTimeList))
		SaveArray(output, outputpath, "energyDistribution", array(energyDistribution))
		SaveArray(output, "/", "energy", E)
		psiList.close()

	finally:
		output.close()

	return array(timeList), array(corrList)

