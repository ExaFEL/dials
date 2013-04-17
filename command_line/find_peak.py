from __future__ import division
from dxtbx.sweep import SweepFactory
#from dials.scratch.luiso_s.to_dials_reg.func_fnd_pk import *

from dials.algorithms.peak_finding.lui_find_peak import *
import time

import numpy
def fnd_pk():
    import sys
    from dxtbx.format.Registry import Registry
    print len(sys.argv[1:]), "images given"
    tm = 2
    if len(sys.argv[1:]) == 1:
        print "2D peak find"
        filename = sys.argv[1:]
        sweep = SweepFactory.sweep(filename)

        array_2d = sweep.to_array()
        data3d = array_2d.as_numpy_array()
        data2d = numpy.copy(data3d[0, :, :])
        n_row = numpy.size(data2d[:, 0:1])
        n_col = numpy.size(data2d[0:1, :])
        print 'n_frm, n_row, n_col =', n_row, n_col

#        data2dsmoth = numpy.zeros_like(data2d)
#        diffdata2d = numpy.zeros_like(data2d)
#        data2d = numpy.copy(data2d)
        dif2d = numpy.zeros_like(data2d)
#        dif2d = find_mask_2d(data2d)
        n_blocks_x = 5
        n_blocks_y = 12
        col_block_size = n_col / n_blocks_x
        row_block_size = n_row / n_blocks_y

        print 'col_block_size, row_block_size =', col_block_size, row_block_size

        time1 = time.time()
        for tmp_block_x_pos in range(n_blocks_x):
            for tmp_block_y_pos in range(n_blocks_y):
                col_from = int(tmp_block_x_pos * col_block_size)
                col_to = int((tmp_block_x_pos + 1) * col_block_size)
                row_from = int(tmp_block_y_pos * row_block_size)
                row_to = int((tmp_block_y_pos + 1) * row_block_size)
                tmp_dat2d = numpy.copy(data2d[row_from:row_to, col_from:col_to])
                tmp_dif2d = find_mask_2d(tmp_dat2d, tm)
                dif2d[row_from:row_to, col_from:col_to] = tmp_dif2d[:, :]
#                dif2d[row_from:row_to, col_from:col_to] = find_mask_2d(data2d[row_from:row_to, col_from:col_to], tm)

        print 'time.time() =', time.time()
        time2 = time.time()
        time_dif = time2 - time1
        print time2, ' - ', time1, '=', time_dif
        time1 = time2

        dif_2d_ext = find_ext_mask_2d(dif2d)
        x_from_lst, x_to_lst, y_from_lst, y_to_lst = find_bound_2d(dif_2d_ext)





        for pos in range(len(x_from_lst)):
            print "x_from, x_to, y_from, y_to =" \
            , x_from_lst[pos], x_to_lst[pos], y_from_lst[pos], y_to_lst[pos]
        from matplotlib import pyplot as plt

        print 'time.time() =', time.time()
        time2 = time.time()
        time_dif = time2 - time1
        print time2, ' - ', time1, '=', time_dif
        time1 = time2


        plt.imshow(data2d, interpolation = "nearest", origin = 'lower')
        plt.show()

        plt.imshow(dif2d, interpolation = "nearest", origin = 'lower')
        plt.show()

        plt.imshow(dif_2d_ext, interpolation = "nearest", origin = 'lower')
        plt.show()

        from matplotlib import pylab, cm
        plt = pylab.imshow(data2d , vmin = 0, vmax = 1000, cmap = cm.Greys_r,
                       interpolation = 'nearest', origin = 'lower')
        pylab.scatter(x_from_lst, y_from_lst, marker = 'x')
        pylab.scatter(x_to_lst, y_to_lst, marker = 'x')
        pylab.show()

    elif len(sys.argv[1:]) > 1:
        print "3D peak find"
        filenames = sys.argv[1:]
        sweep = SweepFactory.sweep(filenames)

        array_3d = sweep.to_array()
        data3d = array_3d.as_numpy_array()
        n_frm = numpy.size(data3d[:, 0:1, 0:1])
        n_row = numpy.size(data3d[0:1, :, 0:1])
        n_col = numpy.size(data3d[0:1, 0:1, :])

        print "n_frm,n_row,n_col", n_frm, n_row, n_col

        #dif3d = numpy.zeros(n_row * n_col * n_frm , dtype = int).reshape(n_frm, n_row, n_col)

        dif3d = numpy.zeros_like(data3d)

        n_blocks_x = 5
        n_blocks_y = 12
        col_block_size = n_col / n_blocks_x
        row_block_size = n_row / n_blocks_y

        print 'col_block_size, row_block_size =', col_block_size, row_block_size

        time1 = time.time()
        for frm_tmp in range(n_frm):
            for tmp_block_x_pos in range(n_blocks_x):
                for tmp_block_y_pos in range(n_blocks_y):

                    col_from = int(tmp_block_x_pos * col_block_size)
                    col_to = int((tmp_block_x_pos + 1) * col_block_size)
                    row_from = int(tmp_block_y_pos * row_block_size)
                    row_to = int((tmp_block_y_pos + 1) * row_block_size)

                    tmp_dat2d = numpy.copy(data3d[frm_tmp, row_from:row_to, col_from:col_to])
                    tmp_dif = find_mask_2d(tmp_dat2d, tm)
                    dif3d[frm_tmp, row_from:row_to, col_from:col_to] = tmp_dif

            print 'time.time() =', time.time()
            time2 = time.time()
            time_dif = time2 - time1
            print time2, ' - ', time1, '=', time_dif
            time1 = time2


        dif_3d_ext = find_ext_mask_3d(dif3d)
        dif_3d_ext[0:1, :, :] = 0
        dif_3d_ext[(n_frm - 1):, :, :] = 0

        x_from_lst, x_to_lst, y_from_lst, y_to_lst, z_from_lst, z_to_lst = find_bound_3d(dif_3d_ext)

        for pos in range(len(x_from_lst)):
            print "x_from, x_to, y_from, y_to, z_from, z_to =" \
            , x_from_lst[pos], x_to_lst[pos], y_from_lst[pos], y_to_lst[pos], z_from_lst[pos], z_to_lst[pos]

        from matplotlib import pylab, cm
        plt = pylab.imshow(data3d[1, :, :] , vmin = 0, vmax = 1000, cmap = cm.Greys_r,
                       interpolation = 'nearest', origin = 'lower')
        pylab.scatter(x_from_lst, y_from_lst, marker = 'x')
        pylab.scatter(x_to_lst, y_to_lst, marker = 'x')
        pylab.show()
    else:
        print "No IMG file to load"

if __name__ == '__main__':
    fnd_pk()

