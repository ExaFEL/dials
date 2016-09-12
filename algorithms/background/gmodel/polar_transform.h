/*
 * polar_transform.h
 *
 *  Copyright (C) 2013 Diamond Light Source
 *
 *  Author: James Parkhurst
 *
 *  This code is distributed under the BSD license, a copy of which is
 *  included in the root directory of this package.
 */

#ifndef DIALS_ALGORITHMS_BACKGROUND_GMODEL_POLAR_TRANSFORM_H
#define DIALS_ALGORITHMS_BACKGROUND_GMODEL_POLAR_TRANSFORM_H

#include <dxtbx/model/beam.h>
#include <dxtbx/model/detector.h>
#include <dxtbx/model/goniometer.h>
#include <dials/array_family/scitbx_shared_and_versa.h>
#include <dials/error.h>

namespace dials { namespace algorithms {

  using dxtbx::model::Beam;
  using dxtbx::model::Panel;
  using dxtbx::model::Detector;
  using dxtbx::model::Goniometer;


  class PolarTransform {
  public:

    PolarTransform(
        const Beam &beam,
        const Panel &panel,
        const Goniometer &goniometer,
        std::size_t multiplier)
        : multiplier_(multiplier) {

      // Check input
      DIALS_ASSERT(multiplier > 0);

      // Set some image sizes
      vec2<std::size_t> image_size = panel.get_image_size();
      vec2<std::size_t> map_size   = image_size * multiplier;
      af::c_grid<2> map_grid(map_size[1], map_size[0]);
      DIALS_ASSERT(image_size[0] > 0);
      DIALS_ASSERT(image_size[1] > 0);

      // Save the image grid
      image_grid_ = af::c_grid<2>(image_size[1], image_size[0]);

      // Allocate map arrays
      image_xmap_ = af::versa<double, af::c_grid<2> >(map_grid);
      image_ymap_ = af::versa<double, af::c_grid<2> >(map_grid);

      // Setup x, y, z axis for transform
      vec3<double> s0 = beam.get_s0().normalize();
      vec3<double> m2 = goniometer.get_rotation_axis().normalize();
      vec3<double> zaxis = s0;
      vec3<double> yaxis = zaxis.cross(m2);
      vec3<double> xaxis = zaxis.cross(yaxis);

      // Generate polar coords from image pixels
      for (std::size_t j = 0; j < map_size[1]; ++j) {
        for (std::size_t i = 0; i < map_size[0]; ++i) {
          double ii = i / multiplier + ((i % multiplier) + 0.5) / ((float) multiplier);
          double jj = j / multiplier + ((j % multiplier) + 0.5) / ((float) multiplier);
          vec3<double> s1 = panel.get_pixel_lab_coord(vec2<double>(ii,jj)).normalize();
          double z = s1 * zaxis;
          double y = s1 * yaxis;
          double x = s1 * xaxis;
          image_xmap_(j, i) = std::acos(z);
          image_ymap_(j, i) = std::atan2(y, x);
        }
      }

      // Get the min/max x and y
      double map_xmin = image_xmap_[0];
      double map_xmax = image_xmap_[0];
      double map_ymin = image_ymap_[1];
      double map_ymax = image_ymap_[1];
      std::size_t map_xmin_ind = 0;
      std::size_t map_xmax_ind = 0;
      for (std::size_t i = 1; i < image_xmap_.size(); ++i) {
        if (image_xmap_[i] < map_xmin) map_xmin_ind = i;
        if (image_xmap_[i] > map_xmax) map_xmax_ind = i;
        if (image_xmap_[i] < map_xmin) map_xmin = image_xmap_[i];
        if (image_xmap_[i] > map_xmax) map_xmax = image_xmap_[i];
        if (image_ymap_[i] < map_ymin) map_ymin = image_ymap_[i];
        if (image_ymap_[i] > map_ymax) map_ymax = image_ymap_[i];
      }

      // Compute the polar grid x size
      int xind1 = (map_xmin_ind % (map_size[0])) / multiplier_;
      int yind1 = (map_xmin_ind / (map_size[0])) / multiplier_;
      double d1 = std::sqrt((xind1 - 0)*(xind1 - 0) + (yind1 - 0)*(yind1 - 0));
      double d2 = std::sqrt((xind1 - 0)*(xind1 - 0) + (yind1 - image_size[1])*(yind1 - image_size[1]));
      double d3 = std::sqrt((xind1 - image_size[0])*(xind1 - image_size[0]) + (yind1 - 0)*(yind1 - 0));
      double d4 = std::sqrt((xind1 - image_size[0])*(xind1 - image_size[0]) + (yind1 - image_size[1])*(yind1 - image_size[1]));
      std::size_t polar_xsize = (std::size_t)std::ceil(
          std::max(
            std::max(d1, d2),
            std::max(d3, d4)));
      std::size_t polar_ysize = (std::size_t) std::ceil((image_size[0] * image_size[1]) / polar_xsize);

      // Compute polar y grid size
      /* int xind2 = std::min((int)(image_size[0]-2), (int)(map_xmax_ind % (image_size[0]))); */
      /* int yind2 = std::min((int)(image_size[0]-2), (int)(map_xmax_ind / (image_size[1]))); */
      /* double t[4] = { */
      /*   image_ymap_(yind2,xind2), */
      /*   image_ymap_(yind2+1,xind2), */
      /*   image_ymap_(yind2,xind2+1), */
      /*   image_ymap_(yind2+1,xind2+1), */
      /* }; */
      /* double td = 0; */
      /* for (std::size_t j = 0; j < 4; ++j) { */
      /*   for (std::size_t i = 0; i < 4; ++i) { */
      /*     double tdd = std::abs(t[i] - t[j]); */
      /*     if (tdd > td) tdd = td; */
      /*   } */
      /* } */
      /* std::size_t polar_ysize = (std::size_t)std::ceil(2*scitbx::constants::pi / td); */
      polar_grid_ = af::c_grid<2>(polar_ysize, polar_xsize);

      // The polar grid limits
      double polar_xmin = map_xmin;
      double polar_xmax = map_xmax;
      double polar_xstep = (polar_xmax - polar_xmin) / polar_xsize;
      double polar_ymin = map_ymin;
      double polar_ymax = map_ymax;
      double polar_ystep = (polar_ymax - polar_ymin) / polar_ysize;

      // Convert polar coords to indices
      for (std::size_t j = 0; j < map_size[1]; ++j) {
        for (std::size_t i = 0; i < map_size[0]; ++i) {
          double px = image_xmap_(j,i);
          double py = image_ymap_(j,i);
          double pi = ((px - polar_xmin) / polar_xstep);
          double pj = ((py - polar_ymin) / polar_ystep);
          image_xmap_(j,i) = pi;
          image_ymap_(j,i) = pj;
        }
      }
    }

    af::versa< double, af::c_grid<2> > image_xmap() const {
      return image_xmap_;
    }

    af::versa< double, af::c_grid<2> > image_ymap() const {
      return image_ymap_;
    }

    af::versa< double, af::c_grid<2> > to_polar(
        const af::const_ref< double, af::c_grid<2> > &data) const {

      DIALS_ASSERT(data.accessor().all_eq(image_grid_));
      af::versa< double, af::c_grid<2> > data_out(polar_grid_);

      double fraction = 1.0 / (multiplier_ * multiplier_);
      for (std::size_t j = 0; j < image_grid_[0]; ++j) {
        for (std::size_t i = 0; i < image_grid_[1]; ++i) {
          for (std::size_t jj = 0; jj < multiplier_; ++jj) {
            for (std::size_t ii = 0; ii < multiplier_; ++ii) {
              std::size_t iii = i * multiplier_ + ii;
              std::size_t jjj = j * multiplier_ + jj;
              DIALS_ASSERT(jjj < image_xmap_.accessor()[0]);
              DIALS_ASSERT(iii < image_xmap_.accessor()[1]);
              double x = image_xmap_(jjj,iii);
              double y = image_ymap_(jjj,iii);
              int pj = (int)std::floor(y);
              int pi = (int)std::floor(x);
              if (pj >= 0 && pj < polar_grid_[0] && pi >= 0 && pi < polar_grid_[1]) {
                data_out(pj,pi) += data(j,i) * fraction;
              }
            }
          }
        }
      }

      return data_out;
    }

    af::versa< double, af::c_grid<2> > from_polar(
        const af::const_ref< double, af::c_grid<2> > &data) const {

      DIALS_ASSERT(data.accessor().all_eq(polar_grid_));
      af::versa< double, af::c_grid<2> > data_out(image_grid_);

      double fraction = 1.0 / (multiplier_ * multiplier_);
      for (std::size_t j = 0; j < image_grid_[0]; ++j) {
        for (std::size_t i = 0; i < image_grid_[1]; ++i) {
          for (std::size_t jj = 0; jj < multiplier_; ++jj) {
            for (std::size_t ii = 0; ii < multiplier_; ++ii) {
              std::size_t iii = i * multiplier_ + ii;
              std::size_t jjj = j * multiplier_ + jj;
              DIALS_ASSERT(jjj < image_xmap_.accessor()[0]);
              DIALS_ASSERT(iii < image_xmap_.accessor()[1]);
              double x = image_xmap_(jjj,iii);
              double y = image_ymap_(jjj,iii);
              int pj = (int)std::floor(y);
              int pi = (int)std::floor(x);
              if (pj >= 0 && pj < polar_grid_[0] && pi >= 0 && pi < polar_grid_[1]) {
                data_out(j,i) += data(pj,pi);
              }
            }
          }
        }
      }

      return data_out;
    }

  protected:

    std::size_t multiplier_;
    af::c_grid<2> image_grid_;
    af::c_grid<2> polar_grid_;
    af::versa< double, af::c_grid<2> > image_xmap_;
    af::versa< double, af::c_grid<2> > image_ymap_;

  };

}} // namespace dials::algorithms

#endif // DIALS_ALGORITHMS_BACKGROUND_GMODEL_POLAR_TRANSFORM_H