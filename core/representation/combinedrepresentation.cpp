#include "combinedrepresentation.h"
#include "cartesianrepresentation.h"
#include "../utility/blitztricks.h"
#include "../utility/blitzblas.h"

template<int Rank>
CombinedRepresentation<Rank>::CombinedRepresentation() 
{
	Algorithm = 3;
}

template<int Rank>
CombinedRepresentation<Rank>::~CombinedRepresentation() 
{
}


template<int Rank>
typename Representation<Rank>::RepresentationPtr CombinedRepresentation<Rank>::Copy()
{
	return typename Representation<Rank>::RepresentationPtr(new CombinedRepresentation<Rank>(*this));
}


/*----------------------------------------------------------------------------
                Implementation of the Representation interface
  ----------------------------------------------------------------------------*/
template<int Rank> blitz::Array<double, 1> CombinedRepresentation<Rank>::
GetGlobalGrid(int rank)
{
	//Get the local grid in the specified rank
	return GetRepresentation(rank)->GetGlobalGrid(rank);
}

template<int Rank> blitz::Array<double, 1> CombinedRepresentation<Rank>::
GetGlobalWeights(int rank)
{
	//Get the local grid in the specified rank
	return GetRepresentation(rank)->GetGlobalWeights(rank);
}

template<int Rank> blitz::TinyVector<int, Rank> CombinedRepresentation<Rank>
::GetFullShape() 
{
	blitz::TinyVector<int, Rank> shape;
	for (int i=0;i<Rank;i++)
	{
		shape(i) = GetRepresentation(i)->GetFullShape()(0);
	}
	return shape;
}

//Get the representation of the specified rank
template<int Rank> Representation1DPtr CombinedRepresentation<Rank>
::GetRepresentation(int rank)
{
	//return Representations[rank];
	return Representations(rank);
}

//Change the representation of the specified rank
template<int Rank> void CombinedRepresentation<Rank>
::SetRepresentation(int rank, Representation1DPtr repr)
{
	if (Representations(rank) != 0 && Representations(rank)->GetDistributedModel() != 0 && repr->GetDistributedModel() != 0)
	{
		repr->GetDistributedModel()->SetDistribution(Representations(rank)->GetDistributedModel()->GetDistribution());
	}
	Representations(rank) = repr;
}

template<int Rank> void CombinedRepresentation<Rank>
::ApplyConfigSection(const ConfigSection &config) 
{
	//Do this manually for each sub-representation

	if (config.HasValue("innerproduct_algorithm"))
	{
		config.Get("innerproduct_algorithm", Algorithm);
	}
}

template<int Rank>
OverlapMatrix::Ptr CombinedRepresentation<Rank>::GetGlobalOverlapMatrix(int rank)
{
	return GetRepresentation(rank)->GetGlobalOverlapMatrix(rank);
}

template<int Rank>
void CombinedRepresentation<Rank>::MultiplyOverlap(Wavefunction<Rank> &psi)
{
	for (int i=0; i<Rank; i++)
	{	
		if (this->GetDistributedModel()->IsDistributedRank(i) && !this->IsOrthogonalBasis(i))
		{
			throw std::runtime_error("Rank is distributed and not orthogonal");
		}

		blitz::Array<cplx, 3> data = MapToRank3(psi.GetData(), i, 1);
		if (this->IsOrthogonalBasis(i))
		{
			blitz::Array<double, 1> weights = this->GetLocalWeights(i);
			data *= weights(blitz::tensor::j) + 0*blitz::tensor::k;
		}
		else
		{
			this->GetGlobalOverlapMatrix(i)->MultiplyOverlapTensor(data);
		}
	}
}

template<int Rank>
void CombinedRepresentation<Rank>::SolveOverlap(Wavefunction<Rank> &psi)
{
	for (int i=0; i<Rank; i++)
	{	
		if (this->GetDistributedModel()->IsDistributedRank(i) && !this->IsOrthogonalBasis(i))
		{
			throw std::runtime_error("Rank is distributed and not orthogonal");
		}
		blitz::Array<cplx, 3> data = MapToRank3(psi.GetData(), i, 1);
		if (this->IsOrthogonalBasis(i))
		{
			blitz::Array<double, 1> weights = this->GetLocalWeights(i);
			data /= weights(blitz::tensor::j) + 0*blitz::tensor::k;
		}
		else
		{
			this->GetGlobalOverlapMatrix(i)->SolveOverlapTensor(data);
		}
	}
}

template<int Rank>
void CombinedRepresentation<Rank>::MultiplySqrtOverlap(bool conjugate, Wavefunction<Rank> &psi)
{
	for (int i=0; i<Rank; i++)
	{	
		if (this->GetDistributedModel()->IsDistributedRank(i) && !this->IsOrthogonalBasis(i))
		{
			throw std::runtime_error("Rank is distributed and not orthogonal");
		}
		blitz::Array<cplx, 3> data = MapToRank3(psi.GetData(), i, 1);
		if (this->IsOrthogonalBasis(i))
		{
			blitz::Array<double, 1> weights = this->GetLocalWeights(i);
			//TODO: This can't be good. too many sqrt evals
			data *= sqrt(weights(blitz::tensor::j)) + 0*blitz::tensor::k;
		}
		else
		{
			this->GetGlobalOverlapMatrix(i)->MultiplySqrtOverlapTensor(conjugate, data);
		}
	}
}

template<int Rank>
void CombinedRepresentation<Rank>::SolveSqrtOverlap(bool conjugate, Wavefunction<Rank> &psi)
{
	for (int i=0; i<Rank; i++)
	{	
		if (this->GetDistributedModel()->IsDistributedRank(i) && !this->IsOrthogonalBasis(i))
		{
			throw std::runtime_error("Rank is distributed and not orthogonal");
		}
		blitz::Array<cplx, 3> data = MapToRank3(psi.GetData(), i, 1);
		if (this->IsOrthogonalBasis(i))
		{
			blitz::Array<double, 1> weights = this->GetLocalWeights(i);
			//TODO: This can't be good. too many sqrt evals
			data /= sqrt(weights(blitz::tensor::j)) + 0*blitz::tensor::k;
		}
		else
		{
			this->GetGlobalOverlapMatrix(i)->SolveSqrtOverlapTensor(conjugate, data);
		}
	}
}


template<int Rank> cplx CombinedRepresentation<Rank>
::InnerProduct(const Wavefunction<Rank>& w1, const Wavefunction<Rank>& w2)
{
	blitz::Array<cplx, Rank> d1(w1.GetData());
	blitz::Array<cplx, Rank> d2(w2.GetData());

	/*
	 * Algorithm1 is faster for orthogonal basises
	 * Algorithm2 is faster for nonorthogonal basies
	 * Algorithm3 is the only one working for parallel problems, but require
	 *    more memory
	 *
	 * For a combination of orthogonal and non-orthogonal
	 * basises, 1 and 2 are most likely almost equally fast 
	 *
	 * Conclusion: Algo 3 is default
	 */

	if (Algorithm == 1)
	{
		return InnerProductImpl_Algo1(d1, d2);
	}
	else if (Algorithm == 2)
	{
		return InnerProductImpl_Algo2(d1, d2);
	}
	else if (Algorithm == 3)
	{
		blitz::TinyVector<int, Rank> shape = d1.shape();
		
		blitz::Array<cplx, Rank> temp1;
		blitz::Array<cplx, Rank> temp2;
		
		int tempName[2];
		int tempNamePsi[2];
		Wavefunction<Rank>* psiList[2];
		for (int i=0; i<2; i++)
		{
			tempName[i] = -1;
			tempNamePsi[i] = -1;
		}
		psiList[0] = const_cast<Wavefunction<Rank>*>(&w1);
		psiList[1] = const_cast<Wavefunction<Rank>*>(&w2);

		//Find any available buffers of correct size on any of the wavefunctions
		for (int i=0; i<2; i++)
		{
			//See if there is an available buffer in psi j
			for (int j=0; j<2; j++)
			{
				int name = psiList[j]->GetAvailableDataBufferName(shape);
				if (name != -1)
				{
					tempName[i] = name;
					tempNamePsi[i] = j;
					psiList[j]->LockBuffer(name);
					break;
				}
			}
		}

		//If we didnt find two available buffers, we must allocate
		//We'll allocate on w2
		for (int i=0; i<2; i++)
		{
			if (tempName[i] == -1)
			{
				tempName[i] = psiList[1]->AllocateData(shape);
				tempNamePsi[i] = 1;
				psiList[1]->LockBuffer(tempName[i]);
			}
		}

		//Get the actual data buffers
		temp1.reference(psiList[tempNamePsi[0]]->GetData(tempName[0]));
		temp2.reference(psiList[tempNamePsi[1]]->GetData(tempName[1]));

		//Perform MatrixVector multiplication
		//first step
		//
		
		for (int i=0; i<Rank; i++)
		{
			if (this->GetDistributedModel()->IsDistributedRank(i) && !this->IsOrthogonalBasis(i))
			{
				throw std::runtime_error("This inner product only supports parallelization for orthogonal ranks");
			}

			if (this->IsOrthogonalBasis(i))
			{
				if (i == 0)
				{
					temp1 = d2;
				}
				//TODO: Make this faster by moving it to TensorMultiply
				blitz::Array<double, 1> weights = this->GetLocalWeights(i);
				blitz::Array<cplx, 3> temp3d = MapToRank3(temp1, i, 1);
				temp3d *= weights(blitz::tensor::j) + 0*blitz::tensor::k;
			}
			else
			{
				blitz::Array<cplx, 2> overlapMatrix = this->GetGlobalOverlapMatrix(i)->GetOverlapHermitianLower();
				//Reshape the overlap matrix into a N-d array suitable for TensorPotentialMultiply
				blitz::TinyVector<int, Rank> overlapShape = 1;
				overlapShape(i) = overlapMatrix.size();
				blitz::TinyVector<int, Rank> overlapStride = 1;
				for (int j=0; j<i; j++)
				{
					overlapStride(j) = overlapMatrix.size();
				}
				blitz::Array<cplx, Rank> overlapTensor(overlapMatrix.data(), overlapShape, overlapStride, blitz::neverDeleteData);
		
				if (i==0)
				{
					temp1 = 0;
					TensorPotentialMultiply_Rank1_Band(i, overlapTensor, 1.0, d2, temp1);
				}
				else
				{
					temp2 = 0;
					TensorPotentialMultiply_Rank1_Band(i, overlapTensor, 1.0, temp1, temp2);
					blitz::swap(temp1, temp2);
				}
			}
		}

		//Calculate inner product by overlap of the vectors
		cplx innerProduct = VectorInnerProduct(d1, temp1);

		for (int i=0; i<2; i++)
		{
			psiList[tempNamePsi[i]]->UnLockBuffer(tempName[i]);
		}
	
		return innerProduct;
	}
	else
	{
		cout << "Unknown InnerProduct algorithm " << Algorithm << endl;
		throw std::runtime_error("Unknown InnerProduct algorithm");
	}

}


/*
 * Multiply rank of wavefunction by overlapmatrix
 */
template<int Rank> void CombinedRepresentation<Rank>
::MultiplyOverlap(Wavefunction<Rank> &srcPsi, Wavefunction<Rank> &dstPsi, int rank)
{
	using namespace blitz;

	if (this->IsOrthogonalBasis(rank))
	{
		//Todo: should multiply weights
		dstPsi.GetData() = srcPsi.GetData();
	}
	else
	{
		//Map the data to a 3D array, where the b-spline part is the middle rank
		Array<cplx, 3> srcData = MapToRank3(srcPsi.Data, rank, 1);
		Array<cplx, 3> dstData = MapToRank3(dstPsi.Data, rank, 1);

		this->GetGlobalOverlapMatrix(rank)->MultiplyOverlapTensor(srcData, dstData);
	}

}



/*----------------------------------------------------------------------------
                Implementation of the inner product
  ----------------------------------------------------------------------------*/

template<int Rank> 
cplx CombinedRepresentation<Rank>::InnerProductImpl_Algo1(DataArray d1, DataArray d2)
{
	/* 
	 * Specialized versions of the inner product algorithms are generated
	 * by combinedrepresentation_generator.py and compiled separately
	 */	
	throw std::runtime_error("InnerProduct Not Implemented");
}

template<int Rank> 
cplx CombinedRepresentation<Rank>::InnerProductImpl_Algo2(DataArray d1, DataArray d2)
{
	/* 
	 * Specialized versions of the inner product algorithms are generated
	 * by combinedrepresentation_generator.py and compiled separately
	 */
	throw std::runtime_error("InnerProduct Not Implemented");
}

//Include the generated implementations
#include "combinedrepresentation_generated.cpp"

template class CombinedRepresentation<1>;
template class CombinedRepresentation<2>;
template class CombinedRepresentation<3>;
template class CombinedRepresentation<4>;

