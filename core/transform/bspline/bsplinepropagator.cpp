#include "bsplinepropagator.h"
#include "../representation/representation.h"
#include "../../utility/blitzblas.h"
#include "../../utility/blitztricks.h"
#include "../../utility/blitzlapack.h"
#include <cmath>


namespace BSpline
{

template<int Rank>
void Propagator<Rank>::ApplyConfigSection(const ConfigSection &config)
{
	config.Get("mass", Mass);
	cout << "BSplinePropagator: Mass = " << Mass << endl;
}


template<int Rank>
void Propagator<Rank>::Setup(const cplx &dt, const Wavefunction<Rank> &psi, 
	BSpline::Ptr bsplineObject, int rank)
{
	using namespace blitz;

	TimeStep = dt;

	//Get b-spline object from wavefunction
	BSplineObject = bsplineObject;

	//Set class parameters
	PropagateRank = rank;

	//Call setup routine to calculate all LAPACK form matrices
	SetupLapackMatrices(dt);

	//Call setup routine to calculate all BLAS form matrices
	SetupBlasMatrices(dt);

	//Allocate temp data
	TempData.resize(PropagationMatrix.extent(0));
}

/*
 * Advance the wavefunction one time step
 */
template<int Rank>
void Propagator<Rank>::AdvanceStep(Wavefunction<Rank> &psi)
{
	using namespace blitz;

	//Map the data to a 3D array, where the b-spline part is the 
	//middle rank
	Array<cplx, 3> data3d = MapToRank3(psi.Data, PropagateRank, 1);

	//Propagate the 3D array
	ApplyCrankNicolson(PropagationMatrix, data3d);
}


template<int Rank>
void Propagator<Rank>::MultiplyHamiltonian(Wavefunction<Rank> &srcPsi, Wavefunction<Rank> &dstPsi)
{
	using namespace blitz;

	int N = BSplineObject->NumberOfBSplines;
	int offDiagonalBands = BSplineObject->MaxSplineOrder - 1;
	linalg::LAPACK<cplx> lapack;

	//Map the data to a 3D array, where the b-spline part is the 
	//middle rank
	Array<cplx, 3> srcData = MapToRank3(srcPsi.Data, PropagateRank, 1);
	Array<cplx, 3> dstData = MapToRank3(dstPsi.Data, PropagateRank, 1);
	Array<cplx, 2> matrix = GetHamiltonianMatrix();

	Array<int, 1> pivot(N);
	Array<cplx, 2> smat(OverlapMatrix.shape());

	//iterate over the array directions which are not propagated by this
	//propagator
	Array<cplx, 1> temp(srcData.extent(1));
	for (int i = 0; i < srcData.extent(0); i++)
	{
		for (int j = 0; j < srcData.extent(2); j++)
		{
			// smat is a copy of the overlap matrix.
			// Need to copy this every iteration since LAPACK
			// call destroys input matrix.
			smat = OverlapMatrix;

			Array<cplx, 1> v = srcData(i, Range::all(), j);
			Array<cplx, 1> w = dstData(i, Range::all(), j);
			MatrixVectorMultiplyHermitianBanded(matrix, v, temp, 1.0, 0.0);

			//Then call LAPACK to solve system of equations
			//    S * d = b
			pivot = 0;
			lapack.SolveGeneralBandedSystemOfEquations(smat, pivot, temp, offDiagonalBands, 
				offDiagonalBands);
			w += temp;
		}
	}
}


/*
 * Propagate the b-spline rank of the wavefunction using the Crank-Nicolson method.
 * Since the b-splines are not orthogonal, the usual identity matrix appearing in
 * the formula is replaced by the overlap matrix S. This matrix is sparse (2k - 1 bands),
 * and we utilize this by first calling a BLAS function to do the banded matrix-vector
 * multiplication on the right, before calling LAPACK to solve the system of equation.
 *
 *     M * c(t+dt/2) = b(t-dt/2)  (solve using LAPACK)
 *     b = conj(M) * c(t-dt/2)    (perform using BLAS)
 *     M = S + idt/2 * H
 * 
 */
template<int Rank>
void Propagator<Rank>::ApplyCrankNicolson(const blitz::Array<cplx, 2> &matrix, 
	blitz::Array<cplx, 3> &data)
{
	using namespace blitz;

	Array<cplx, 1> temp = TempData;
	int N = BSplineObject->NumberOfBSplines;
	int offDiagonalBands = BSplineObject->MaxSplineOrder - 1;
	Array<int, 1> pivot(N);
	Array<cplx, 2> pmat(PropagationMatrix.shape());

	cplx scaling = -I * TimeStep / 2.0;
			
	//iterate over the array directions which are not propagated by this
	//propagator
	for (int i=0; i<data.extent(0); i++)
	{
		for (int j=0; j<data.extent(2); j++)
		{
			// pmat is a copy of the propagation matrix.
			// Need to copy this every iteration since LAPACK
			// call destroys input matrix.
			pmat = PropagationMatrix;

			/* v is a view of a slice of the wave function
			 * temp is a temporary copy of that slice
			 */
			Array<cplx, 1> v = data(i, Range::all(), j);
			temp = v; 

			//Call BLAS function for fast banded matrix-vector product
			MatrixVectorMultiplyHermitianBanded(HamiltonianMatrix, temp, v, scaling, 0.0);
			MatrixVectorMultiplyHermitianBanded(PropagationMatrixBlas, temp, v, 1.0, 1.0);

			//Then call LAPACK to solve banded system of equations, obtaining 
			//solution at t+dt/2
			pivot = 0;
			linalg::LAPACK<cplx> lapack;
			lapack.SolveGeneralBandedSystemOfEquations(pmat, pivot, v, offDiagonalBands, 
				offDiagonalBands);
		}
	}
}


template<int Rank>
void Propagator<Rank>::SetupLapackMatrices(const cplx &dt)
{
	int k = BSplineObject->MaxSplineOrder;
	int N = BSplineObject->NumberOfBSplines;
	int ldab = 3 * k - 2;
	cplx Im = cplx(0.0, 1.0);

	PropagationMatrix.resize(N, ldab);
	PropagationMatrix = 0;

	//Get full b-bspline overlap matrix (stored on LAPACK form)
	OverlapMatrix.reference( BSplineObject->GetBSplineOverlapMatrixFull().copy() );

	cplx ham = 0.0;
	cplx overlap = 0.0;
	for (int i = 0; i < N; i++)
	{
		int jMax = std::min(i + k, N);
		for (int j = i; j < jMax; j++)
		{
			//Upper lapack indices
			int Ju = j;
			int Iu = 2 * k - 2 + i - j;

			//Lower lapack indices, from transposing S and H matrices
			int Jl = i;
			int Il = 2 * k - 2 + j - i;

			ham = -1.0 / (2.0 * Mass) * BSplineObject->BSplineDerivative2OverlapIntegral(i, j);
			overlap = BSplineObject->BSplineOverlapIntegral(i, j);

			//PropagationMatrix(Ju, Iu) = OverlapMatrix(Ju, Iu) + Im * dt / 2.0 * ham;
			//PropagationMatrix(Jl, Il) = OverlapMatrix(Jl, Il) + Im * dt / 2.0 * ham;
			PropagationMatrix(Ju, Iu) = overlap + Im * dt / 2.0 * ham;
			PropagationMatrix(Jl, Il) = overlap + Im * dt / 2.0 * ham;
		}
	}
}


template<int Rank>
void Propagator<Rank>::SetupBlasMatrices(const cplx &dt)
{
	cplx Im = cplx(0.0, 1.0);
	int k = BSplineObject->MaxSplineOrder;
	int N = BSplineObject->NumberOfBSplines;
	int lda = k;
	PropagationMatrixBlas.resize(N, lda);
	PropagationMatrixBlas = 0;
	HamiltonianMatrix.resize(N, lda);
	HamiltonianMatrix = 0;

	cplx ham = 0.0;
	cplx overlap = 0.0;
	for (int j = 0; j < N; j++)
	{
		int iMax = std::min(j + k, N);
		for (int i = j; i < iMax; i++)
		{
			int J = j;
			int I = i - j;

			//BSplineOverlapIntegral must have j >= i, so we transpose.
			//This is okay, since the matrix is real and symmetric.
			ham = -1.0 / (2.0 * Mass) * BSplineObject->BSplineDerivative2OverlapIntegral(j, i);
			overlap = BSplineObject->BSplineOverlapIntegral(j, i);

			//PropagationMatrixBlas(J, I) = overlap - Im * dt / 2.0 * ham;
			PropagationMatrixBlas(J, I) = overlap;
			HamiltonianMatrix(J, I) = ham;
		}
	}
}


//Instantiate propagators of rank 1-4
template class Propagator<1>;
template class Propagator<2>;
template class Propagator<3>;
template class Propagator<4>;

} //Namespace

