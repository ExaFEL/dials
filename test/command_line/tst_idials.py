from __future__ import division
from dials.array_family import flex # import dependency


class Test(object):

  def __init__(self):
    from os.path import join
    import libtbx.load_env
    try:
      dials_regression = libtbx.env.dist_path('dials_regression')
    except KeyError, e:
      print 'SKIP: dials_regression not configured'
      exit(0)

    self.path = join(dials_regression, "centroid_test_data")
    self.integration_test_data = join(dials_regression, "integration_test_data")

  def run(self):

    from os.path import join, exists
    from libtbx import easy_run
    import os

    # Run a few commands from stdin
    stdin_lines = [
      "import template=%s" % join(self.path, "centroid_####.cbf"),
      "find_spots",
      "index",
      "refine_bs",
      "reindex solution=22",
      "refine",
      "goto 5",
    ]

    easy_run.fully_buffered(
      'idials',
      stdin_lines=stdin_lines).raise_if_errors()
    print 'OK'

    # Check that state works
    stdin_lines = [
      "refine scan_varying=True",
      "integrate",
      "export",
      "goto 6",
      "integrate profile.fitting=False",
      "export",
    ]

    easy_run.fully_buffered('idials', stdin_lines=stdin_lines).raise_if_errors()

    print 'OK'

    # Check all the stuff we expect, exists
    assert exists("dials.state")
    assert exists("dials-1")
    assert exists("9_integrated.mtz")
    assert exists("11_integrated.mtz")
    assert exists("dials-1/1_import")
    assert exists("dials-1/2_find_spots")
    assert exists("dials-1/3_index")
    assert exists("dials-1/4_refine_bs")
    assert exists("dials-1/5_reindex")
    assert exists("dials-1/6_refine")
    assert exists("dials-1/7_refine")
    assert exists("dials-1/8_integrate")
    assert exists("dials-1/9_export")
    assert exists("dials-1/10_integrate")
    assert exists("dials-1/11_export")

    print 'OK'

if __name__ == '__main__':
  from dials.test import cd_auto
  with cd_auto(__file__):
    test = Test()
    test.run()