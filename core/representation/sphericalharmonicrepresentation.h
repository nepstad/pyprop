#ifndef LMREPRESENTATION_H
#define LMREPRESENTATION_H

#include "../common.h"
#include "orthogonalrepresentation.h"
#include "lmrange.h"

/** Represents the wavefunction in a spherical harmonic (l,m) basis.
  * The spherical harmonic of highest order which is represented is 
  * Ylm with l == Range.MaxL, which leaves Range.Count() == (1 + MaxL)**2
  * functions 
  */
class SphericalHarmonicRepresentation : public OrthogonalRepresentation
{
public:
	typedef shared_ptr<SphericalHarmonicRepresentation> Ptr;

	LmRange Range;

	//Constructors
	SphericalHarmonicRepresentation() {}
	virtual ~SphericalHarmonicRepresentation() {}

	virtual Representation<1>::RepresentationPtr Copy()
	{
		return Representation<1>::RepresentationPtr(new SphericalHarmonicRepresentation(*this));
	}

	void SetupRepresentation(int maxL)
	{
		Range = LmRange(maxL);
	}

	/* ---------- Implementation of Representation<1> interface ----------- */
		
	//Returns the size of the grid 
	virtual blitz::TinyVector<int, 1> GetFullShape()
	{
		return Range.Count();
	}

	/*
	 * Performs an inner product between two radial wavefunctions
	 * This should probably not be called to often, because a faster version
	 * will be available in SphericalRepresentation
	 */
	virtual std::complex<double> InnerProduct(const Wavefunction<1>& w1, const Wavefunction<1>& w2)
	{
		std::cout << "Calculating inner product of spherical harmonics in "
		          << "SphericalHarmonicRepresentation. This should probably be done "
			  << "in the combined representation insted for optimal efficiency"
			  << std::endl;
		
	
		//The inner product in the spherical harmonics representation is
		//simply the sum of the product between each element. This can be shown 
		//from the definition of the expansion coefficients (integration is already
		//taken care of by the spherical harmonics)
		return sum(conj(w1.Data) * w2.Data); 
	}

	/** 
	Returns the portion of the grid local to the current processor.
	**/
	virtual blitz::Array<double, 1> GetGlobalWeights(int rank)
	{
		if (rank != GetBaseRank())
		{
			cout << "Warning: Trying to get the wrong sphharm rank. Got " << rank << ", expected " << GetBaseRank() <<  endl;
		}
		return Range.GetWeights();
	}
	
	/** 
	Returns the portion of the grid local to the current processor.
	**/
	virtual blitz::Array<double, 1> GetGlobalGrid(int rank)
	{
		if (rank != GetBaseRank())
		{
			cout << "Warning: Trying to get the wrong sphharm rank. Got " << rank << ", expected " << GetBaseRank() <<  endl;
		}
		return Range.GetIndexGrid();
	}

	/** 
	Returns the portion of the grid local to the current processor.
	**/
	virtual blitz::Array<double, 2> GetLocalLmGrid()
	{
		blitz::Array<double, 2> lmGrid( Range.GetLmGrid() );
		int size = lmGrid.extent(0);

		blitz::Range indexRange = this->GetDistributedModel()->GetLocalIndexRange(size, GetBaseRank());
		return lmGrid(indexRange, blitz::Range::all());
	}
	
	/** Apply config, and set up Range
	  */
	virtual void ApplyConfigSection(const ConfigSection &config)
	{
		int maxl;
		config.Get("maxl", maxl);
		Range = LmRange(maxl);
	}

};

typedef boost::shared_ptr<SphericalHarmonicRepresentation> SphericalHarmonicRepresentationPtr;

#endif
