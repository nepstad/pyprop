#include <core/wavefunction.h>
#include <core/potential/dynamicpotentialevaluator.h>

#include <core/transform/bspline/bspline.h>
#include <core/utility/blitztricks.h>
#include <core/utility/blitzblas.h>

#include <core/transform/reducedspherical/reducedsphericaltools.h>

using namespace blitz;

template<int Rank>
cplx VectorDotProduct(Wavefunction<Rank> &psi1, Wavefunction<Rank> &psi2)
{
	return VectorInnerProduct(psi1.GetData(), psi2.GetData());
}

template<class TBase, int Rank>
void RepresentPotentialInBasisBSpline( BSpline::BSpline::Ptr bsplineObject, Array<TBase, Rank> source, Array<TBase, Rank> dest, Array<int, 2> indexPair, std::string storageId, int rank, int differentiation )
{
	typedef Array<TBase, 3> Array3D;
	typedef Array<TBase, 1> Array1D;
	Array3D source3d = MapToRank3(source, rank, 1);
	Array3D dest3d = MapToRank3(dest, rank, 1);

	int preCount = source3d.extent(0);
	int postCount = source3d.extent(2);
	int pairCount = indexPair.extent(0);

	bool isHermitian = storageId == "Herm";
	double scaling = 1;

	for (int preIndex=0; preIndex<preCount; preIndex++)
	{
		for (int pairIndex=0; pairIndex<pairCount; pairIndex++)
		{
			int rowIndex = indexPair(pairIndex, 0);
			int colIndex = indexPair(pairIndex, 1);
			if (isHermitian && rowIndex == colIndex)
			{
				scaling = 0.5;
			}
			else
			{
				scaling = 1.0;
			}

			for (int postIndex=0; postIndex<postCount; postIndex++)
			{
				Array1D sourceSlice = source3d(preIndex, Range::all(), postIndex);
				dest3d(preIndex, pairIndex, postIndex) = scaling * bsplineObject->BSplineGlobalOverlapIntegral(sourceSlice, differentiation, rowIndex, colIndex);
			}
		}
	}
}

typedef ReducedSpherical::ReducedSphericalTools::Ptr ReducedSphericalToolsPtr;

template<class TBase, int Rank>
void RepresentPotentialInBasisReducedSphericalHarmonic( ReducedSphericalToolsPtr obj, Array<TBase, Rank> source, Array<TBase, Rank> dest, Array<int, 2> indexPair, std::string storageId, int rank, int differentiation )
{
	typedef Array<TBase, 3> Array3D;
	typedef Array<TBase, 1> Array1D;
	Array3D source3d = MapToRank3(source, rank, 1);
	Array3D dest3d = MapToRank3(dest, rank, 1);

	int preCount = source3d.extent(0);
	int thetaCount = source3d.extent(1);
	int postCount = source3d.extent(2);
	int pairCount = indexPair.extent(0);

	
	Array<double, 2> leftAssocLegendre = obj->GetAssociatedLegendrePolynomial();
	Array<double, 2> rightAssocLegendre;
	if (differentiation == 0)
	{
		rightAssocLegendre.reference(obj->GetAssociatedLegendrePolynomial());
	}
	else if (differentiation == 1)
	{
		rightAssocLegendre.reference(obj->GetAssociatedLegendrePolynomialDerivative());
	}
	else 
	{
		throw std::runtime_error("Reduced spherical harmonics does not support higher derivatives than 1");
	}
	Array<double, 1> weights = obj->GetWeights();
	
	dest3d = 0;
	bool isHermitian = storageId == "Herm";
	double scaling = 1;

	for (int preIndex=0; preIndex<preCount; preIndex++)
	{
		for (int pairIndex=0; pairIndex<pairCount; pairIndex++)
		{
			int rowIndex = indexPair(pairIndex, 0);
			int colIndex = indexPair(pairIndex, 1);
			if (isHermitian && rowIndex == colIndex)
			{
				scaling = 0.5;
			}
			else
			{
				scaling = 1.0;
			}

			for (int thetaIndex=0; thetaIndex<thetaCount; thetaIndex++)
			{
				double leftLegendre = leftAssocLegendre(thetaIndex, rowIndex);
				double rightLegendre = rightAssocLegendre(thetaIndex, colIndex);
				double weight = weights(thetaIndex);
		
				for (int postIndex=0; postIndex<postCount; postIndex++)
				{
					dest3d(preIndex, pairIndex, postIndex) += leftLegendre * source3d(preIndex, thetaIndex, postIndex) * rightLegendre * weight;
				}
			}
		}
	}
}

template<class TBase, int Rank>
void RepresentPotentialInBasisFiniteDifference( Array<TBase, 2> differenceMatrixBandedBlas, Array<TBase, Rank> source, Array<TBase, Rank> dest, Array<int, 2> indexPair, int rank )
{
	typedef Array<TBase, 3> Array3D;
	typedef Array<TBase, 1> Array1D;
	Array3D source3d = MapToRank3(source, rank, 1);
	Array3D dest3d = MapToRank3(dest, rank, 1);

	int preCount = source3d.extent(0);
	int postCount = source3d.extent(2);
	int pairCount = indexPair.extent(0);

	int k = (differenceMatrixBandedBlas.extent(1) - 1) / 2;

	dest3d = 0;
	for (int preIndex=0; preIndex<preCount; preIndex++)
	{
		for (int pairIndex=0; pairIndex<pairCount; pairIndex++)
		{
			int rowIndex = indexPair(pairIndex, 0);
			int colIndex = indexPair(pairIndex, 1);

			if (rowIndex == -1) continue;
			if (colIndex == -1) continue;

			int blasJ = colIndex;
			int blasI = k + rowIndex - colIndex;
			cplx diffCoeff = 0;
			if (0 <= blasI && blasI < differenceMatrixBandedBlas.extent(1))
			{
				diffCoeff = differenceMatrixBandedBlas(blasJ, blasI);
			}

			for (int postIndex=0; postIndex<postCount; postIndex++)
			{
				dest3d(preIndex, pairIndex, postIndex) = diffCoeff * source3d(preIndex, colIndex, postIndex);
			}
		}
	}
}




template<class TBase>
void MultiplyTensorPotential_1(blitz::Array<TBase, 1> potentialData, double scaling, blitz::Array<int, 2> pair0, blitz::Array<cplx, 1> source, blitz::Array<cplx, 1> dest, int algo)
{
	for (int i=0; i<potentialData.extent(0); i++)
	{
		int row = pair0(i, 0);
		int col = pair0(i, 1);
		dest(row) += potentialData(i) * scaling * source(col);
	}
}

template<class TBase>
void MultiplyTensorPotential_2(blitz::Array<TBase, 2> potentialData, double scaling, blitz::Array<int, 2> pair0, blitz::Array<int, 2> pair1, blitz::Array<cplx, 2> source, blitz::Array<cplx, 2> dest, int algo)
{
	if (algo == 0)
	{
		for (int i=0; i<potentialData.extent(0); i++)
		{
			int row0 = pair0(i, 0);
			int col0 = pair0(i, 1);
			for (int j=0; j<potentialData.extent(1); j++)
			{
				int row1 = pair1(j, 0);
				int col1 = pair1(j, 1);
		
				dest(row0, row1) += potentialData(i, j) * scaling * source(col0, col1);
			}
		}
	}

	if (algo == 1)
	{
		int k = 8;
		
		for (int i=0; i<potentialData.extent(0); i++)
		{
			int row0 = pair0(i, 0);
			int col0 = pair0(i, 1);
		
			int N1 = source.extent(1);

			cplx* __restrict__ potentialPtr = &potentialData(i, 0);
			cplx* __restrict__ destPtr = &dest(row0, 0);
			for (int row1=0; row1<N1; row1++)
			{
				int startCol1 = std::max(0, row1-k+1);
				int endCol1 = std::min(N1, row1+k);
				cplx* __restrict__ sourcePtr = &source(col0, startCol1);
				for (int col1=startCol1; col1<endCol1; col1++)
				{
					(*destPtr) += (*potentialPtr++) * scaling * (*sourcePtr++);
				}
				destPtr++;
			}
		}
	}

	if (algo == 2)
	{
		int k = 8;
		
		for (int i=0; i<potentialData.extent(0); i++)
		{
			int row0 = pair0(i, 0);
			int col0 = pair0(i, 1);
		
			int N1 = source.extent(1);

			cplx* __restrict__ potentialPtr = &potentialData(i, 0);
			cplx* __restrict__ destPtr = &dest(row0, 0);
			
			cplx* __restrict__ sourceStartPtr = &source(col0, 0);
			for (int row1=0; row1<k; row1++)
			{
				int startCol1 = 0;
				int endCol1 = row1+k;
				//cout << "Start -> Stop (0)= " << startCol1 << " -> " << endCol1 << endl;
				cplx* __restrict__ sourcePtr = sourceStartPtr;
				for (int col1=startCol1; col1<endCol1; col1++)
				{
					(*destPtr) += (*potentialPtr++) * scaling * (*sourcePtr++);
				}
				destPtr++;
			}
			for (int row1=k; row1<N1-k; row1++)
			{
				int startCol1 = row1-k+1;
				int endCol1 = row1+k;
				//cout << "Start -> Stop (1)= " << startCol1 << " -> " << endCol1 << endl;
				cplx* __restrict__ sourcePtr = sourceStartPtr;
				sourceStartPtr++;
				for (int col1=startCol1; col1<endCol1; col1++)
				{
					(*destPtr) += (*potentialPtr++) * scaling * (*sourcePtr++);
				}
				destPtr++;
			}
			for (int row1=N1-k; row1<N1; row1++)
			{
				int startCol1 = row1-k+1;
				int endCol1 = N1;
				//cout << "Start -> Stop (2)= " << startCol1 << " -> " << endCol1 << endl;
				cplx* __restrict__ sourcePtr = sourceStartPtr;
				sourceStartPtr++;
				for (int col1=startCol1; col1<endCol1; col1++)
				{
					(*destPtr) += (*potentialPtr++) * scaling * (*sourcePtr++);
				}
				destPtr++;
			}
			//exit(-1);
		}
	}

/*
	if (algo == 3)
	{
		int k = 8;
		
		for (int i=0; i<potentialData.extent(0); i++)
		{
			int row0 = pair0(i, 0);
			int col0 = pair0(i, 1);
		
			int N1 = source.extent(1);

			cplx* __restrict__ potentialPtr = &potentialData(i, 0);
			cplx* __restrict__ destPtr = &dest(row0, 0);
			for (int band1=-k+1; band1<k; band1++)
			{
				int start1 = 0;
				int end1 = N1;
				if (band1 < 0)
				{
					start1 = -band1;
				}
				else
				{
					end1 = N1 - band1;
				}

				int j = band1+k-1;
				for (int index1=start1; index1<end1; index1++)
				{
					int col1 = index1+band1+k;
					int row1 = index1;
					if (row1 != pair1(j, 0) || col1 != pair1(j, 1))
					{
						cout << "Error (" << row1 << ", " << col1 << ") != (" << pair1(j, 0) << ", " <<  pair1(j, 1) << ")" << endl; 
					}
					dest(row0, row1) += potentialData(i, j) * source(col0, col1);
					j += 2*k - 1;
				}
			}
			exit(-1);
		}
	}
*/
}



template<int Rank>
class KineticEnergyPotential : public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	//Potential parameters
	double mass;

	/*
	 * Called once with the corresponding config section
	 * from the configuration file. Do all one time set up routines
	 * here.
	 */
	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("mass", mass);
	}

	/*
	 * Called for every grid point at every time step. 
	 */
	inline double GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		return - 1. / (2. * mass);
	}

};


template<int Rank>
class DipoleLaserPotential : public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	//Potential parameters
	int angularRank;
	int radialRank;
	double Charge;

	/*
	 * Called once with the corresponding config section
	 * from the configuration file. Do all one time set up routines
	 * here.
	 */
	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("angular_rank", angularRank);
		config.Get("radial_rank", radialRank);
		config.Get("charge", Charge);
	}

	/*
	 * Called for every grid point at every time step. 
	 */
	inline double GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		double theta = pos(angularRank);
		double r = pos(radialRank);
		return -Charge * r * cos(theta);
	}
};

template<int Rank>
class DipoleLaserPotentialVelocityRadialDerivative : public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	//Potential parameters
	int angularRank;
	int radialRank;
	double Charge;

	/*
	 * Called once with the corresponding config section
	 * from the configuration file. Do all one time set up routines
	 * here.
	 */
	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("angular_rank", angularRank);
		config.Get("radial_rank", radialRank);
		config.Get("charge", Charge);
	}

	/*
	 * Called for every grid point at every time step. 
	 */
	inline cplx GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		double theta = pos(angularRank);
		return Charge * cplx(0.,1.)*cos(theta);
	}
};

template<int Rank>
class DipoleLaserPotentialVelocityAngularDerivative : public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	//Potential parameters
	int angularRank;
	int radialRank;
	double Charge;

	/*
	 * Called once with the corresponding config section
	 * from the configuration file. Do all one time set up routines
	 * here.
	 */
	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("angular_rank", angularRank);
		config.Get("radial_rank", radialRank);
		config.Get("charge", Charge);
	}

	/*
	 * Called for every grid point at every time step. 
	 */
	inline cplx GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		double r = pos(radialRank);
		//double theta = pos(angularRank);
		//return -cplx(0.,1.)*sin(theta) / r;
		return -Charge * cplx(0.,1.) / r;
	}
};

template<int Rank>
class DipoleLaserPotentialVelocity: public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	//Potential parameters
	int angularRank;
	int radialRank;
	double Charge;

	/*
	 * Called once with the corresponding config section
	 * from the configuration file. Do all one time set up routines
	 * here.
	 */
	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("angular_rank", angularRank);
		config.Get("radial_rank", radialRank);
		config.Get("charge", Charge);
	}

	/*
	 * Called for every grid point at every time step. 
	 */
	inline cplx GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		double r = pos(radialRank);
		double theta = pos(angularRank);
		return -Charge * cplx(0.,1.) * cos(theta) / r;
	}
};

template<int Rank>
class AngularKineticEnergyPotential : public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	//Potential parameters
	int angularRank;
	int radialRank;
	double mass;

	/*
	 * Called once with the corresponding config section
	 * from the configuration file. Do all one time set up routines
	 * here.
	 */
	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("angular_rank", angularRank);
		config.Get("radial_rank", radialRank);
		config.Get("mass", mass);
	}

	/*
	 * Called for every grid point at every time step. 
	 */
	inline double GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		double l = pos(angularRank);
		double r = pos(radialRank);
		return l*(l+1.0) / (2 * mass * r*r);
	}
};

template<int Rank>
class RadialHarmonicPotential : public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	//Potential parameters
	int angularRank;
	int radialRank;

	/*
	 * Called once with the corresponding config section
	 * from the configuration file. Do all one time set up routines
	 * here.
	 */
	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("angular_rank", angularRank);
		config.Get("radial_rank", radialRank);
	}

	/*
	 * Called for every grid point at every time step. 
	 */
	inline double GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		double r = pos(radialRank);
		return 0.5*r*r;
	}
};

template<int Rank>
class RadialCoulombPotential : public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	//Potential parameters
	int angularRank;
	int radialRank;

	/*
	 * Called once with the corresponding config section
	 * from the configuration file. Do all one time set up routines
	 * here.
	 */
	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("angular_rank", angularRank);
		config.Get("radial_rank", radialRank);
	}

	/*
	 * Called for every grid point at every time step. 
	 */
	inline double GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		double r = pos(radialRank);
		return - 1.0 / r;
	}
};

template<int Rank>
class H2pPotential : public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	//Potential parameters
	double Charge;
	double NuclearSeparation;
	double Softing;

	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("charge", Charge);
		config.Get("nuclear_separation", NuclearSeparation);
		config.Get("softing", Softing);
	}

	inline double GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		//Coordinates
		double r = std::abs(pos(1));
		double theta = pos(0);

		double r2 = sqr(r) + sqr(NuclearSeparation) / 4 + sqr(Softing);
		double z = r * cos(theta);
	
		double angDep = NuclearSeparation * z; 
		double V1 = 1 / sqrt(r2 + angDep); 
		double V2 = 1 / sqrt(r2 - angDep); 

		return Charge * (V1 + V2);
	}
};

template<int Rank>
class CoulombSofted1D : public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	//Potential parameters
	double SoftParam;
	double Charge;

	/*
	 * Called once with the corresponding config section
	 * from the configuration file. Do all one time set up routines
	 * here.
	 */
	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("soft_param", SoftParam);
		config.Get("charge", Charge);
	}

	/*
	 * Called for every grid point at every time step. 
	 */
	inline double GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		double x = pos(0);
		return Charge / std::sqrt(x * x + SoftParam*SoftParam);
	}
};


template<int Rank>
class SingleActiveElectronPotential : public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	int angularRank;
	int radialRank;

	//Potential parameters
	double Z;
	double a1;
	double a2;
	double a3;
	double a4;
	double a5;
	double a6;

	/*
	 * Called once with the corresponding config section
	 * from the configuration file. Do all one time set up routines
	 * here.
	 */
	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("z", Z);
		config.Get("a1", a1);
		config.Get("a2", a2);
		config.Get("a3", a3);
		config.Get("a4", a4);
		config.Get("a5", a5);
		config.Get("a6", a6);

		config.Get("angular_rank", angularRank);
		config.Get("radial_rank", radialRank);
	}

	/*
	 * Called for every grid point at every time step. 
	 *
	 * Some general tips for max efficiency:
	 * - If possible, move static computations to ApplyConfigSection.
	 * - Minimize the number of branches ("if"-statements are bad)
	 * - Minimize the number of function calls (sin, cos, exp, are bad)
	 * - Long statements can confuse the compiler, consider making more 
	 *   simpler statements
	 */
	inline double GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		double r = std::fabs(pos(radialRank));
		
		double V = -(Z + a1 * exp(-a2 * r) + a3 * r * exp(-a4 * r)
			+ a5 * exp(-a6 * r)) / r;

		return V;
	}
};


template<int Rank>
class OverlapPotential : public PotentialBase<Rank>
{
public:
	//Required by DynamicPotentialEvaluator
	cplx TimeStep;
	double CurTime;

	int angularRank;
	int radialRank;

	void ApplyConfigSection(const ConfigSection &config)
	{
	}

	inline double GetPotentialValue(const blitz::TinyVector<double, Rank> &pos)
	{
		return 1.0;
	}
};


#include <core/representation/combinedrepresentation.h>
#include <core/representation/reducedspherical/reducedsphericalharmonicrepresentation.h>
#include "laserhelper.h"

/* First part of the linearly polarized laser in the velocity gauge
 * expressed in spherical harmonics
 *
 * <Ylm | - \frac{1}{r} \sin \theta \partialdiff{}{\theta} 
 *	      - \frac{\cos \theta}{r} | Yl'm'>
 */
template<int Rank>
class CustomPotential_LaserVelocity1_ReducedSpherical
{
public:
	typedef blitz::Array<int, 2> BasisPairList;

private:
	BasisPairList AngularBasisPairs;
	int AngularRank;
	int RadialRank;

public:
	CustomPotential_LaserVelocity1_ReducedSpherical() {}
	virtual ~CustomPotential_LaserVelocity1_ReducedSpherical() {}

	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("radial_rank", RadialRank);
		config.Get("angular_rank", AngularRank);
	}

	virtual void SetBasisPairs(int rank, const BasisPairList &basisPairs)
	{
		if (rank != AngularRank)
		{
			throw std::runtime_error("Only angular rank supports basis pairs");
		}
		AngularBasisPairs.reference(basisPairs.copy());
	}

	BasisPairList GetBasisPairList(int rank)
	{
		if (rank == AngularRank)
			return AngularBasisPairs;
		else
			return BasisPairList();
	}

	virtual void UpdatePotentialData(typename blitz::Array<cplx, Rank> data, typename Wavefunction<Rank>::Ptr psi, cplx timeStep, double curTime)
	{
		using namespace ReducedSpherical;

		typedef CombinedRepresentation<Rank> CmbRepr;
		typename CmbRepr::Ptr repr = boost::static_pointer_cast< CmbRepr >(psi->GetRepresentation());
		ReducedSphericalHarmonicRepresentation::Ptr angRepr = boost::static_pointer_cast< ReducedSphericalHarmonicRepresentation >(repr->GetRepresentation(AngularRank));
	
		int rCount = data.extent(RadialRank);
		int angCount = data.extent(AngularRank);

		blitz::Array<double, 1> localr = psi->GetRepresentation()->GetLocalGrid(RadialRank);
		BasisPairList angBasisPairs = GetBasisPairList(AngularRank);

		if (psi->GetRepresentation()->GetDistributedModel()->IsDistributedRank(AngularRank)) throw std::runtime_error("Angular rank can not be distributed");
		if (data.extent(RadialRank) != rCount) throw std::runtime_error("Invalid r size");
		if (data.extent(AngularRank) != angBasisPairs.extent(0)) throw std::runtime_error("Invalid ang size");

		cplx IM(0,1.0);

		data = 0;
		blitz::TinyVector<int, Rank> index;
	
		for (int angIndex=0; angIndex<angCount; angIndex++)
		{
			index(AngularRank) = angIndex;

			int leftIndex = angBasisPairs(angIndex, 0);
			int rightIndex = angBasisPairs(angIndex, 1);
	
			//"Left" quantum numbers
			int l = leftIndex;
			int m = 0;
			
			//"Right" quantum numbers (Mp = M)
			int lp = rightIndex;
			int mp = 0;

			double C = LaserHelper::C(lp, mp) * LaserHelper::kronecker(l, lp+1);
			double D = LaserHelper::D(lp, mp) * LaserHelper::kronecker(l, lp-1);
			double E = LaserHelper::E(lp, mp) * LaserHelper::kronecker(l, lp+1);
			double F = LaserHelper::F(lp, mp) * LaserHelper::kronecker(l, lp-1);

			double coupling = -(C + D) - (E + F);

			for (int ri=0; ri<rCount; ri++)
			{
				index(RadialRank) = ri;
				double r = localr(ri);

				data(index) = - IM * coupling/r;
			}
		}
	}
};

/* Second part of the linearly polarized laser in the velocity gauge
 * expressed in spherical harmonics.
 *
 * Should be used with first order differentiation in r
 *
 * <Ylm | \frac{\partial}{\partial r} \cos \theta | Yl'm'>
 */
template<int Rank>
class CustomPotential_LaserVelocity2_ReducedSpherical
{
public:
	typedef blitz::Array<int, 2> BasisPairList;

private:
	BasisPairList AngularBasisPairs;
	int AngularRank;
	int RadialRank;

public:
	CustomPotential_LaserVelocity2_ReducedSpherical() {}
	virtual ~CustomPotential_LaserVelocity2_ReducedSpherical() {}

	void ApplyConfigSection(const ConfigSection &config)
	{
		config.Get("radial_rank", RadialRank);
		config.Get("angular_rank", AngularRank);
	}

	virtual void SetBasisPairs(int rank, const BasisPairList &basisPairs)
	{
		if (rank != AngularRank)
		{
			throw std::runtime_error("Only angular rank supports basis pairs");
		}
		AngularBasisPairs.reference(basisPairs.copy());
	}

	BasisPairList GetBasisPairList(int rank)
	{
		if (rank == AngularRank)
			return AngularBasisPairs;
		else
			return BasisPairList();
	}

	virtual void UpdatePotentialData(typename blitz::Array<cplx, Rank> data, typename Wavefunction<Rank>::Ptr psi, cplx timeStep, double curTime)
	{
		using namespace ReducedSpherical;

		typedef CombinedRepresentation<Rank> CmbRepr;
		typename CmbRepr::Ptr repr = boost::static_pointer_cast< CmbRepr >(psi->GetRepresentation());
		ReducedSphericalHarmonicRepresentation::Ptr angRepr = boost::static_pointer_cast< ReducedSphericalHarmonicRepresentation >(repr->GetRepresentation(AngularRank));
	
		int rCount = data.extent(RadialRank);
		int angCount = data.extent(AngularRank);

		blitz::Array<double, 1> localr = psi->GetRepresentation()->GetLocalGrid(RadialRank);
		BasisPairList angBasisPairs = GetBasisPairList(AngularRank);

		if (psi->GetRepresentation()->GetDistributedModel()->IsDistributedRank(AngularRank)) throw std::runtime_error("Angular rank can not be distributed");
		if (data.extent(RadialRank) != rCount) throw std::runtime_error("Invalid r size");
		if (data.extent(AngularRank) != angBasisPairs.extent(0)) 
		{
			cout << "Angular Rank = " << AngularRank << ", " << data.extent(AngularRank) << " != " << angBasisPairs.extent(0) << endl;
			throw std::runtime_error("Invalid ang size");
		}

		data = 0;
		blitz::TinyVector<int, Rank> index;

		cplx IM(0,1.0);
	
		for (int angIndex=0; angIndex<angCount; angIndex++)
		{
			index(AngularRank) = angIndex;

			int leftIndex = angBasisPairs(angIndex, 0);
			int rightIndex = angBasisPairs(angIndex, 1);
	
			//"Left" quantum numbers
			int l = leftIndex;
			int m = 0;
			
			//"Right" quantum numbers (Mp = M)
			int lp = rightIndex;
			int mp = 0;

			double E = LaserHelper::E(lp, mp) * LaserHelper::kronecker(l, lp+1);
			double F = LaserHelper::F(lp, mp) * LaserHelper::kronecker(l, lp-1);

			double coupling = (E + F);

			for (int ri=0; ri<rCount; ri++)
			{
				index(RadialRank) = ri;
				double r = localr(ri);

				data(index) =  - IM * coupling;
			}
		}
	}
};

