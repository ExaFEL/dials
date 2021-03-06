#!/usr/bin/env python
#
# reflection_predictor.py
#
#  Copyright (C) 2014 Diamond Light Source
#
#  Author: James Parkhurst
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.

from __future__ import absolute_import, division
import logging
logger = logging.getLogger(__name__)

from libtbx.phil import parse
from libtbx.utils import Sorry

# The phil parameters
phil_scope = parse('''

  prediction {

    d_min = None
      .type = float
      .help = "The maximum resolution limit"

    d_max = None
      .type = float
      .help = "The minimum resolution limit"

    margin = 1
      .type = int
      .help = "The margin to use to scan varying prediction"

    force_static = False
      .type = bool
      .help = "For scan-varying prediction force scan-static prediction"

    force_scan_varying = False
      .type = bool
      .help = "For scan-static prediction force scan-varying prediction"

    padding = 1.0
      .type = float(value_min=0)
      .help = "The padding in degrees"
  }

''')


class ReflectionPredictor(object):
  '''
  A reflection predictor that takes a number of experiments and does the proper
  prediction for each type of experiment.

  '''

  def __init__(self,
               experiment,
               dmin=None,
               dmax=None,
               margin=1,
               force_static=False,
               force_scan_varying=False,
               padding=0):
    '''
    Initialise a predictor for each experiment.

    :param experiment: The experiment to predict for
    :param dmin: The maximum resolution
    :param dmax: The minimum resolution
    :param margin: The margin of hkl to predict
    :param force_static: force scan varying prediction to be static
    :param force_scan_varying: force scan-static prediction to be scan-varying

    '''
    from dials.algorithms.spot_prediction import ScanStaticReflectionPredictor
    from dials.algorithms.spot_prediction import ScanVaryingReflectionPredictor
    from dials.algorithms.spot_prediction import StillsReflectionPredictor
    from dxtbx.imageset import ImageSweep
    from dials.array_family import flex

    if force_static and force_scan_varying:
      raise Sorry("Can not set both force_static and force_scan_varying")

    class Predictor(object):
      def __init__(self, name, func):
        self.name = name
        self.func = func
      def __call__(self):
        result = self.func()
        if dmax is not None:
          assert(dmax > 0)
          result.compute_d_single(experiment)
          mask = result['d'] > dmax
          result.del_selected(mask)
        return result

    # Check prediction to maximum resolution is possible
    wl = experiment.beam.get_wavelength()
    if dmin is not None and dmin < 0.5 * wl:
      raise Sorry("Prediction at d_min of {0} is not possible "
                  "with wavelength {1}".format(dmin, wl))

    # Select the predictor class
    if isinstance(experiment.imageset, ImageSweep):
      nsp = experiment.crystal.num_scan_points
      nim = experiment.scan.get_num_images()

      if force_scan_varying and nsp == 0:
        nsp = nim + 1
        A = [experiment.crystal.get_A() for i in range(nsp)]
        experiment.crystal.set_A_at_scan_points(A)

      if not force_static and nsp == nim + 1:
        predictor = ScanVaryingReflectionPredictor(
          experiment,
          dmin=dmin,
          margin=margin,
          padding=padding)
        A = [experiment.crystal.get_A_at_scan_point(i) for i in
               range(experiment.crystal.num_scan_points)]
        predict = Predictor(
          "scan varying prediction",
          lambda: predictor.for_ub(flex.mat3_double(A)))
      else:
        predictor = ScanStaticReflectionPredictor(
          experiment,
          dmin=dmin,
          padding=padding)
        predict = Predictor(
          "scan static prediction",
          lambda: predictor.for_ub(experiment.crystal.get_A()))
    else:
      predictor = StillsReflectionPredictor(
        experiment,
        dmin=dmin)

      predict = Predictor(
        "stills prediction",
        lambda: predictor.for_ub(experiment.crystal.get_A()))

    # Create and add the predictor class
    self._predict = predict

  def __call__(self):
    '''
    Predict all the observable reflections.

    :return: A reflection table

    '''
    logger.info('Prediction type: %s' % self._predict.name)
    table = self._predict()
    logger.info('Predicted %d reflections' % len(table))
    return table

  def predictor(self, index):
    '''
    Get the predictor for the given experiment index.

    :param index: The experiment index
    :return: The predictor

    '''
    return self._predict[index]
