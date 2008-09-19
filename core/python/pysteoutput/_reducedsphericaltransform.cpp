
// Boost Includes ==============================================================
#include <boost/python.hpp>
#include <boost/cstdint.hpp>

// Includes ====================================================================
#include <transform/reducedspherical/reducedsphericaltools.h>
#include <transform/reducedspherical/reducedsphericaltransform.h>

// Using =======================================================================
using namespace boost::python;

// Module ======================================================================
void Export_python_reducedsphericaltransform()
{
    class_< ReducedSpherical::ReducedSphericalTools >("ReducedSphericalTools", init<  >())
        .def(init< const ReducedSpherical::ReducedSphericalTools& >())
        .def_readwrite("Algorithm", &ReducedSpherical::ReducedSphericalTools::Algorithm)
        .def("GetLMax", &ReducedSpherical::ReducedSphericalTools::GetLMax)
        .def("GetThetaGrid", &ReducedSpherical::ReducedSphericalTools::GetThetaGrid)
        .def("GetWeights", &ReducedSpherical::ReducedSphericalTools::GetWeights)
        .def("GetAssociatedLegendrePolynomial", &ReducedSpherical::ReducedSphericalTools::GetAssociatedLegendrePolynomial)
        .def("GetAssociatedLegendrePolynomialDerivative", &ReducedSpherical::ReducedSphericalTools::GetAssociatedLegendrePolynomialDerivative)
        .def("Initialize", &ReducedSpherical::ReducedSphericalTools::Initialize)
    ;

    class_< ReducedSpherical::ReducedSphericalTransform<2> >("ReducedSphericalTransform_2", init<  >())
        .def(init< const ReducedSpherical::ReducedSphericalTransform<2>& >())
        .def_readwrite("transform", &ReducedSpherical::ReducedSphericalTransform<2>::transform)
        .def("SetupStep", &ReducedSpherical::ReducedSphericalTransform<2>::SetupStep)
        .def("ForwardTransform", &ReducedSpherical::ReducedSphericalTransform<2>::ForwardTransform)
        .def("InverseTransform", &ReducedSpherical::ReducedSphericalTransform<2>::InverseTransform)
        .def("CreateSphericalHarmonicRepr", &ReducedSpherical::ReducedSphericalTransform<2>::CreateSphericalHarmonicRepr)
        .def("CreateAngularRepresentation", &ReducedSpherical::ReducedSphericalTransform<2>::CreateAngularRepresentation)
        .def("GetBaseRank", &ReducedSpherical::ReducedSphericalTransform<2>::GetBaseRank)
        .def("SetBaseRank", &ReducedSpherical::ReducedSphericalTransform<2>::SetBaseRank)
    ;

    class_< ReducedSpherical::ReducedSphericalTransform<3> >("ReducedSphericalTransform_3", init<  >())
        .def(init< const ReducedSpherical::ReducedSphericalTransform<3>& >())
        .def_readwrite("transform", &ReducedSpherical::ReducedSphericalTransform<3>::transform)
        .def("SetupStep", &ReducedSpherical::ReducedSphericalTransform<3>::SetupStep)
        .def("ForwardTransform", &ReducedSpherical::ReducedSphericalTransform<3>::ForwardTransform)
        .def("InverseTransform", &ReducedSpherical::ReducedSphericalTransform<3>::InverseTransform)
        .def("CreateSphericalHarmonicRepr", &ReducedSpherical::ReducedSphericalTransform<3>::CreateSphericalHarmonicRepr)
        .def("CreateAngularRepresentation", &ReducedSpherical::ReducedSphericalTransform<3>::CreateAngularRepresentation)
        .def("GetBaseRank", &ReducedSpherical::ReducedSphericalTransform<3>::GetBaseRank)
        .def("SetBaseRank", &ReducedSpherical::ReducedSphericalTransform<3>::SetBaseRank)
    ;

}

