/*
 * bbox_calculator.cc
 *
 *  Copyright (C) 2013 Diamond Light Source
 *
 *  Author: James Parkhurst
 *
 *  This code is distributed under the BSD license, a copy of which is
 *  included in the root directory of this package.
 */
#include <boost/python.hpp>
#include <boost/python/def.hpp>
#include <dials/algorithms/integration/bbox_calculator.h>

namespace dials { namespace algorithms { namespace boost_python {

  using namespace boost::python;

  void export_bbox_calculator()
  {
    int6 (BBoxCalculator::*calculate_single)(
      vec3 <double>, double, std::size_t) const = 
        &BBoxCalculator::operator();
    flex_int6 (BBoxCalculator::*calculate_array) (
      const flex_vec3_double&, const flex_double &, std::size_t) const = 
        &BBoxCalculator::operator();
    void (BBoxCalculator::*calculate_reflection)(Reflection &) const = 
      &BBoxCalculator::operator();
    void (BBoxCalculator::*calculate_reflection_list)(
      ReflectionList &) const = &BBoxCalculator::operator();

    class_ <BBoxCalculator> ("BBoxCalculator", no_init)
      .def(init <const Beam&,
                 const Detector&,
                 const Goniometer&,
                 const Scan&,
                 double,
                 double > ((
        arg("beam"), 
        arg("detector"),
        arg("goniometer"),
        arg("scan"),
        arg("delta_divergence"),
        arg("delta_mosaicity"))))
      .def("__call__", calculate_single, (
        arg("s1"), arg("phi")))
      .def("__call__", calculate_array, (
        arg("s1"), arg("phi")))
      .def("__call__", calculate_reflection, (
        arg("reflection")))
      .def("__call__", calculate_reflection_list, (
        arg("reflections")));
  }

}}} // namespace = dials::algorithms::boost_python
