import sys

class PiramSolver:
	"""
	Pyprop wrapper for pIRAM, a homegrown IRAM implementation. 
	There were some problems with calling P_ARPACK from C, and i could not
	figure out what was wrong, so I implemented it from scratch in C++.

	As a bonus, it is much easier to read than ARPACK, which due to the 
	reverse communication interface, is rather hard to read.

	On the down side, it does not converge as fast as ARPACK. There are some
	details regarding inflation I havent yet fully grasped.

	see core/krylov/piram for more details

	It works by using the matrix-vector product functionality of the Problem-object
	supplied in the constructor

	"""

	def __init__(self, prop):
		self.BaseProblem = prop
		self.Rank = prop.psi.GetRank()
		self.Silent = getattr(prop.Config.Propagation, "silent", False)

		#Create a copy of the wavefunction to calculate H|psi>
		self.TempPsi = prop.psi.CopyDeep()

		#Set up pIRAM Solver
		self.Solver = CreateInstanceRank("core.krylov_PiramSolver", self.Rank)

		configSection = prop.Config.Arpack
		configSection.Apply(self.Solver)

		useInverseIterations = False
		if hasattr(configSection, "inverse_iterations"):
			useInverseIterations = configSection.inverse_iterations

		matrixSize = prop.psi.GetData().size
		basisSize = configSection.krylov_basis_size
		memoryUsage = self.Solver.EstimateMemoryUsage(matrixSize, basisSize)
		if ProcId == 0:
			print "Approximate pIRAM memory usage = %.2fMB" % memoryUsage
		self.Solver.Setup(prop.psi)

		self.Debug = False
		if hasattr(configSection, "krylov_debug"):
			if configSection.krylov_debug == True:	
				self.Debug = True

		self.CounterOn = False
		if hasattr(configSection, "counter_on"):
			if configSection.counter_on == True:
				self.CounterOn = True

		eigenvalueCount = configSection.krylov_eigenvalue_count
		maxIterations = configSection.krylov_max_iteration_count
		self.TotalMaxIterations = (basisSize - eigenvalueCount) * maxIterations
				
		#Check for user-defined matrix-vector product
		self.ApplyMatrix = self.BaseProblem.Propagator.MultiplyHamiltonian
		if hasattr(configSection, "matrix_vector_func"):
			if configSection.matrix_vector_func:
				PrintOut("  Using custom matrix-vector product")
				self.ApplyMatrix = configSection.matrix_vector_func
		else:
			if useInverseIterations:
				raise Exception("Inverse Iterations must be used together with a userdefined matrix_vector_func")

	def Solve(self):
		psi = self.BaseProblem.psi;
		tempPsi = self.TempPsi

		self.Count = 0

		#Run the Arnoldi iterations
		self.Solver.Solve(self.__MatVecCallback, psi, tempPsi, False)

	def __MatVecCallback(self, psi, tempPsi):
		#self.BaseProblem.Propagator.MultiplyHamiltonianBalancedOverlap(tempPsi, 0, 0)
		#self.BaseProblem.Propagator.MultiplyHamiltonian(psi, tempPsi, 0, 0)
		self.ApplyMatrix(psi, tempPsi, 0, 0)

		self.Count += 1
		if self.Debug and ProcId == 0:
			if self.Count % 100 == 0:
				print ""
				print "Count = ", self.Count
				print "EV = ", real(self.Solver.GetEigenvalues())
				print "Error = ", self.Solver.GetErrorEstimates()
				print "Convergence = ", self.Solver.GetConvergenceEstimates()

		if (not self.Silent) and self.CounterOn and ProcId == 0:

			if self.Count == 1:
				infoStr = "Progress:   0 %"
				sys.stdout.write(infoStr)
				sys.stdout.flush()
		
			if (self.Count * 100) % self.TotalMaxIterations == 0:
				backStr = "\b" * 30
				
				convergenceCriteria = self.Solver.GetConvergenceEstimates()
				total = len(convergenceCriteria)
				converged = len(where(convergenceCriteria<0)[0])

				infoStr =  "Progress: %3i %s (%i/%i)" % ((self.Count * 100)/ self.TotalMaxIterations, "%", converged, total)
				sys.stdout.write(backStr + infoStr)
				sys.stdout.flush()


	def GetEigenvalues(self):
		"""
		Returns the real part of all the converged eigenvalues from pIRAM
	    """
		return self.Solver.GetEigenvalues().real.copy()

	def GetEigenvector(self, index):
		"""
		Returns an eigenvector as a 1d numpy array.
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
		shape = psi.GetData().shape
		psi.GetData()[:] = numpy.reshape(self.GetEigenvector(eigenvectorIndex), shape)
		if normalize:
			psi.Normalize()

