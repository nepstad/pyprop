
#----------------------------------------------------------------------------------------------------
# Cartesian FFT Evaluator
#----------------------------------------------------------------------------------------------------
class CartesianPropagator(PropagatorBase):
	FFT_FORWARD = -1
	FFT_BACKWARD = 1
	
	def __init__(self, psi):
		PropagatorBase.__init__(self, psi)

		rank = psi.GetRank()
		self.FFTTransform = CreateInstanceRank("core.CartesianFourierTransform", rank)

		self.SplittingOrder = 2
		self.RepresentationMapping = dict()

	def ApplyConfig(self, config): 
		PropagatorBase.ApplyConfig(self, config)
		
	def ApplyConfigSection(self, configSection): 
		PropagatorBase.ApplyConfigSection(self, configSection)
		self.Mass = 1.0
		if hasattr(configSection, 'mass'):
			self.Mass = configSection.mass

	def SetupStep(self, dt):
		#representation mappings		
		startRepr = self.psi.GetRepresentation()
		fftRepr = self.FFTTransform.CreateFourierRepresentation(startRepr)
		self.RepresentationMapping[startRepr] = fftRepr
		self.RepresentationMapping[fftRepr] = startRepr

		# set up potential
		self.SetupPotential(dt/2.)

		self.SetupTranspose()
		
		# set up kinetic energy
		self.TransformForward()
		self.SetupKineticPotential(dt)
		self.TransformInverse()

	def AdvanceStep(self, t, dt):
		self.ApplyPotential(t, dt/2.)
		self.AdvanceKineticEnergy(t, dt)
		self.ApplyPotential(t, dt/2.)

	def TransformForward(self):
		# transform into fourier space
		if IsSingleProc():
			self.FFTTransform.ForwardTransform(self.psi)
		else:
			for rank in range(1, self.psi.GetRank()):
				self.TransformRank(rank, self.FFT_FORWARD)
			self.Transpose(1)
			self.TransformRank(0, self.FFT_FORWARD)

		self.ChangeRepresentation()

	def TransformInverse(self):
		# transform back into real space
		if IsSingleProc():
			self.FFTTransform.InverseTransform(self.psi)
		else:
			self.TransformRank(0, self.FFT_BACKWARD)
			self.Transpose(2)
			for rank in range(1, self.psi.GetRank()):
				self.TransformRank(rank, self.FFT_BACKWARD)
			self.TransformNormalize()
		self.ChangeRepresentation()


	def AdvanceKineticEnergy(self, t, dt):
		# transform into fourier space
		self.TransformForward()
		
		# apply kinetic energy potential
		self.KineticPotential.AdvanceStep(t, dt) 
		
		# transform back into real space
		self.TransformInverse()

	def SetupKineticPotential(self, dt):
		#create config
		class staticEnergyConf(Section):
			def __init__(self, type, classname):
				self.type = type
				self.classname = classname
		conf = staticEnergyConf(PotentialType.Static, "CartesianKineticEnergyPotential")
		conf.mass = self.Mass

		#create potential 
		pot = CreatePotentialFromSection(conf, "KineticEnergy", self.psi)
		pot.SetupStep(dt)
		self.KineticPotential = pot
		
	def IsDistributedRank(self, rank):
		return self.psi.GetRepresentation().GetDistributedModel().IsDistributedRank(rank)
		
	#Transpose
	def SetupTranspose(self):
		#get transpose
		distrModel = self.psi.GetRepresentation().GetDistributedModel()
		if not distrModel.IsSingleProc():
			self.Distribution1 = distrModel.GetDistribution().copy()
			if len(self.Distribution1) > 1: 
				raise "Does not support more than 1D proc grid"
			transpose = distrModel.GetTranspose()
			#Setup shape	
			fullShape = self.psi.GetRepresentation().GetFullShape()
			self.Distribution2 = array([1])
			distribShape = transpose.CreateDistributedShape(fullShape, self.Distribution2)
			#allocate wavefunction
			self.TransposeBuffer1 = self.psi.GetActiveBufferName()
			self.TransposeBuffer2 = self.psi.AllocateData(distribShape)

	def Transpose(self, stage):
		distrModel = self.psi.GetRepresentation().GetDistributedModel()
		if not distrModel.IsSingleProc():
			if stage == 1:
				distrModel.ChangeDistribution(self.psi, self.Distribution2, self.TransposeBuffer2)
			elif stage == 2:
				distrModel.ChangeDistribution(self.psi, self.Distribution1, self.TransposeBuffer1)
			else:
				raise "Invalid stage %i" % stage

		
	def TransformRepresentation(self):
		self.psi.GetRepresentation().GetDistributedModel().ChangeRepresentation(self.psi)

	def TransformA(self, direction):
		rank = self.psi.GetRepresentation().GetDistributedModel().GetDistributedRank(self.psi)
		self.FFTTransform.TransformExceptDistributedRank(self.psi, direction)
		return rank
		
	def TransformB(self, rank, direction):
		self.FFTTransform.TransformRank(self.psi, rank, direction)

	#TransformB is not a very nice name, use this instead...
	def TransformRank(self, rank, direction):
		self.TransformB(rank, direction)
		
	def TransformNormalize(self):
		self.FFTTransform.Renormalize(self.psi)
		
	def ChangeRepresentation(self, direction=1):
		oldRepr = self.psi.GetRepresentation()

		#forward change of representation
		if direction == 1:
			if not self.RepresentationMapping.has_key(oldRepr):
				raise "Unknown representation ", oldRepr
				
			newRepr = self.RepresentationMapping[oldRepr]
			self.psi.SetRepresentation(newRepr)
		
		#Reverse change of representation
		if direction == -1:
			for key, value in self.RepresentationMapping.items():
				if value == oldRepr:
					self.psi.SetRepresentation(key)
					return
		
			raise "Unknown representation", oldRepr
