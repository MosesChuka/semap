#!/usr/bin/env python
import roslib; roslib.load_manifest('spatial_db')

import rospy
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, backref

from geoalchemy2.types import Geometry
from geoalchemy2.elements import WKTElement, WKBElement, RasterElement, CompositeElement
from geoalchemy2.functions import ST_Distance, ST_AsText
from geoalchemy2.compat import buffer, bytes
from postgis_functions import *

from sets import Set
from geometry_msgs.msg import Point 
from geometry_msgs.msg import Point32 
from geometry_msgs.msg import Pose2D 
from geometry_msgs.msg import Pose 
from geometry_msgs.msg import PoseStamped 
from geometry_msgs.msg import Polygon 
from mesh_msgs.msg import TriangleMesh, TriangleIndices
from mesh_msgs.msg import PolygonMesh, PolygonIndices
from spatial_db_msgs.msg import PolygonMesh as ROSPolygonMesh
from spatial_db_msgs.msg import Point2DModel, Point3DModel, Pose2DModel, Pose3DModel, Polygon2DModel, Polygon3DModel, TriangleMesh3DModel, PolygonMesh3DModel
from spatial_db_msgs.msg import ObjectDescription 
from spatial_db_msgs.msg import ObjectInstance

from numpy import radians
from tf.transformations import quaternion_matrix, random_quaternion, quaternion_from_matrix, euler_from_matrix, euler_matrix

def fromPoint2D(point):
  return WKTElement('POINT(%f %f %f)' % (point.x, point.y, 0.0))

def toPoint2D(geometry, is_text = False):
  if not is_text:
    geometry = db().execute(ST_AsText(geometry)).scalar()
  values = [float(x) for x in geometry.strip('POINT Z(').strip(')').split(' ')]
  point = Point()
  point.x = values[0]# + pose.position.x
  point.y = values[1]# + pose.position.y
  point.z = values[2]# + pose.position.z
  return point

def fromPolygon2D(polygon):
  prefix = 'POLYGON(('
  infix=''
  postfix = '%f %f %f))' % ( polygon.points[0].x, polygon.points[0].y, 0.0)
  for point in polygon.points:
    infix = infix + '%f %f %f,' % ( point.x, point.y, 0.0)
  return WKTElement(prefix + infix + postfix)

def toPolygon2D(geometry, is_text = False):
  if not is_text:
    geometry = db().execute(ST_AsText(geometry)).scalar()
  polygon = geometry.strip('POLYGON Z((').strip('))').split(',')
  ros = Polygon()
  for point in polygon[0:len(polygon)-1]:
    values = [float(x) for x in point.split(' ')]
    ros.points.append(Point32(values[0],values[1], 0.0))
  return ros

# 3D Geometry

def fromPoint3D(geometry:
  return WKTElement( 'POINT(%f %f %f)' % (model.geometry.x, model.geometry.y, model.geometry.z) )

def toPoint3D(geometry, is_text = False):
  if not is_text:
    geometry = db().execute(ST_AsText(geometry)).scalar()
  values =  [float(x) for x in geometry.strip('POINT Z(').strip(')').split(' ')]
  point = Point()
  point.x = values[0]
  point.y = values[1]
  point.z = values[2]
  return point

def fromPolygon3D(geometry):
  prefix = 'POLYGON(('
  infix=''
  postfix = '%f %f %f))' % ( geometry.points[0].x, geometry.points[0].y, geometry.points[0].z)
  for point in geometry.points:
    infix = infix + '%f %f %f,' % ( point.x, point.y, point.z)
  return WKTElement(prefix + infix + postfix)

def toPolygon3D(geometry, is_text = False):
  if not is_text:
      geometry = db().execute(ST_AsText(geometry)).scalar()
  polygon = geometry.strip('POLYGON Z((').strip('))').split(',')
  ros = Polygon()
  for point in polygon[0:len(polygon)-1]:
    values =  [float(x) for x in point.split(' ')]
    ros.points.append(Point32(values[0],values[1],values[2]))
  return ros

def fromTriangleMesh3D(geometry):
  prefix = 'TIN('
  postfix = ')'
  triangles = geometry.triangles
  vertices = geometry.vertices
  triangle_strings = []
  for triangle in triangles:
    indices = triangle.vertex_indices
    triangle_strings.append('((%f %f %f, %f %f %f, %f %f %f, %f %f %f))' \
        % (vertices[indices[0]].x, vertices[indices[0]].y, vertices[indices[0]].z, \
         vertices[indices[1]].x, vertices[indices[1]].y, vertices[indices[1]].z, \
         vertices[indices[2]].x, vertices[indices[2]].y, vertices[indices[2]].z, \
         vertices[indices[0]].x, vertices[indices[0]].y, vertices[indices[0]].z))
  infix = ",".join(triangle_strings)
  return WKTElement(prefix + infix + postfix)

def toTriangleMesh3D(geometry, is_text = False):
  if not is_text:
    geometry = db().execute(ST_AsText(geometry)).scalar()

  mesh = TriangleMesh()
  triangles = geometry.split(')),')
  for triangle in triangles:
    index = []
    points = triangle.strip('TIN Z(((').strip('))').split(',')
    for point in points[0:len(points)-1]:
      values = [float(x) for x in point.split()]
      index.append(len(mesh.vertices)-1)
      point = Point()
      point.x = values[0]
      point.y = values[1]
      point.z = values[2]
      mesh.vertices.append(ros_point)

    indices = TriangleIndices()
    indices.vertex_indices = index
    mesh.triangles.append(indices)

  return mesh

def fromPolygonMesh3D(geometry):
  prefix = 'POLYHEDRALSURFACE('
  postfix = ')'
  polygon_strings = []
  for polygon in geometry.polygons:
    polygon_string = ''
    for index in polygon.vertex_indices:
      vertex =  geometry.vertices[index]
      polygon_string = polygon_string + '%f %f %f,' % ( vertex.x, vertex.y, vertex.z)
    vertex =  geometry.vertices[0]
    polygon_string= '(('+ polygon_string + '%f %f %f))' % ( vertex.x, vertex.y, vertex.z)
    polygon_strings.append(polygon_string)
  infix = ",".join(polygon_strings)
  return WKTElement(prefix + infix + postfix)

def toPolygonMesh3D(geometry, is_text = False):
  if not is_text:
    geometry = db().execute(ST_AsText(geometry)).scalar()

  mesh = PolygonMesh()
  polygons = geometry.split(')),')
  for polygon in polygons:
    index = []
    points = polygon.strip('POLYHEDRALSURFACE Z(((').strip('))').split(',')
    for point in points[0:len(points)-1]:
      values = [float(x) for x in point.split()]
      index.append(len(mesh.vertices)-1)
      point = Point()
      point.x = values[0]
      point.y = values[1]
      point.z = values[2]
      mesh.vertices.append(ros_point)

    indices = PolygonIndices()
    indices.vertex_indices = index
    mesh.polygons.append(indices)

  return mesh
