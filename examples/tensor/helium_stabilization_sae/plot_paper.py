#execfile("plot_paper_common.py")
#execfile("example.py")
from plot_paper_common import *
from example import *
from stabilization import *
from analysis import *


def PaperGetBaseEnergy(experiment):
	if experiment == "1s1s" or experiment == "1s1s_cycle10" or experiment == "1s1s_cycle20":
		return 2.903
	elif experiment == "1s2s":
		return 2.17
	elif experiment == "1s2s_1":
		return 2.14
	elif experiment == "1s2s_1_cycle10":
		return PaperGetBaseEnergy("1s2s_1")
	elif experiment == "1s2p_1":
		return 2.13
	elif experiment == "1s2p_3":
		return 2.13
	else:
		raise Exception("Unknown experiment %s" % experiment)


def PaperGetDpDeNormalizationFactor(experiment):
	if experiment == "1s1s":
	#	return 1.0 / 1.44999676268 * 0.00072561123476237374/5.0,
		return 1.0 / 1.5 * 0.00072561123476237374/5.0
	elif experiment == "1s1s_cycle20":
		return 1.0 / 1.5 * 0.00072561123476237374/5.0
	else:
		return 1.0


def PaperGetDpDeVmaxList(experiment):
	if experiment == "1s1s":
		return [2.24366662509, 942.434516461, 1213.43592354]
	elif experiment == "1s1s_cycle20":
		return [15, None, None]
	else:
		return [None, None, None]


def PaperGetDpDeSymmetrization(experiment):
	if experiment == "1s1s_cycle20":
		return "sym"
	else:
		return "nosym"


#------------------ Run Stabilization -------------------------

def PaperGetExperimentArgs(experiment, e0):
	"""
	Sets up two argument dicts for propagating a product of 
	two 1e systems. I.e. if experiment == "1s2p",
	the first argument dict corresponds to a 1s he+ system
	and the second argument dict corresponds to a 2p h system

	if experiment == "1s1s" two idential arg dicts are returned
	containing a 1s he2 (Z=1.7) model
	"""
	freq = 5.
	arg = {
		"frequency": freq,
		"amplitude": e0/freq,
		"config": "config_paper.ini",
		"experiment": experiment,
		"e0": e0,
		"initialN": 1,
		"initialL": 0,
		"outputCount": 10,
		}

	if experiment == "1s1s":
		arg["model"] = "he2"
		arg1 = arg2 = arg

	elif experiment == "1s1s_cycle20":
		arg["model"] = "he2"
		arg['pulseDuration'] = 2 * pi / freq * 20
		arg1 = arg2 = arg
		arg1 = dict(arg)
		arg2 = dict(arg)
		arg1["model"] = "he+"
		arg2["model"] = "he"

	elif experiment == "1s2s":
		arg1 = dict(arg)
		arg2 = dict(arg)
		arg1["model"] = "he+"
		arg2["model"] = "h"
		arg2["initialN"] = 2
		arg2["initialL"] = 0

	elif experiment == "1s2s_2":
		arg1 = dict(arg)
		arg2 = dict(arg)
		arg1["model"] = "he+"
		arg2["model"] = "he"
		arg2["initialN"] = 2
		arg2["initialL"] = 0

	elif experiment == "1s2p":
		arg1 = dict(arg)
		arg2 = dict(arg)
		arg1["model"] = "he+"
		arg2["model"] = "h"
		arg2["initialN"] = 2
		arg2["initialL"] = 1

	elif experiment == "1s2p_2":
		arg1 = dict(arg)
		arg2 = dict(arg)
		arg1["model"] = "he+"
		arg2["model"] = "he"
		arg2["initialN"] = 2
		arg2["initialL"] = 1
	

	else:
		raise Exception("Experiment %s not found" % experiment)

	return arg1, arg2


if not "ComputedProblems" in globals():
	ComputedProblems = {}
def PaperGetProblems(experiment, e0):
	global ComputedProblems
	key = "%s_%f" % (experiment, e0)
	if not key in ComputedProblems:
		#get arguments for this experiment
		arg1, arg2 = PaperGetExperimentArgs(experiment, e0)
		#print arg1

		#do stabilization runs for this experiment
		prop1 = RunStabilization(**arg1)
		if arg2 == arg1:
			prop2 = prop1
		else:
			prop2 = RunStabilization(**arg2)
		ComputedProblems[key] = (prop1, prop2)

	return ComputedProblems[key]

if not "AnalysisData" in globals():
	AnalysisData = {}
def GetAnalysisData(experiment):
	global AnalysisData
	key = "%s" % (experiment, )
	if not key in AnalysisData:
		#get arguments for this experiment
		arg1, arg2 = PaperGetExperimentArgs(experiment, 0)

		def getAnalysisData(**args):
			PrintOut("Preparing analysis data...")
			prop = SetupProblem(**args)
			S = SetupOverlapMatrix(prop)
			E, V = SetupRadialEigenstates(prop)
			return S, E, V

		AnalysisData[key] = (getAnalysisData(**arg1), getAnalysisData(**arg2))

	return AnalysisData[key]

#
# Supply continuum analysis data consistent with the two-electron Coulomb waves
# we are using (Z=2 for double ionization, bound+Z=1 for single ionization)
#
if not "AnalysisDataContinuum" in globals():
	AnalysisDataContinuum = {}
def GetAnalysisDataContinuum(experiment):
	global AnalysisDataContinuum
	key = "%s" % (experiment, )
	if not key in AnalysisDataContinuum:
		#get arguments for this experiment
		arg1, arg2 = PaperGetExperimentArgs(experiment, 0)

		#Set model2 to He+ (Z=2) and model1 to H (Z=1)
		arg1["model"] = "h"
		arg2["model"] = "he+"

		def getAnalysisData(**args):
			PrintOut("Preparing analysis data...")
			prop = SetupProblem(**args)
			S = SetupOverlapMatrix(prop)
			E, V = SetupRadialEigenstates(prop)
			return S, E, V

		AnalysisDataContinuum[key] = (getAnalysisData(**arg1), getAnalysisData(**arg2))

	return AnalysisDataContinuum[key]


def PaperGetDpDeDoubleOld(experiment, e0):
	prop1, prop2 = PaperGetProblems(experiment, e0)

	(S1, E1, V1), (S2, E2, V2) = GetAnalysisData(experiment)
	
	en1, dp1 = CalculateEnergyDistribution(prop1.psi, E1, V1, S1, 0.01, maxE=10)
	en2, dp2 = CalculateEnergyDistribution(prop2.psi, E2, V2, S2, 0.01, maxE=10)
	
	return en1, en2, outer(dp1,dp2)


def PaperGetDpDeDouble(experiment, e0):
	PrintOut("Calculating double ionization energy distribution...")

	#Get propagation data
	prop1, prop2 = PaperGetProblems(experiment, e0)

	#Get problems eigenstate data
	(S1, E1, V1), (S2, E2, V2) = GetAnalysisData(experiment)

	#Get continuum analysis data
	SC, DC = GetAnalysisDataContinuum(experiment)
	singleCont = {'S': SC[0], 'E': SC[1], 'V': SC[2]}
	doubleCont = {'S': DC[0], 'E': DC[1], 'V': DC[2]}

	#Remove bound states
	PrintOut("Removing bound state populations...")
	dummy = RemoveBoundDistribution(prop1.psi, E1, V1, S1)
	dummy = RemoveBoundDistribution(prop2.psi, E2, V2, S2)

	#Set up interpolation energy grid
	maxE = 14
	#dE = min(diff(sorted(E1[0])))
	#E = r_[0.01:maxE:dE]

	def getDpDeDoubleSymmetric():
		#Get one-electron energy distributions
		PrintOut("Calculating one-electron energy distributions")
		en1, dp1 = CalculateEnergyDistributionNoSumL(prop1.psi, doubleCont['E'], doubleCont['V'], doubleCont['S'], 0.01, maxE=maxE)
		en2, dp2 = CalculateEnergyDistributionNoSumL(prop2.psi, doubleCont['E'], doubleCont['V'], doubleCont['S'], 0.01, maxE=maxE)
		
		PrintOut("Calculating two-electron energy distribution")
		numL = prop1.psi.GetData().shape[0]
		dp = zeros((len(en1), len(en2)), dtype=double)
		for l1 in range(numL):
			for l2 in range(numL):
				A = outer(dp1[l1], dp2[l2])
				B = outer(dp2[l2], dp1[l1])
				#AA = ComplexBivariateInterp(en1[l1], en1[l2], A, E)
				#BB = ComplexBivariateInterp(en1[l2], en1[l1], B, E)
				dp += abs(A + B)**2

		return en1, en2, dp

	def getDpDeDouble():
		PrintOut("Calculating one-electron energy distributions")
		en1, dp1 = CalculateEnergyDistribution(prop1.psi, doubleCont['E'], doubleCont['V'], doubleCont['S'], 0.01, maxE=maxE)
		en2, dp2 = CalculateEnergyDistribution(prop2.psi, doubleCont['E'], doubleCont['V'], doubleCont['S'], 0.01, maxE=maxE)
		
		PrintOut("Calculating two-electron energy distribution")
		return en1, en2, outer(dp1, dp2)

	dpdeSym = PaperGetDpDeSymmetrization(experiment)
	if dpdeSym == "nosym":
		en1, en2, dp = getDpDeDouble()
	elif dpdeSym == "sym":
		en1, en2, dp = getDpDeDoubleSymmetric()
	else:
		raise Exception("Unknown symmetry type: %s" % dpdeSym)

	return en1, en2, dp


def PaperGetDpDeSingle(experiment, e0):
	PrintOut("Calculating single ionization energy distribution...")

	prop1, prop2 = PaperGetProblems(experiment, e0)
	(S1, E1, V1), (S2, E2, V2) = GetAnalysisDataContinuum(experiment)

	en, dp = CalculateEnergyDistribution(prop1.psi, E1, V1, S1, 0.005)
	
	return en, dp


def PaperGetDpDomegaDouble(experiment, e0):
	#Get propagation data
	prop1, prop2 = PaperGetProblems(experiment, e0)

	#Get problems eigenstate data
	(S1, E1, V1), (S2, E2, V2) = GetAnalysisData(experiment)

	#Get continuum analysis data
	SC, DC = GetAnalysisDataContinuum(experiment)
	singleCont = {'S': SC[0], 'E': SC[1], 'V': SC[2]}
	doubleCont = {'S': DC[0], 'E': DC[1], 'V': DC[2]}

	#Remove bound states
	PrintOut("Removing bound state populations...")
	dummy = RemoveBoundDistribution(prop1.psi, E1, V1, S1)
	dummy = RemoveBoundDistribution(prop2.psi, E2, V2, S2)

	#Set up interpolation energy grid
	maxE = 14
	#dE = min(diff(sorted(E1[0])))
	#E = r_[0.01:maxE:dE]

	E, theta, angDistr = CalculateAngularDistribution(prop1.psi, doubleCont['E'], doubleCont['V'], doubleCont['S'], interpMethod="polar-square")

	return E, theta, angDistr

	 

def GetIonizationProbabilityScan(experiment):
	e0List = r_[1:35:1]
	
	def getIonizationProbability(e0):
		prop1, prop2 = PaperGetProblems(experiment, e0)
		Ion1 = 1-prop1.BoundTotalList[-1]
		Ion2 = 1-prop2.BoundTotalList[-1]
		#print Ion1, Ion2
		single = Ion1*(1-Ion2) + Ion2*(1-Ion1)
		double = Ion1*Ion2
		return single, double

	singleList, doubleList = zip(*map(getIonizationProbability, e0List))
	return e0List, singleList, doubleList


def SaveIonizationResults(experiment):
	e0, single, double = GetIonizationProbabilityScan(experiment)
	folder = PaperGetFolder()
	f = tables.openFile(os.path.join(folder, "%s.h5" % experiment), "w")
	try:
		f.createArray(f.root, "Amplitude", array(e0))
		f.createArray(f.root, "SingleIonization", array(single))
		f.createArray(f.root, "DoubleIonization", array(double))

	finally:
		f.close()

	

#------------------ Run Stabilization -------------------------

#def PaperMakePlotDpDomega(e0, energy1, energy2=None, vmin=None, vmax=None):
#	if energy2 == None:
#		energy2 = energy1
#
#	#get data
#	if type(e0) == str:
#		filename = e0
#	else:
#		filename = "output/stabilization_freq5/stabilization_I_%i_kb20_dt_1e-02.h5" % e0
#	en, th, dp = GetDpDomegaDoubleFromFile(filename)
#	
#	#slice at energies
#	idx1 = argmin(abs(en-energy1))
#	idx2 = argmin(abs(en-energy2))
#	dpSlice = dp[:,:,idx1, idx2]
#
#	#interpolate
#	th2 = linspace(0,pi,512)
#	dp2 = scipy.interpolate.RectBivariateSpline(th, th, dpSlice)(th2, th2)
#
#	#load color map
#	cmap = LoadColormap(GradientFile, reverse=True)
#
#	#plot
#	fig = figure()
#
#	ax = gca()
#	ax.pcolorfast(th2/pi, th2/pi, dp2, cmap=cmap, vmin=vmin, vmax=vmax)
#	ax.set_xlabel("$\\theta_1$")
#	ax.set_ylabel("$\\theta_2$")
#	xticks([0,0.25,0.5,0.75,1], ("$0$", "$\pi/4$", "$\pi/2$", "$\pi\  3/4$", "$\pi$"))
#	yticks([0,0.25,0.5,0.75,1], ("$0$", "$\pi/4$", "$\pi/2$", "$\pi\  3/4$", "$\pi$"))
#	ax.set_position(Bbox(array([[0.25, 0.25], [0.95, 0.95]])))
#	draw()
#
#
#	return fig
#

def PaperMakePlotDpDomegaPolar(experiment, thCut, energy1, energy2=None, vmin=None, vmax=None, energyAverage=False, phiEvalType="avg"):
	if energy2 == None:
		energy2 = energy1

	#setup bounds
	rectBound = (.20, .20, .65, .65)
	singleWidth = .025
	singleSpacing = 0.005
	
	lineStyleList = ["-", "--", ":"]
	colorList = [UiB_Blue, UiB_Green, UiB_Red]
	e0List = [1, 10, 20]
	#e0List = range(1,21)
	#e0List = [1]

	#get photon energy interval
	limits = [0] + [ 5 * (i+0.5) - PaperGetBaseEnergy(experiment) for i in range(1,5)]
	totalEnergy = energy1 + energy2
	enLimLow = filter(lambda en: en<totalEnergy, limits)[-1]
	enLimHigh = filter(lambda en: en>totalEnergy, limits)[0]

	#create figure
	fig = figure()
	rectMain = (rectBound[0]+singleWidth, rectBound[1]+singleWidth, rectBound[2]-singleWidth, rectBound[3]-singleWidth)
	axMain = fig.add_axes(rectMain, polar=True, axisbelow=True)
	
	maxValDpDomega = 0
	for	e0 in e0List:
		#get data
		en, th, dp = PaperGetDpDomegaDouble(experiment, e0)

		#slice at energies and theta1
		idx1 = argmin(abs(en-energy1))
		idx2 = argmin(abs(en-energy2))
		#idx3 = argmin(abs(th - thCut))
		#dpSlice = sum(sum(dp, axis=3), axis=2)[idx3, :]
		dpSlice = dp[:, idx1]
	#	if energyAverage:
	#		print "Averaging over energy"
	#		#dpdomega_double = CalculatePartialAngularIonizationProbability(en, th, dp, enLimLow, enLimHigh)
	#		dpdomega_double = CalculateRadialPartialAngularIonizationProbability(en, th, dp, energy1, energy2, energyAvgRadius)
	#		dpSlice = dpdomega_double[:, idx3]
	#	else:
	#		dpSlice = dp[idx3, : ,idx1, idx2]

		#interpolate
		th2 = linspace(0,pi,512)
		dp2 = scipy.interpolate.UnivariateSpline(th, dpSlice, s=0)(th2)
	
		#get n-photon ionization probability, skip this e0 if too small
		curColor = colorList.pop(0)
		curStyle = lineStyleList.pop(0)
		#curColor = UiB_Blue
		#if e0 == 10:
		#	curColor = UiB_Green
		#if e0 == 20:
		#	curColor = UiB_Red
		#curStyle = "-"

		#normalize
		dp2Norm = sum(dp2 * sin(th2)) * diff(th2)[0]
		dp2 /= dp2Norm

		#update max val
		maxValDpDomega = max(max(dp2), maxValDpDomega)

		#plot
		axMain.plot(th2, dp2, color = curColor, linestyle = curStyle)
		axMain.plot(-th2, dp2, color = curColor, linestyle = curStyle)

	#fig.figurePatch.set_alpha(1.0)
	PaperUpdatePolarFigure(fig)
	axMain.set_position(GetOptimalAxesPosition(fig, axMain))
	axMain.set_xlim([0, maxValDpDomega])

	#Update r and theta grid lines/labels
	#axMain.axes.axesFrame.set_visible(False)
	rGridLines = linspace(0, maxValDpDomega, 5)[1:-1]
	#rGridLines = [maxValDpDomega / 1.618]
	rgrids(rGridLines, ["" for p in rGridLines])
	thetagrids(range(0,360,45), [r"%s$^\circ$" % t for t in range(0,360,45)])

	#put arrow indicating direction of other electron
	axMain.plot([0,0], [0, maxValDpDomega/3.0], "k-", linewidth=0.8)
	axMain.plot([0], [maxValDpDomega/3.0], "k>", markersize=3.0)

	draw()

	return fig


def PaperMakePlotDpDe(experiment, e0, vmax=None):
	"""

	"""

	#setup bounds
	rectBound = (.15, .15, .80, .80)
	singleWidth = .025
	singleSpacing = 0.005
	energyLim = (0,14.5)

	#get data
	dpdeFunc = PaperGetDpDeCalcFunc(experiment)
	energy_double1, energy_double2, dpde_double = dpdeFunc(experiment, e0)
	energy_single, dpde_single = PaperGetDpDeSingle(experiment, e0)

	#interpolate to get smoother plot
	energy_interp = linspace(energy_double1[0], energy_double1[-1], 512)
	interp = scipy.interpolate.RectBivariateSpline(energy_double1, energy_double2, dpde_double)
	dpde_double_interp = interp(energy_interp, energy_interp)
	
	fig = figure()
	
	if vmax == None:
		vmax = numpy.max(dpde_double)
	#print "vmax = %s" % (vmax,)

	#load color map
	cmap = LoadColormap(GradientFile, reverse=True)

	#plot double dpde
	rectMain = (rectBound[0]+singleWidth, rectBound[1]+singleWidth, rectBound[2]-singleWidth, rectBound[3]-singleWidth)
	axMain = fig.add_axes(rectMain)
	axMain.pcolorfast(energy_interp, energy_interp, dpde_double_interp, vmin=0, vmax=vmax, cmap=cmap)
	axMain.set_xticks([])
	axMain.set_yticks([])
	axMain.set_xlim(energyLim)
	axMain.set_ylim(energyLim)

	for curE in [(5*i - 2.9) for i in range(1,4)]:
	#for curE in [(5*i - 2.17) for i in range(1,4)]:
		lin = Line2D([0,curE,], [curE, 0], color=UiB_Black)
		axMain.add_artist(lin)

	#plot left single dpde
	rectLeft = (rectBound[0], rectBound[1]+singleWidth, singleWidth-singleSpacing, rectBound[3]-singleWidth)
	axLeft = fig.add_axes(rectLeft)
	axLeft.pcolorfast(array([0,1]), energy_single, array([dpde_single, dpde_single]).transpose(), vmin=0, vmax=vmax, cmap=cmap)
	axLeft.set_xticks([])
	axLeft.set_ylim(energyLim)
	setp(axLeft.get_yticklines(), "markersize", 2)
	ylabel("Energy (a.u.)", fontsize=10)


	#plot bottom single dpde
	rectBottom = (rectBound[0]+singleWidth, rectBound[1], rectBound[2]-singleWidth, singleWidth-singleSpacing)
	axBottom = fig.add_axes(rectBottom)
	axBottom.pcolorfast(energy_single, array([0,1]), array([dpde_single, dpde_single]), vmin=0, vmax=vmax, cmap=cmap)
	axBottom.set_yticks([])
	axBottom.set_xlim(energyLim)
	setp(axBottom.get_xticklines(), "markersize", 2)
	xlabel("Energy (a.u.)")
	draw()

	fig.figurePatch.set_alpha(1.0)
	PaperUpdateFigure(fig)
	RepositionDpDe(fig, axMain, axLeft, axBottom)

	return fig, axMain, axLeft, axBottom


def PaperMakePlotDpDeAlt(experiment, e0, normFactor = 1.0, vmax=None):
	"""

	"""

	#setup bounds
	rectBound = (.15, .15, .80, .80)
	singleWidth = .025
	singleSpacing = 0.005
	energyLim = (0,14.5)

	#get data
	energy_double1, energy_double2, dpde_double = PaperGetDpDeDouble(experiment, e0)

	#interpolate to get smoother plot
	energy_interp = linspace(energy_double1[0], energy_double1[-1], 512)
	interp = scipy.interpolate.RectBivariateSpline(energy_double1, energy_double2, dpde_double)
	dpde_double_interp = interp(energy_interp, energy_interp)

	#Normalize
	dpde_double_interp /= normFactor
	
	fig = figure()
	
	if vmax == None:
		vmax = numpy.max(dpde_double_interp)
	#vmax = numpy.max(dpde_double)
	#vmax -= vmax * 0.1
	print "vmax = %s" % (vmax,)

	#load color map
	cmap = LoadColormap(GradientFile, reverse=True)

	#plot double dpde
	rectMain = (rectBound[0], rectBound[1], rectBound[2], rectBound[3])
	axMain = fig.add_axes(rectMain)
	quadMeshMain = axMain.pcolorfast(energy_interp, energy_interp, dpde_double_interp, vmin=0, vmax=vmax, cmap=cmap)
	axMain.set_xlim(energyLim)
	axMain.set_ylim(energyLim)
	ylabel("Energy (a.u.)", fontsize=10)
	xlabel("Energy (a.u.)")

	for curE in [(5*i - 2.9) for i in range(1,4)]:
	#for curE in [(5*i - 2.17) for i in range(1,4)]:
		lin = Line2D([0,curE,], [curE, 0], color=UiB_Black)
		axMain.add_artist(lin)

	#add colorbar
	cbar = colorbar(quadMeshMain, ax=axMain, format="%3i")
	axColorbar = cbar.ax

	#update colorbar fonts
	#cbarFont = matplotlib.font_manager.FontProperties(size=5.0)
	#for ytl in axColorbar.get_yticklabels():
	#	ytl.set_fontproperties(cbarFont)

	fig.figurePatch.set_alpha(1.0)
	PaperUpdateFigure(fig)
	#RepositionDpDe(fig, axMain, axLeft, axBottom)

	draw()

	return fig, axMain


def RepositionDpDe(fig, axMain, axLeft, axBottom):
	rectBound = (.15, .15, .80, .80)
	singleWidth = .025
	singleSpacing = 0.005
	energyLim = (0,14.5)

	#reposition
	box = GetOptimalAxesPosition(fig, axMain, [axMain, axLeft, axBottom])
	#box = GetOptimalAxesPosition(fig, axMain, padding=0)
	axMain.set_position(box)

	boxLeft = Bbox([[box.xmin - (singleWidth), box.ymin],
	                [box.xmin - (singleSpacing), box.ymax]])
	axLeft.set_position(boxLeft)

	boxBottom = Bbox([[box.xmin, box.ymin - (singleWidth)],
	                 [box.xmax, box.ymin - (singleSpacing)]])
	axBottom.set_position(boxBottom)
	draw()

	return fig


	

#-------------------------------------------------------------------------------------

#
#def PaperMakePlotDpDomegaScan(doClose=True):
#	e0list = [1,15,30]
#	E1 = (5 - 2.9)/2
#	E2 = (2*5 - 2.9)/2
#
#	folder = PaperGetFolder()
#	
#
#	interactive = rcParams["interactive"]
#	rcParams["interactive"] = False
#	try:
#		for e0 in e0list:
#			PaperFigureSettings(FigWidth, FigWidth)
#			fig = PaperMakePlotDpDomega(e0, E1, E1)
#			fig.figurePatch.set_alpha(1.0)
#			PaperUpdateFigure(fig)
#			fig.savefig(os.path.join(folder, "dpdomega_e0_%i_1photon_equalenergy.eps" % (e0,)), dpi=300)
#			fig.savefig(os.path.join(folder, "dpdomega_e0_%i_1photon_equalenergy.pdf" % (e0,)), dpi=300)
#			if doClose: close(fig)
#		
#			PaperFigureSettings(FigWidth, FigWidth)
#			fig = PaperMakePlotDpDomega(e0, E2, E2)
#			fig.figurePatch.set_alpha(1.0)
#			PaperUpdateFigure(fig)
#			fig.savefig(os.path.join(folder, "dpdomega_e0_%i_2photon_equalenergy.eps" % (e0,)), dpi=300)
#			fig.savefig(os.path.join(folder, "dpdomega_e0_%i_2photon_equalenergy.pdf" % (e0,)), dpi=300)
#			if doClose: close(fig)
#	
#	finally:
#		rcParams["interactive"] = interactive
#


def PaperMakePlotDpDomegaPolarScan(experiment, doClose=True):
	e0list = [1,10,20]
	E1 = (5 - 2.9)/2
	E2 = (2*5 - 2.9)/2

	folder = PaperGetFolder()
	

	interactive = rcParams["interactive"]
	rcParams["interactive"] = False
	try:
		PaperFigureSettings(FigWidth, FigWidth)
		fig = PaperMakePlotDpDomegaPolar(experiment, 0, E1, E1)
		fig.figurePatch.set_alpha(1.0)
		PaperUpdateFigure(fig)
		fig.savefig(os.path.join(folder, "dpdomega_2photon_equalenergy.eps"), dpi=300)
		fig.savefig(os.path.join(folder, "dpdomega_2photon_equalenergy.pdf"), dpi=300)
		if doClose: close(fig)
	
		#PaperFigureSettings(FigWidth, FigWidth)
		#fig = PaperMakePlotDpDomega(e0, E2, E2)
		#fig.figurePatch.set_alpha(1.0)
		#PaperUpdateFigure(fig)
		#fig.savefig(os.path.join(folder, "dpdomega_e0_%i_2photon_equalenergy.eps" % (e0,)), dpi=300)
		#fig.savefig(os.path.join(folder, "dpdomega_e0_%i_2photon_equalenergy.pdf" % (e0,)), dpi=300)
		#if doClose: close(fig)
	
	finally:
		rcParams["interactive"] = interactive


def PaperMakePlotDpDeScan(experiment, e0list = [1,10,20]):
	E1 = (5 - 2.9)/2
	E2 = (2*5 - 2.9)/2

	folder = PaperGetFolder()
	#PaperFigureSettings(FigWidth, FigWidth)
	PaperFigureSettings(FigWidth*1.165, FigWidth)

	#Normalization and vmax (from helium_stabilization)
	vmaxList = PaperGetDpDeVmaxList(experiment)
	normFactor = PaperGetDpDeNormalizationFactor(experiment)
	#print "Normalization factor is: %s" % normFactor

	interactive = rcParams["interactive"]
	rcParams["interactive"] = False
	try:
		for i, (e0, vmax) in enumerate(zip(e0list, vmaxList)):
			#fig, axMain, ax1, ax2 = PaperMakePlotDpDe(experiment, e0, vmax=vmax)
			fig, axMain = PaperMakePlotDpDeAlt(experiment, e0, normFactor = normFactor, vmax = vmaxList[i])
			fig.savefig(os.path.join(folder, "%s_dpde_e0_%i.eps" % (experiment, e0,)), dpi=300)
			fig.savefig(os.path.join(folder, "%s_dpde_e0_%i.pdf" % (experiment, e0,)), dpi=300)
			close(fig)
	
	finally:
		rcParams["interactive"] = interactive


def PaperMakePlotPartialIonization(experiment):
	limits = [0] + [ 5 * (i+0.5) - PaperGetBaseEnergy(experiment) for i in range(1,4)]
	e0 = linspace(1,35,35)
	partial = CalculatePartialIonizationProbabilityScan(experiment, e0, limits)
	
	inter = isinteractive()
	ioff()
	try:
		PaperFigureSettings(FigWidthLarge, FigWidthLarge/1.33)
		fig = figure()
		ax = fig.gca()
		ax.plot(e0, sum(partial[:], axis=1), color=UiB_Blue, label="Total prob. ", linestyle="-", linewidth=2*GraphLineWidth)
		ax.plot(e0, partial[:,0], color=UiB_Green, label="2 photon", linestyle="--")
		ax.plot(e0, partial[:,1], color=UiB_Red, label="3 photon", linestyle="-.")
		#ax.plot(e0, partial[:,3], color=UiB_Blue, label="4 photon", linestyle=":")
		legend()
		ax.get_legend().legendPatch.set_visible(False)
		ax.set_xlim(0,35)
		ax.set_xlabel("Field Strength (a.u.)")
		ax.set_ylabel("Ionization Probability")
		ax.set_ylim(0,1)
		
		ax.set_position(Bbox(array([[0.21, 0.21], [0.92, 0.92]])))
		PaperUpdateFigure(fig)
	finally:
		interactive(inter)
	draw()

	folder = PaperGetFolder()
	savefig(os.path.join(folder, "%s_ionization_partial_probability.eps" % experiment), dpi=300)
	savefig(os.path.join(folder, "%s_ionization_partial_probability.pdf" % experiment), dpi=300)

def PaperMakePlots():
	"""
	Make all plots for paper
	"""
	PaperMakePlotDpDomegaScan()
	PaperMakePlotDpDeScan()
	PaperMakePlotIonization()
	PaperMakePlotPartialIonization()


def CalculatePartialIonizationProbability(energy_double, dpde_double, minE, maxE, doPlot=False):
	"""
	Calculates the double ionization probability for getting electrons with
	combined energy between minE and maxE (minE < E1 + E2 < maxE)

	dpde_double is the calculated differential probability at equidistant energies
	energy_double is the list of the corresponding energies in dpde_double
	"""

	E1, E2 = meshgrid(energy_double, energy_double)
	#flatten to make indices from find work
	dp = dpde_double.copy().reshape(dpde_double.size)
	#zero out energies outside the requested range
	dp[find(E1 + E2 < minE)] = 0
	dp[find(E1 + E2 >= maxE)] = 0
	#reshape back to original shape
	dp = dp.reshape(dpde_double.shape)

	#plot if requested
	if doPlot:
		pcolormesh(energy_double, energy_double, dp)
		title("minE = %f, maxE = %f" % (minE, maxE))

	#integrate to get partial ionization probability
	#partialProb = sum(triu(dp)) * diff(energy_double)[0]**2
	partialProb = sum(dp) * diff(energy_double)[0]**2

	return partialProb


def CalculatePartialIonizationProbabilityScan(experiment, e0List, limits):
	partialList = []
	for e0 in e0List:
		#get data
		energy_double1, energy_double2, dpde_double = PaperGetDpDeDouble(experiment, e0)

		#p1 = CalculatePartialIonizationProbability(energy_double1, dpde_double, limits[0], limits[1])
		p2 = CalculatePartialIonizationProbability(energy_double1, dpde_double, limits[1], limits[2])
		p3 = CalculatePartialIonizationProbability(energy_double1, dpde_double, limits[2], limits[3])
		p4 = CalculatePartialIonizationProbability(energy_double1, dpde_double, limits[3], limits[4])
		partialList.append([p2, p3])
	
	return array(partialList)
