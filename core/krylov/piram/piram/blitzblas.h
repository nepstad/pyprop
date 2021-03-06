#ifndef PIRAM_BLITZBLAS_H
#define PIRAM_BLITZBLAS_H

#include <blitz/array.h>
#include <complex>

#ifdef PYPROP_USE_BLAS_MKL
#include <mkl_cblas.h>
#else
extern "C"
{
#include <cblas.h>
}
#endif

#define BLAS_NAME(x) cblas_ ## x

#include <core/common.h>

namespace blitz
{
namespace linalg
{

using namespace blitz;

class MatrixTranspose
{
public:
	MatrixTranspose(int value) : value(value) {}

	bool operator==(const MatrixTranspose &other) const
	{
		return other.value == value;
	}

	bool operator==(int otherValue) const
	{
		return otherValue == value;
	}

	operator char()
	{
		if (value == None) return 'N';
		if (value == Transpose) return 'T';
		if (value == Conjugate) return 'C';
		return -1;
	}

	operator CBLAS_TRANSPOSE()
	{
		if (value == Transpose) return CblasTrans;
		if (value == Conjugate) return CblasConjTrans;
		return CblasNoTrans;
	}

	static const int None = 1; 
	static const int Transpose = 2;
	static const int Conjugate = 3;

private:
	int value;
};

class MatrixHermitianStorage
{
public:
	MatrixHermitianStorage(int value) : value(value) {}

	bool operator==(const MatrixHermitianStorage &other) const
	{
		return other.value == value;
	}

	bool operator==(int otherValue) const
	{
		return otherValue == value;
	}

	operator char()
	{
		if (value == Upper) return 'U';
		if (value == Lower) return 'L';
		return -1;
	}

	operator CBLAS_UPLO()
	{
		if (value == Upper) return CblasUpper;
		return CblasLower;
	}

	static const int Upper = 1; 
	static const int Lower = 2;

private:
	int value;
};

class MatrixDiagonal
{
public:
	MatrixDiagonal(int value) : value(value) {}

	bool operator==(const MatrixDiagonal &other) const
	{
		return other.value == value;
	}

	bool operator==(int otherValue) const
	{
		return otherValue == value;
	}

	operator char()
	{
		if (value == Unit) return 'U';
		if (value == NonUnit) return 'N';
		return -1;
	}

	operator CBLAS_DIAG()
	{
		if (value == Unit) return CblasUnit;
		return CblasNonUnit;
	}

	static const int Unit = 1; 
	static const int NonUnit = 2;

private:
	int value;
};

template <class T>
class BLAS
{


public:
	typedef Array<T, 1> VectorType;
	typedef Array<T, 2> MatrixType;

	/*
	 * BLAS Level 1
	 */

	// xCOPY: dst = src
	void CopyVector(VectorType &src, VectorType &dst);

	// xSCAL: vector *= scaling
	void ScaleVector(VectorType &vector, T scaling);

	// xAXPY: dst += scaling * src
	void AddVector(VectorType &src, T scaling, VectorType &dst);

	// xDOTy: sum( conj(x) * y )
	T InnerProduct(VectorType &x, VectorType &y);

	// yxNRM2: sum( conj(x) * x )
	T VectorNorm(VectorType &x);

	/*
	 * BLAS Level 2
	 */

	//NOTE: Matrices are supposed to be in col-major (fortran) format
	// xGEMV: dst = dstScaling * dst + srcScaling * sum( matrix(i, j) * vector(i), i)
	void MultiplyMatrixVector(MatrixTranspose transpose, MatrixType &matrix, T srcScaling, VectorType &src, T dstScaling, VectorType &dst);
	void MultiplyMatrixVector(MatrixType &matrix, VectorType &src, VectorType &dst)
	{
		MultiplyMatrixVector(MatrixTranspose::None, matrix, 1.0, src, 0.0, dst);
	}

	//NOTE: Matrices are supposed to be in a special storage format (see zhbmv documentation for details)
	// xHBMV: dest = alpha * matrix * source + beta * dest
	void MultiplyMatrixVectorBandedHermitian(MatrixHermitianStorage storage, const MatrixType &matrix, cplx alpha, const VectorType &source, cplx beta, VectorType &dest);

	// xTBMV: in place matrix-vector multiplication for triangular matrices
	void MultiplyMatrixVectorBandedTriangular(MatrixHermitianStorage storage, MatrixTranspose transpose, MatrixDiagonal unitDiagonal, const MatrixType &matrix, VectorType &vector);

	//NOTE: Matrices are supposed to be in a special storage format (see zhbmv documentation for details)
	// xTBSV: Triangular backsubstitution of banded matrices
	void SolveMatrixVectorBandedTriangular(MatrixHermitianStorage storage, MatrixTranspose transpose, MatrixDiagonal unitDiagonal, const MatrixType &matrix, VectorType &vector);

	
	/*
	 * BLAS Level 3
	 */

	//NOTE: Matrices are supposed to be in col-major (fortran) format
	// xGEMM: dst = dstScaling * dst + srcScaling * sum( op(a)(i, j) *  op(b)(k, i), i)
	void MultiplyMatrixMatrix(MatrixTranspose transposeA, MatrixTranspose transposeB, T srcScaling, MatrixType &a, MatrixType &b, T dstScaling, MatrixType &dst);
	void MultiplyMatrixMatrix(MatrixType &a, MatrixType &b, MatrixType &dst)
	{
		MultiplyMatrixMatrix(MatrixTranspose::None, MatrixTranspose::None, 1.0, a, b, 0.0, dst);
	}

private:
	// Precondition checks to cotrol that valid parameters have been passed to the 
	// BLAS routines
	void PreconditionCopyVector(VectorType &src, VectorType &dst);
	void PreconditionScaleVector(VectorType &vector, T scaling);
	void PreconditionAddVector(VectorType &src, T scaling, VectorType &dst);
	void PreconditionInnerProduct(VectorType &x, VectorType &y);
	void PreconditionVectorNorm(VectorType &x);
	void PreconditionMultiplyMatrixVector(MatrixTranspose transpose, MatrixType &matrix, T srcScaling, VectorType &src, T dstScaling, VectorType &dst);
	void PreconditionMultiplyMatrixMatrix(MatrixTranspose transposeA, MatrixTranspose transposeB, T srcScaling, MatrixType &a, MatrixType &b, T dstScaling, MatrixType &dst);
	void PreconditionMultiplyMatrixVectorBandedHermitian(MatrixHermitianStorage storage, const MatrixType &matrix, cplx alpha, const VectorType &source, cplx beta, VectorType &dest);
	void PreconditionSolveMatrixVectorBandedTriangular(MatrixHermitianStorage storage, MatrixTranspose transpose, MatrixDiagonal unitDiagonal, const MatrixType &matrix, VectorType &vector);
	void PreconditionMultiplyMatrixVectorBandedTriangular(MatrixHermitianStorage storage, MatrixTranspose transpose, MatrixDiagonal unitDiagonal, const MatrixType &matrix, VectorType &vector);
};


/* 
 * Check wheter all parameters are valid to the BLAS functions. 
 * This is type independent, and need only be written once
 */

template<class T>
void BLAS<T>::PreconditionCopyVector(VectorType &src, VectorType &dst)
{
	BZPRECONDITION(src.extent(0) == dst.extent(0));
}

// xSCAL: vector *= scaling
template<class T>
void BLAS<T>::PreconditionScaleVector(VectorType &vector, T scaling)
{
}

// xAXPY: dst += scaling * src
template<class T>
void BLAS<T>::PreconditionAddVector(VectorType &src, T scaling, VectorType &dst)
{
	BZPRECONDITION(src.extent(0) == dst.extent(0));
}

// xDOTy: sum( conj(x) * y )
template<class T>
void BLAS<T>::PreconditionInnerProduct(VectorType &x, VectorType &y)
{
	BZPRECONDITION(x.extent(0) == y.extent(0));
}

// xDOTy: sum( conj(x) * y )
template<class T>
void BLAS<T>::PreconditionVectorNorm(VectorType &x)
{
}

//NOTE: Matrices are supposed to be in col-major (fortran) format
// xGEMV: sum( matrix(i, j) * vector(i), i)
template<class T>
void BLAS<T>::PreconditionMultiplyMatrixVector(MatrixTranspose transpose, MatrixType &matrix, T srcScaling, VectorType &src, T dstScaling, VectorType &dst)
{
#ifdef BZ_DEBUG
	int rows = matrix.extent(1);
	int cols = matrix.extent(0);

	if (transpose == MatrixTranspose::None)
	{
		BZPRECONDITION(cols == src.extent(0));
		BZPRECONDITION(rows == dst.extent(0));
	}
	else
	{
		BZPRECONDITION(cols == dst.extent(0));
		BZPRECONDITION(rows == src.extent(0));
	}
	BZPRECONDITION(matrix.stride(1) == 1);
#endif
}

//NOTE: Matrices are supposed to be in col-major (fortran) format
// xGEMM: sum( a(i, j) *  b(k, i), i)
template<class T>
void BLAS<T>::PreconditionMultiplyMatrixMatrix(MatrixTranspose transposeA, MatrixTranspose transposeB, T srcScaling, MatrixType &a, MatrixType &b, T dstScaling, MatrixType &dst)
{
#ifdef BZ_DEBUG
	int rowsA = a.extent(1);
	int colsA = a.extent(0);
	int rowsB = b.extent(1);
	int colsB = b.extent(0);
	int rowsDst = dst.extent(1);
	int colsDst = dst.extent(0);

	int opRowsA;
	int opColsA;
	int opRowsB;
	int opColsB;
	if (transposeA == MatrixTranspose::None)
	{
		opRowsA = rowsA;
		opColsA = colsA;
	}
	else
	{
		opRowsA = colsA;
		opColsA = rowsA;
	}

	if (transposeB == MatrixTranspose::None)
	{
		opRowsB = rowsB;
		opColsB = colsB;
	}
	else
	{
		opRowsB = colsB;
		opColsB = rowsB;
	}

	BZPRECONDITION(opRowsA == rowsDst);
	BZPRECONDITION(opColsA == opRowsB);
	BZPRECONDITION(opColsB == colsDst);


	BZPRECONDITION(a.stride(1) == 1);
	BZPRECONDITION(b.stride(1) == 1);
#endif
}

//xHBMV Matrix mutliply for banded hermitian matrices. See zhbmv for details about storage format
template<class T>
inline void BLAS<T>::PreconditionMultiplyMatrixVectorBandedHermitian(MatrixHermitianStorage storage, const MatrixType &matrix, cplx alpha, const VectorType &source, cplx beta, VectorType &dest)
{
	BZPRECONDITION(matrix.stride(1) == 1);
	BZPRECONDITION(matrix.extent(0) == source.extent(0));
	BZPRECONDITION(matrix.extent(0) == dest.extent(0));
}

// xTBMV: in place matrix-vector multiplication for triangular matrices
template<class T>
inline void BLAS<T>::PreconditionMultiplyMatrixVectorBandedTriangular(MatrixHermitianStorage storage, MatrixTranspose transpose, MatrixDiagonal unitDiagonal, const MatrixType &matrix, VectorType &vector)
{
	BZPRECONDITION(matrix.stride(1) == 1);
	BZPRECONDITION(matrix.extent(0) == vector.extent(0));
}

// xTBSV: Triangular backsubstitution of banded matrices
template<class T>
inline void BLAS<T>::PreconditionSolveMatrixVectorBandedTriangular(MatrixHermitianStorage storage, MatrixTranspose transpose, MatrixDiagonal unitDiagonal, const MatrixType &matrix, VectorType &vector)
{
	BZPRECONDITION(matrix.stride(1) == 1);
	BZPRECONDITION(matrix.extent(0) == vector.extent(0));
}


/* std::complex< double > implementation */

// xCOPY: dst = src
template<>
inline void BLAS<cplx>::CopyVector(VectorType &src, VectorType &dst)
{
	PreconditionCopyVector(src, dst);

	BLAS_NAME(zcopy)(src.extent(0), src.data(), src.stride(0), dst.data(), dst.stride(0));
}

// xSCAL: vector *= scaling
template<>
inline void BLAS<cplx>::ScaleVector(VectorType &vector, cplx scaling)
{
	PreconditionScaleVector(vector, scaling);

	BLAS_NAME(zscal)(vector.extent(0), &scaling, vector.data(), vector.stride(0));
}

// xAXPY: dst += scaling * src
template<>
inline void BLAS<cplx>::AddVector(VectorType &src, cplx scaling, VectorType &dst)
{
	PreconditionAddVector(src, scaling, dst);

	BLAS_NAME(zaxpy)(src.extent(0), &scaling, src.data(), src.stride(0), dst.data(), dst.stride(0));
}

// xDOTy: sum( conj(x) * y )
template<>
inline cplx BLAS<cplx>::InnerProduct(VectorType &x, VectorType &y)
{
	PreconditionInnerProduct(x, y);

	cplx value;
	BLAS_NAME(zdotc_sub)(x.extent(0), x.data(), x.stride(0), y.data(), y.stride(0), &value);
	return value;
}

// xDOTy: sum( conj(x) * y )
template<>
inline cplx BLAS<cplx>::VectorNorm(VectorType &x)
{
	PreconditionVectorNorm(x);

	return BLAS_NAME(dznrm2)(x.extent(0), x.data(), x.stride(0));
}

//NOTE: Matrices are supposed to be in col-major (fortran) format
// xGEMV: sum( matrix(i, j) * vector(i), i)
template<>
inline void BLAS<cplx>::MultiplyMatrixVector(MatrixTranspose transpose, MatrixType &matrix, cplx srcScaling, VectorType &src, cplx dstScaling, VectorType &dst)
{
	PreconditionMultiplyMatrixVector(transpose, matrix, srcScaling, src, dstScaling, dst);
	
	int rows = matrix.extent(1);
	int cols = matrix.extent(0);

	CBLAS_TRANSPOSE trans = (CBLAS_TRANSPOSE)transpose;

	BLAS_NAME(zgemv)(CblasColMajor, trans, rows, cols, &srcScaling, 
		matrix.data(), matrix.stride(0), src.data(), src.stride(0), 
		&dstScaling, dst.data(), dst.stride(0));
}

//NOTE: Matrices are supposed to be in col-major (fortran) format
// xGEMM: sum( a(i, j) *  b(k, i), i)
template<>
inline void BLAS<cplx>::MultiplyMatrixMatrix(MatrixTranspose transposeA, MatrixTranspose transposeB, cplx srcScaling, MatrixType &a, MatrixType &b, cplx dstScaling, MatrixType &dst)
{
	PreconditionMultiplyMatrixMatrix(transposeA, transposeB, srcScaling, a, b, dstScaling, dst);
	
	int rowsA = a.extent(1);
	int rowsB = b.extent(1);
	int colsDst = dst.extent(0);

	CBLAS_TRANSPOSE transA = (CBLAS_TRANSPOSE)transposeA;
	CBLAS_TRANSPOSE transB = (CBLAS_TRANSPOSE)transposeB;

	BLAS_NAME(zgemm)(CblasColMajor, transA, transB, rowsA, rowsB, colsDst, 
		&srcScaling, a.data(), a.stride(0), b.data(), b.stride(0), 
		&dstScaling, dst.data(), dst.stride(0));
}

//xHBMV Matrix mutliply for banded hermitian matrices. See zhbmv for details about storage format
template<>
void inline BLAS<cplx>::MultiplyMatrixVectorBandedHermitian(MatrixHermitianStorage storage, const MatrixType &matrix, cplx alpha, const VectorType &source, cplx beta, VectorType &dest)
{
	PreconditionMultiplyMatrixVectorBandedHermitian(storage, matrix, alpha, source, beta, dest);

	int N = matrix.extent(0);
	int LDA = matrix.extent(1);
	int K = LDA - 1;
	int incX = source.stride(0);
	int incY = dest.stride(0);

	CBLAS_UPLO uplo = (CBLAS_UPLO)storage;

	BLAS_NAME(zhbmv)(CblasColMajor, uplo, N, K, &alpha, matrix.data(), LDA, source.data(), incX, &beta, dest.data(), incY);
}

// xTBMV: in place matrix-vector multiplication for triangular matrices
template<>
inline void BLAS<cplx>::MultiplyMatrixVectorBandedTriangular(MatrixHermitianStorage storage, MatrixTranspose transpose, MatrixDiagonal unitDiagonal, const MatrixType &matrix, VectorType &vector)
{
	PreconditionMultiplyMatrixVectorBandedTriangular(storage, transpose, unitDiagonal, matrix, vector);

	int k = matrix.extent(1)-1;
	int N = matrix.extent(0);
	int lda = matrix.stride(0);
	int incx = vector.stride(0);

	CBLAS_UPLO uplo = (CBLAS_UPLO)storage;
	CBLAS_TRANSPOSE transA = (CBLAS_TRANSPOSE)transpose;
	CBLAS_DIAG diag = (CBLAS_DIAG)unitDiagonal;

	BLAS_NAME(ztbmv)(CblasColMajor, uplo, transA, diag, N, k, matrix.data(), lda, vector.data(), incx);
}


// xTBSV: Triangular backsubstitution of banded matrices
template<>
inline void BLAS<cplx>::SolveMatrixVectorBandedTriangular(MatrixHermitianStorage storage, MatrixTranspose transpose, MatrixDiagonal unitDiagonal, const MatrixType &matrix, VectorType &vector)
{
	PreconditionSolveMatrixVectorBandedTriangular(storage, transpose, unitDiagonal, matrix, vector);

	int k = matrix.extent(1)-1;
	int N = matrix.extent(0);
	int lda = matrix.stride(0);
	int incx = vector.stride(0);

	CBLAS_UPLO uplo = (CBLAS_UPLO)storage;
	CBLAS_TRANSPOSE transA = (CBLAS_TRANSPOSE)transpose;
	CBLAS_DIAG diag = (CBLAS_DIAG)unitDiagonal;

	BLAS_NAME(ztbsv)(CblasColMajor, uplo, transA, diag, N, k, matrix.data(), lda, vector.data(), incx);
}

}} //Namespaces

#endif

