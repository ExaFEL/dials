
def calculate_threshold(sweep, trusted_range):
    from scipy.ndimage.measurements import histogram
    from thresholding import maximum_deviation
    import numpy

    threshold_list = []
    for i, flex_image in enumerate(sweep):

        # Get image as numpy array
        image = flex_image.as_numpy_array()

        # Cap pixels to within trusted range
        image.shape = -1
        ind = numpy.where(image < trusted_range[0])
        image[ind] = trusted_range[0]
        ind = numpy.where(image > trusted_range[1])
        image[ind] = trusted_range[1]

        # Histogram the pixels
        histo = histogram(image, trusted_range[0], trusted_range[1], trusted_range[1])
        histo = histo / numpy.sum(histo)

        # Calculate the threshold and add to list
        threshold = maximum_deviation(histo)
        threshold_list.append(threshold)

    # Return mean threshold
    return numpy.mean(threshold_list)


def select_strong_pixels(sweep, trusted_range):

    import numpy

    # Calculate the threshold
    print "Calculating a threshold."
    threshold = calculate_threshold(sweep, trusted_range)

    # Select only those pixels with counts > threshold
    print "Selecting pixels"
    image = sweep.to_array().as_numpy_array()
    mask = image >= threshold
    return image, mask

def group_pixels(mask):
    from scipy.ndimage.measurements import label, find_objects

    # Label the indices in the mask
    regions, nregions = label(mask)#, structure)

    # Get the bounding box of each object
    objects = find_objects(regions)

    # Return the list of objects
    return objects

def filter_objects(mask, objects, min_pixels):
    import numpy

    # Select objects with more pixels than min_pixels
    new_obj = []
    for obj in objects:
        ind = numpy.where(mask[obj] != 0)[0]
        if len(ind) >= min_pixels:
            new_obj.append(obj)
        else:
            mask[obj] = 0

    return new_obj


def direction_var(values, weights):
    import numpy
    from scitbx import matrix
    weights = numpy.array(weights)
    valx = numpy.array([x for x, y, z in values])
    valy = numpy.array([y for x, y, z in values])
    valz = numpy.array([z for x, y, z in values])

    # Calculate avergae x, y, z
    avrx = numpy.average(valx, weights=weights)
    avry = numpy.average(valy, weights=weights)
    avrz = numpy.average(valz, weights=weights)

    # Calculate mean direction vector
    s1m = matrix.col((avrx, avry, avrz)).normalize()

    # Calculate angles between vectors
    angles = []
    for s in values:
        angles.append(s1m.angle(s))

    # Calculate variance of angles
    angles = numpy.array(angles)
    var = numpy.dot(weights, (angles)**2)/numpy.sum(weights)
    return var

def centroid(image, mask, detector):
    from numpy import zeros, int32, argmax, where, average
    from scitbx.array_family import flex
    from scitbx import matrix
    import numpy

    var = []
    cent = []
    for obj in objects:
        xs = []
        ys = []
        zs = []
        s1s = []
        weights = []
        bbox = [obj[2].start, obj[2].stop,
                obj[1].start, obj[1].stop,
                obj[0].start, obj[0].stop]

        # Calcyulate beam vector for each point
        for i in range(bbox[4], bbox[5]):
            for s in range(bbox[2], bbox[3]):
                for f in range(bbox[0], bbox[1]):
                    if mask[i, s, f]:
                        s1 = matrix.col(detector.get_pixel_lab_coord((f+0.5, s+0.5)))
                        s1 = s1.normalize()
                        xs.append(f + 0.5)
                        ys.append(s + 0.5)
                        zs.append(i + 0.5)
                        s1s.append(s1)
                        weights.append(image[i, s ,f])

        v = direction_var(s1s, weights)
        var.append(v)
        avrx = average(xs, weights=weights)
        avry = average(ys, weights=weights)
        avrz = average(zs, weights=weights)
        cent.append((avrx, avry, avrz))

    # Return a list of centroids and variances
    return numpy.array(cent), numpy.array(var)


def calculate_sigma_beam_divergence(var):
    '''Calculate the beam divergence as the sum of centroid variance of the
    intensity weighted diffracted beam directions.'''
    from math import sqrt

    # Calculate the sum of s^2
    sum_variance = reduce(lambda x, y: x + y, var)

    # Return the beam divergence as the sum / num reflections
    return sqrt(sum_variance / len(var))


def find_nearest_neighbour(obs_xyz, reflections):
    from annlib_ext import AnnAdaptor
    from scitbx.array_family import flex
    from math import sqrt

    # Get the predicted coords
    pred_xyz = []
    for r in reflections:
        x = r.image_coord_px[0]
        y = r.image_coord_px[1]
        z = r.frame_number
        pred_xyz.append((x, y, z))

    # Create the KD Tree
    ann = AnnAdaptor(flex.double(pred_xyz).as_1d(), 3)

    ann.query(flex.double(obs_xyz).as_1d())

#    for i in xrange(len(ann.nn)):
#        print "Neighbor of {0}, index {1} distance {2}".format(
#        obs_xyz[i], ann.nn[i], sqrt(ann.distances[i]))

    return ann.nn, ann.distances


def filter_objects_by_distance(ref_index, distance2, max_distance):

    import numpy
    from math import sqrt

    # Only accept objects closer than max distance
    indices = []
    for i in range(len(ref_index)):
        if sqrt(distance2[i]) > max_distance:
            continue
        else:
            indices.append(i)

    return numpy.array(indices)


class FractionOfObservedIntensity:

    def __init__(self, z, zeta, scan):
        import numpy
        self.dphi = scan.get_oscillation()[1]
        self.tau = numpy.array([self.calc_tau(zz, scan) for zz in z])
        self.zeta = numpy.abs(numpy.array(zeta))

    def calc_tau(self, z, scan):
        phi = scan.get_angle_from_array_index(z)
        p0 = scan.get_angle_from_array_index(int(z))
        p1 = scan.get_angle_from_array_index(int(z)+1)
        t = phi - (p1 + p0) / 2.0
        return t

    def __call__(self, sigma_m):
        import numpy
        from math import sqrt, erf, log

        #for m in sigma_m: print m

        dphi2 = self.dphi / 2
        den = sqrt(2) * sigma_m / self.zeta

        a = (self.tau + dphi2) / den
        b = (self.tau - dphi2) / den

        a = numpy.array([erf(a[i]) for i in range(len(a))])
        b = numpy.array([erf(b[i]) for i in range(len(b))])
        r = (a - b) / (2 * self.dphi)
        return numpy.log(r)

class Likelihood:

    def __init__(self, R):
        self.R = R

    def __call__(self, sigma_m):
        import numpy
        r = self.R(sigma_m)
        p = numpy.sum(r)
        return -p

class Minimize:

    def __init__(self, z, zeta, sweep):
        from scitbx import simplex
        from scitbx.array_family import flex
        self.L = Likelihood(FractionOfObservedIntensity(z, zeta, sweep.get_scan()))

        starting_simplex=[]
        for ii in range(2):
            starting_simplex.append(flex.double([0.154*3.14159 / 180]))#flex.random_double(1))

        self.optimizer = simplex.simplex_opt(
            1, matrix=starting_simplex, evaluator=self, tolerance=1e-7)

    def target(self, sigma_m):
        return self.L(sigma_m)

    def __call__(self):
        return self.optimizer.get_solution()[0]

def calculate_sigma_mosaicity(z, zeta, sweep):

    #from scipy.optimize import minimize

    #L = Likelihood(FractionOfObservedIntensity(z, zeta, sweep.get_scan()))

    #return minimize(L, 1.0, method=Nelder-Mead)

    minimizer = Minimize(z, zeta, sweep)
    return minimizer()

if __name__ == '__main__':

    import os
    import libtbx.load_env
    from dials.util.nexus import NexusFile
    from glob import glob
    from dxtbx.sweep import SweepFactory
    from math import pi
    from scitbx import matrix

    try:
        dials_regression = libtbx.env.dist_path('dials_regression')
    except KeyError, e:
        print 'FAIL: dials_regression not configured'
        raise

    # The XDS values
    xds_sigma_d = 0.060
    xds_sigma_m = 0.154

    # Read the reflections file
    filename = os.path.join(dials_regression,
        'centroid_test_data', 'reflections.h5')
    handle = NexusFile(filename, 'r')

    # Get the reflection list
    print 'Reading reflections.'
    reflections = handle.get_reflections()
    print 'Read {0} reflections.'.format(len(reflections))

    # Read images
    template = os.path.join(dials_regression,
        'centroid_test_data', 'centroid_*.cbf')
    filenames = glob(template)

    # Load the sweep
    print 'Loading sweep'
    sweep = SweepFactory.sweep(filenames)
    print 'Loaded sweep of {0} images.'.format(len(sweep))

    # Select the strong pixels to use in the divergence calculation
    print 'Select the strong pixels from the images.'
    trusted_range = (0, 20000)
    image, mask = select_strong_pixels(sweep, trusted_range)

    # Putting pixels into groups
    print 'Putting pixels into groups'
    objects = group_pixels(mask)
    print 'Found {0} objects'.format(len(objects))

    print 'Filtering objects'
    min_pixels = 6
    objects = filter_objects(mask, objects, min_pixels)
    print '{0} remaining objects'.format(len(objects))

    print 'Calculating centroid and variance.'
    cent, var = centroid(image, mask, sweep.get_detector())

    print 'Find object nearest predicted reflection'
    ref_index, distance2 = find_nearest_neighbour(cent, reflections)

    print 'Filter objects by distance from nearest reflection.'
    max_distance = 2
    indices = filter_objects_by_distance(ref_index, distance2, max_distance)
    print '{0} remaining objects'.format(len(indices))

    print 'Calculate the e.s.d of the beam divergence'
    sigma_d = calculate_sigma_beam_divergence(var[indices])
    print 'Sigma_d = {0} deg'.format(sigma_d * 180.0 / pi)
    print 'XDS Sigma_d = {0} deg'.format(xds_sigma_d)

    # Calculate rotation angles
    phi = []
    for x, y, z in cent:
        phi.append(sweep.get_scan().get_angle_from_array_index(z))

    import numpy
    z_coord = numpy.array([zz for xx, yy, zz in cent])

    # Calculate the zetas
    s0 = matrix.col(sweep.get_beam().get_s0())
    m2 = matrix.col(sweep.get_goniometer().get_rotation_axis())
    zeta = []
    for x, y, z in cent:
        s1 = sweep.get_detector().get_pixel_lab_coord((x, y))
        s1 = matrix.col(s1).normalize() * s0.length()
        e1 = s1.cross(s0).normalize()
        zeta.append(m2.dot(e1))

    print 'Calculate the e.s.d of the mosaicity.'
    sigma_m = calculate_sigma_mosaicity(z_coord, zeta, sweep)
    print 'Sigma_m = {0} deg'.format(sigma_m * 180 / pi)
    print 'XDS Sigma_m = {0} deg'.format(xds_sigma_m)
