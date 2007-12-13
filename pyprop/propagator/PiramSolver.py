
class PiramSolver:
	"""
	Pyprop wrapper for pIRAM, a homegrown IRAM implementation. 
	There were some problems with calling P_ARPACK from C, and i could not
	figure out what was wrong, so I implemented it from scratch in C++.

	see core/krylov/piram for more details

	It works by using the matrix-vector product functionality of the Propagator

	"""

	def __init__(self, prop):
		self.BaseProblem = prop
		self.Rank = prop.psi.GetRank()

		#Create a copy of the wavefunction to calculate H|psi>
		self.TempPsi = prop.psi.CopyDeep()

		#Set up pIRAM Solver
		self.Solver = CreateInstanceRank("core.krylov_PiramSolver", self.Rank)

		configSection = prop.Config.Arpack
		configSection.Apply(self.Solver)
		self.Solver.Setup(prop.psi)

		self.Debug = False
		if hasattr(configSection, "krylov_debug"):
			if configSection.krylov_debug == True:	
				self.Debug = True
				

	def Solve(self):
		psi = self.BaseProblem.psi;
		tempPsi = self.TempPsi

		self.Count = 0

		#Run the Arnoldi iterations
		self.Solver.Solve(self.__MatVecCallback, psi, tempPsi)

	def __MatVecCallback(self, psi, tempPsi):
		self.BaseProblem.Propagator.MultiplyHamiltonian(tempPsi, 0, 0)

		self.Count += 1
		if self.Debug and ProcId == 0:
			if self.Count % 100 == 0:
				print "Count = ", self.Count
				print "EV = ", self.Solver.GetEigenvalues()


	def GetEigenvalues(self):
		"""
		Returns the real part of all the converged eigenvalues from pIRAM
	    """
		return self.Solver.GetEigenvalues().real

	def GetEigenvector(self, index):
		"""
		Returns an eigenvector as an 1d numpy array.
		The eigenvectors is normalized in the vector 2-norm, and can therefore not be
		expected to be normalized in the grid norm. Assign it to a wavefunction and call 
		psi.Normalize() to get a normalized eigenstate:

		eigenvectorIndex = 0
		shape = psi.GetData().shape
		psi.GetData()[:] = numpy.reshape(solver.GetEigenvector(eigenvectorIndex)
		psi.Normalize()
		"""
		return self.Solver.GetEigenvector(index)

	def SetEigenvector(self, psi, eigenvectorIndex, normalize=True):
		"""
		Sets psi to the eigenvector specified by eigenvetorIndex
		if normalize == True, psi will be normalized
		"""
		eigenvectors = self.GetEigenvectors()
		shape = psi.GetData().shape
		psi.GetData()[:] = numpy.reshape(eigenvectors[eigenvectorIndex, :], shape)
		if normalize:
			psi.Normalize()

