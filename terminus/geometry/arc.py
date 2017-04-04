"""
Copyright (C) 2017 Open Source Robotics Foundation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import math

from geometry.point import Point
from geometry.circle import Circle


class Arc(object):

    def __init__(self, start_point, theta, radius, angular_length):
        """
        start_point: The point in the circumference where the arc starts
        theta: The heading of the tangent in start_point
        radius: The radius of the circular arc
        angular_length: The angle formed between then center -> start point
        and center -> end point. If the angular_length is > 0 the arc direction
        is considered counter-clockwise
        """
        self._start_point = start_point
        self._theta = theta
        self._radius = radius
        self._angular_length = angular_length
        self._end_point = self._compute_point_at(angular_length)

    def start_point(self):
        return self._start_point

    def end_point(self):
        return self._end_point

    def start_heading(self):
        return self._theta

    def end_heading(self):
        return self._theta + self._angular_length

    def theta(self):
        return self._theta

    def radius(self):
        return self._radius

    def angular_length(self):
        return self._angular_length

    def center_point(self):
        """
        Answers the point that is the center of the circular arc
        """
        theta_in_radians = math.radians(self._theta)
        direction_multiplier = math.copysign(1, self._angular_length)
        vector = Point(-self._radius * direction_multiplier * math.sin(theta_in_radians),
                       self._radius * direction_multiplier * math.cos(theta_in_radians))
        return self._start_point + vector

    def length(self):
        """
        The length of the perimeter of the arc
        """
        return abs(math.pi * self._radius * self._angular_length / 180.0)

    def includes_point(self, point, buffer=0.001):
        """
        Answer if a given point is part of the arc's perimeter. Allow to
        parametrize with a given buffer to contemplate rounding errors
        """
        center = self.center_point()
        center_start = self._start_point - center
        center_point = point - center
        if abs(center_point.norm() - self._radius) > buffer:
            return False
        angle_between_vectors = math.degrees(center_start.angle(center_point))
        if angle_between_vectors == 0:
            return True
        return ((angle_between_vectors < 0) == (self._angular_length < 0)) and abs(angle_between_vectors) <= abs(self._angular_length)

    def extend(self, distance):
        """
        Extend the arc by a given distance, following the arc's direction
        """
        angular_delta = 180 * distance / (math.pi * self._radius)
        return Arc(self._start_point, self._theta, self._radius, self._angular_length + angular_delta)

    def point_at_offset(self, offset):
        """
        Returns a point in the arc taken as an offset from the start of the arc.
        """
        if offset > self.length():
            raise ValueError("Offset ({0})is greater than arc length ({1})".format(offset, self.length()))
        angular_offset = math.copysign(offset, self._angular_length) * 180 / (math.pi * self._radius)
        return self._compute_point_at(angular_offset)

    def offset_for_point(self, point):
        """
        Answer how far is a given point from the start of the arc, measured as
        a distance on the arc's perimeter.
        """
        angle = self._angular_offset_for_point(point)
        return abs(math.pi * self._radius * angle / 180.0)

    def line_string_points(self, step=1):
        """
        Return a collection of points used to interpolate the arc.
        """
        points = []
        length = self.length()
        last_point = length - step
        traversed = 0
        while traversed <= last_point:
            points.append(self.point_at_offset(traversed))
            traversed += step
        if length - traversed > step / 2:
            points.append(self.point_at_offset(traversed))
        points.append(self.end_point().clone())
        return points

    def heading_at_offset(self, offset):
        """
        Answer the heading of a point at a given offset.
        """
        if offset > self.length():
            raise ValueError("Offset ({0}) is greater than segment length ({1})".format(offset, self.length()))
        angular_offset = math.copysign(offset, self._angular_length) * 180 / (math.pi * self._radius)
        return self._theta + angular_offset

    def intersection(self, other):
        circle1 = Circle(self.center_point(), self.radius)
        circle2 = Circle(other.center_point(), other.radius)
        if circle1.intersection(circle2) is None:
            return None
        else:
            intersections = []
            for point in circle1.intersection(circle2):
                if self.includes_point(point) and other.includes_point(point):
                    intersection.append(point)
            return intersections

    def _compute_point_at(self, angular_offset):
        theta_in_radians = math.radians(self._theta)
        angular_length_in_radians = math.radians(angular_offset)
        direction_multiplier = math.copysign(1, angular_offset)
        start_end_angle = theta_in_radians + angular_length_in_radians
        start_end_vector = Point(self._radius * direction_multiplier * (math.sin(start_end_angle) - math.sin(theta_in_radians)),
                                 self._radius * direction_multiplier * (math.cos(theta_in_radians) - math.cos(start_end_angle)))
        return self._start_point + start_end_vector

    def _angular_offset_for_point(self, point):
        if not self.includes_point(point):
            raise ValueError("Point {0} is not included in line segment".format(point))
        center = self.center_point()
        center_start = self._start_point - center
        center_point = point - center
        return math.degrees(center_start.angle(center_point))

    def __eq__(self, other):
        return self._start_point == other._start_point and \
            self._theta == other._theta and \
            self._radius == other._radius and \
            self._angular_length == other._angular_length

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._start_point, self._theta, self._radius, self._angular_length))

    def __repr__(self):
        return "Arc({0}, {1}, {2}, {3})".format(self._start_point, self._theta, self._radius, self._angular_length)
