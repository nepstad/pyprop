
class PamPropagator(PropagatorBase):
	__Base = PropagatorBase
	
	def __init__(self, psi):
		self.__Base.__init__(self, psi)
		self.Rank = psi.GetRank()
		
		self.PampWrapper = CreateInstanceRank("core.krylov_PampWrapper", self.Rank)

	def ApplyConfig(self, config):
		self.__Base.ApplyConfig(self, config)

		#Set up the base propagator (which will perform matrix vector multiplications)
		propagatorType = config.Propagation.base_propagator
		self.BasePropagator = propagatorType(self.psi)
		config.Apply(self.BasePropagator)
		#Set up the expokit propagator
		config.Apply(self.PampWrapper)

	def ApplyConfigSection(self, configSection): 
		self.__Base.ApplyConfigSection(self, configSection)

		#Set up base propagator
		configSection.Apply(self.BasePropagator)
		#Set up the expokit propagator
		configSection.Apply(self.PampWrapper)
	
	def SetupStep(self, dt):
		self.BasePropagator.SetupStep(dt)
		self.PampWrapper.Setup(self.psi);
		#We need an additional wavefunction to perform matrix-vector muls
		self.TempPsi = self.psi.CopyDeep()

		self.PsiDistrib = self.psi.GetRepresentation().GetDistributedModel()
		self.TempDistrib = self.TempPsi.GetRepresentation().GetDistributedModel()

	def MultiplyHamiltonian(self, destPsi, t, dt):
		self.BasePropagator.MultiplyHamiltonian(destPsi, t, dt)

	def AdvanceStep(self, t, dt):
		repr = self.psi.GetRepresentation()
		repr.MultiplySqrtOverlap(False, self.psi)
		self.PampWrapper.AdvanceStep(self.MatVecCallback, self.psi, self.TempPsi, dt, t, False)
		repr.SolveSqrtOverlap(False, self.psi)
		#self.PampWrapper.AdvanceStep(self.MatVecCallback, self.psi, self.TempPsi, dt, t, True)

	def MatVecCallback(self, psi, tempPsi, dt, t):
		#assert psi == self.psi
		#assert tempPsi == self.TempPsi
		
		#inN = psi.GetNorm()
	
		self.psi.GetRepresentation().SetDistributedModel(self.PsiDistrib)
		tempPsi.GetRepresentation().SetDistributedModel(self.TempDistrib)

		#This should be implemented on propagators but its not.
		#self.BasePropagator.MultiplyHamiltonianBalancedOverlap(tempPsi, t, dt)

		#This only works on orthogonal representations (Not BSplines)
		self.BasePropagator.MultiplyHamiltonian(tempPsi, t, dt)
		repr = tempPsi.GetRepresentation()
		repr.SolveOverlap(tempPsi)


		#outN = self.TempPsi.GetNorm()
		#if outN < 0.001:
		#	pylab.plot(abs(psi.GetData())**2)
		#	pylab.plot(abs(tempPsi.GetData())**2)
		#	print "inN = ", inN
		#	print "outN = ", outN
		#	assert False
	


