
// Boost Includes ==============================================================
#include <boost/python.hpp>
#include <boost/cstdint.hpp>

// Includes ====================================================================
#include <finitediff/cranknicholsonpropagator.h>
#include <finitediff/finitedifferencehelper.h>

// Using =======================================================================
using namespace boost::python;

// Module ======================================================================
void Export_python_cranknicholson()
{
    class_< CrankNicholsonPropagator<1>, boost::noncopyable >("CrankNicholsonPropagator_1", init<  >())
        .def("MultiplyKineticEnergyOperator", &CrankNicholsonPropagator<1>::MultiplyKineticEnergyOperator)
        .def("AdvanceStep", &CrankNicholsonPropagator<1>::AdvanceStep)
        .def("SetupStep", &CrankNicholsonPropagator<1>::SetupStep)
        .def("ApplyConfigSection", &CrankNicholsonPropagator<1>::ApplyConfigSection)
        .def("GetLaplacianBlasBanded", &CrankNicholsonPropagator<1>::GetLaplacianBlasBanded)
        .def("GetLaplacianDistributedBanded", &CrankNicholsonPropagator<1>::GetLaplacianDistributedBanded)
        .def("GetLaplacianFull", &CrankNicholsonPropagator<1>::GetLaplacianFull)
        .def("GetBackwardPropagationLapackBanded", &CrankNicholsonPropagator<1>::GetBackwardPropagationLapackBanded)
    ;

    class_< CrankNicholsonPropagator<2>, boost::noncopyable >("CrankNicholsonPropagator_2", init<  >())
        .def("MultiplyKineticEnergyOperator", &CrankNicholsonPropagator<2>::MultiplyKineticEnergyOperator)
        .def("AdvanceStep", &CrankNicholsonPropagator<2>::AdvanceStep)
        .def("SetupStep", &CrankNicholsonPropagator<2>::SetupStep)
        .def("ApplyConfigSection", &CrankNicholsonPropagator<2>::ApplyConfigSection)
        .def("GetLaplacianBlasBanded", &CrankNicholsonPropagator<2>::GetLaplacianBlasBanded)
        .def("GetLaplacianDistributedBanded", &CrankNicholsonPropagator<2>::GetLaplacianDistributedBanded)
        .def("GetLaplacianFull", &CrankNicholsonPropagator<2>::GetLaplacianFull)
        .def("GetBackwardPropagationLapackBanded", &CrankNicholsonPropagator<2>::GetBackwardPropagationLapackBanded)
    ;

    class_< CrankNicholsonPropagator<3>, boost::noncopyable >("CrankNicholsonPropagator_3", init<  >())
        .def("MultiplyKineticEnergyOperator", &CrankNicholsonPropagator<3>::MultiplyKineticEnergyOperator)
        .def("AdvanceStep", &CrankNicholsonPropagator<3>::AdvanceStep)
        .def("SetupStep", &CrankNicholsonPropagator<3>::SetupStep)
        .def("ApplyConfigSection", &CrankNicholsonPropagator<3>::ApplyConfigSection)
        .def("GetLaplacianBlasBanded", &CrankNicholsonPropagator<3>::GetLaplacianBlasBanded)
        .def("GetLaplacianDistributedBanded", &CrankNicholsonPropagator<3>::GetLaplacianDistributedBanded)
        .def("GetLaplacianFull", &CrankNicholsonPropagator<3>::GetLaplacianFull)
        .def("GetBackwardPropagationLapackBanded", &CrankNicholsonPropagator<3>::GetBackwardPropagationLapackBanded)
    ;

    class_< CrankNicholsonPropagator<4>, boost::noncopyable >("CrankNicholsonPropagator_4", init<  >())
        .def("MultiplyKineticEnergyOperator", &CrankNicholsonPropagator<4>::MultiplyKineticEnergyOperator)
        .def("AdvanceStep", &CrankNicholsonPropagator<4>::AdvanceStep)
        .def("SetupStep", &CrankNicholsonPropagator<4>::SetupStep)
        .def("ApplyConfigSection", &CrankNicholsonPropagator<4>::ApplyConfigSection)
        .def("GetLaplacianBlasBanded", &CrankNicholsonPropagator<4>::GetLaplacianBlasBanded)
        .def("GetLaplacianDistributedBanded", &CrankNicholsonPropagator<4>::GetLaplacianDistributedBanded)
        .def("GetLaplacianFull", &CrankNicholsonPropagator<4>::GetLaplacianFull)
        .def("GetBackwardPropagationLapackBanded", &CrankNicholsonPropagator<4>::GetBackwardPropagationLapackBanded)
    ;

    class_< FiniteDifferenceHelper, boost::noncopyable >("FiniteDifferenceHelper", init<  >())
        .def("Setup", &FiniteDifferenceHelper::Setup)
        .def("FindDifferenceCoefficients", &FiniteDifferenceHelper::FindDifferenceCoefficients)
        .def("SetupLaplacianBlasBanded", &FiniteDifferenceHelper::SetupLaplacianBlasBanded)
    ;

}

