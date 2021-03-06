# -*- coding: utf-8 -*-
"""GJK_playground

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1whIFgHq2NqaPAz55TKDLED5f47rFgXJG

Added a visualizer to double check the GJK algorithm works

Really need to clean this up

Very outdated file
"""

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
from matplotlib import pyplot as plt
import matplotlib.patches as patches
import numpy as np
import scipy.linalg
import pdb

# may not need
# !pip install ipywidgets

class Rectangle:

    def __init__(self, bottomleft_corner, width, height, angle=0, get_poly=True):
        """cjt is the center of rectangle, thought of as translation.
           may be more efficient to incorporate time into object"""
        self.angle = angle
        self.angle_rad = angle*np.pi/180
        # bottomleft_corner is defined with regards to angle=0 and rotates appropriately
        # clean this up as storing a lot 
        v1 = bottomleft_corner
        v2 = v1 + np.array([[width*np.cos(self.angle_rad)], [width*np.sin(self.angle_rad)]])
        v4 = v1 + np.array([[-height*np.sin(self.angle_rad)], [height*np.cos(self.angle_rad)]])
        v3 = v2 + v4 - v1
        self.vertices = [v1, v2, v3, v4]
        self.w = width
        self.h = height
        self.center = (self.vertices[0] + self.vertices[2]) / 2
        
        if get_poly:
            self.get_polyhedron()
        self.calcSupportVectors()       # used in collision

    def get_lineqns(self, two_points):
        # want ax + by = c from two pts
        # returns a, b, c
        # (y1-y2) * x + (x2-x1) * y + (x1-x2)*y1 + (y2-y1)*x1 = 0
        x1, y1 = two_points[0]
        x2, y2 = two_points[1]
        return y1-y2, x2-x1, (x1-x2)*-y1 - (y2-y1)*x1

    def get_Ab(self, adj_pairs):
        self.A = np.zeros((4, 2))
        self.b = np.zeros((4, 1))
        for i, pair in enumerate(adj_pairs):
            self.A[i][0], self.A[i][1], self.b[i] = self.get_lineqns(pair)
        self.A = -self.A
        self.b = -self.b    # flip sign to match literature for inequality

    def get_c(self):
        self.c = np.zeros((4, 2, 1))
        self.c[0] = self.vertices[0]
        self.c[1] = self.vertices[2]
        self.c[2] = self.vertices[2]
        self.c[3] = self.vertices[0]

    def get_polyhedron(self):
        adj_pairs = []
        for i in range(3):
            adj_pairs.append(self.vertices[i:(i+2)])
        adj_pairs.append([self.vertices[-1], self.vertices[0]])
        
        self.get_Ab(adj_pairs)
        self.get_c()

    def print_eqns_Ab(self):
        """To see paste into https://www.desmos.com/calculator
           rounding as desmos interprets 'e' in terms of exponential
           not scientific notation"""
        A = np.around(self.A, 2)
        b = np.around(self.b, 2)
        for i in range(np.shape(self.A)[0]):
            print(f'{A[i][0]}x + {A[i][1]}y <= {b[i][0]}')

    def print_eqns_Ac(self):
        """"Verification, should print same as above, disregarding rounding error"""
        A = np.around(self.A, 2)
        c = np.around(self.c, 2)
        for i in range(np.shape(self.A)[0]):
            print(f'{A[i][0]}(x - {c[i][0][0]}) + {A[i][1]}(y - {c[i][1][0]}) <= 0')

    def calcSupportVectors(self):
        s1 = self.vertices[0] - self.center
        s2 = self.vertices[1] - self.center
        s3 = self.vertices[2] - self.center
        s4 = self.vertices[3] - self.center
        self.svecs = np.vstack((s1.T, s2.T, s3.T, s4.T))

    def support(self, dir, dim='3D', exact=False):
        # used in collisionGJK
        dir2 = dir[:2]
        if exact:
            s = self.supportExact(dir2)
        else:
            s = self.supportVertex(dir2)
        if dim == '3D':
            print(np.reshape(dir[2, :], (1, 1)))
            s = np.append(s, np.reshape(dir[2, :], (1, 1)), axis=0)
        return s

    def supportVertex(self, dir):
        return self.vertices[np.argmax(self.svecs@dir, axis=0)[0]]

    def supportExact(self, dir):
        dotproducts = self.svecs@dir
        two_largest = np.argpartition(dotproducts, -2, axis=0)[-2:, 0]
        weights = dotproducts[two_largest]/np.sum(dotproducts[two_largest], axis=0)

        return self.center + self.svecs[two_largest].T@weights

    def drawRectangle(self, color='cyan', fill=True):
        ax = plt.gca()
        r = patches.Rectangle(self.vertices[0], self.w, self.h, self.angle, color=color, fill=fill)
        ax.add_artist(r)

class Ellipse():

    def __init__(self, center, matrix):
        self.mtx = matrix
        self.c = center
        self.c3D = np.append(center, [[0]], axis=0)

    def convertFromMatrix(self, mtx):
        # designed for 2x2 input
        e, v = np.linalg.eig(np.linalg.inv(mtx))
        width = 2/np.sqrt(e[0])
        height = 2/np.sqrt(e[1])
        angle = np.degrees(v[0][0]/np.linalg.norm(v[0]))
        self.w = width
        self.h = height
        self.angle = angle

    def convertToMatrix(self, angle, w, h):
        rotate = get_rotation_mtx(angle)
        self.mtx = np.linalg.inv(rotate@np.diag(((2/w)**2, (2/h)**2))@rotate.T)

    def getHalfMtxPts(self):
        mtx_half = scipy.linalg.sqrtm(self.mtx)
        halfmtx_pts = np.zeros((2, 2*mtx_half.shape[0]))
        for i in range(mtx_half.shape[0]):
            halfmtx_pts[:, i] = mtx_half[:, i]
            halfmtx_pts[:, i + mtx_half.shape[0]] = -mtx_half[:, i]
        halfmtx_pts += self.c
        return halfmtx_pts

    def support(self, dir, dim='3D', exact=True):
        # https://juliareach.github.io/LazySets.jl/latest/lib/sets/Ellipsoid/
        #B = np.linalg.cholesky(np.linalg.inv(self.mtx))
        dir2 = dir[:2]
        if dim == '3D':
            return self.c3D + np.append(self.mtx@dir2/(np.sqrt(dir2.T@self.mtx@dir2)), np.reshape(dir[2, :], (1, 1)), axis=0)
            #return self.c3D + np.append(B@dir2/(np.sqrt(dir2.T@self.mtx@dir2)), np.reshape(dir[2, :], (1, 1)), axis=0)
            #return self.c3D + np.append(dir2*np.linalg.norm(B@dir2, axis=0), np.reshape(dir[2, :], (1, 1)), axis=0)
        elif dim == '2D':
            return self.c + np.array([[self.w/2*dir2[0, 0]], [self.h/2*dir2[1, 0]]])
            #return self.c + self.mtx@dir2/(np.sqrt(dir2.T@self.mtx@dir2))
            #return self.c + B@dir2/(np.sqrt(dir2.T@self.mtx@dir2))
            #return self.c + dir2*np.linalg.norm(B@dir2, axis=0)

    def drawEllipse(self, color="gray", fill=False):
        ax = plt.gca()
        ellip = patches.Ellipse(self.c, self.w, self.h, self.angle, color=color, fill=fill)
        ax.add_artist(ellip)

def collisionGJK(A, B):
    # supports 2D 
    # A and B are shapes
    # https://apps.dtic.mil/dtic/tr/fulltext/u2/a622925.pdf

    class Simplex():

        def __init__(self, vertices=[]):
            self.v = vertices
            self.contains_origin = False
            self.next_simplex = None
            self.next_direction = None

        def add(self, P):
            if self.num_points() < 3:
                self.v.append(P)

        def num_points(self):
            return len(self.v)

        def process(self):

            def simplex0():
                if np.allclose(self.v[-1], np.zeros((3, 1))):
                    self.contains_origin = True
                else:
                    self.next_direction = normalize(-self.v[-1])
                    self.next_simplex = self

            def simplex1():
                AB = self.v[-1] - self.v[-2]
                AO = -self.v[-1]
                dir = np.cross(np.cross(AB, AO, axis=0), AB, axis=0)
                if np.allclose(dir, np.zeros((3, 1))):
                    self.contains_origin
                else:
                    dir = normalize(dir)
                    self.next_direction = dir
                    self.next_simplex = self

            def simplex2():
                AB = self.v[-1] - self.v[-2]
                AC = self.v[-1] - self.v[-3]
                ABCn = np.cross(AB, AC, axis=0)
                ACn = np.cross(ABCn, AC, axis=0)
                ABn = np.cross(AB, ABCn, axis=0)
                AO = -self.v[-1]
                if ABn.T@AO > 0:
                    # in 2D can use ABn
                    self.next_direction = normalize(ABn)
                    self.next_simplex = Simplex([self.v[-2], self.v[-1]])
                elif ACn.T@AO > 0:
                    self.next_direction = normalize(ACn)
                    self.next_simplex = Simplex([self.v[-3], self.v[-1]])
                else:
                    self.contains_origin = True
                    self.plot_simplex()

            if self.num_points() == 1:
                simplex0()
            elif self.num_points() == 2:
                simplex1()
            elif self.num_points() == 3:
                simplex2()

        def get_next(self):
            return self.next_simplex, self.next_direction

        def plot_simplex(self):
            for v in self.v:
                plt.scatter(v[0, 0], v[1, 0], s=100, color='black')

    niters = 0
    # use done variable if limiting iterations
    done = False
    result = False
    dir = np.array([[1], [0], [0]])
    simp = Simplex()
    while not done and niters < 20:
        niters+=1
        # print(f'A.support(dir): {A.support(dir)}')
        # print(f'B.support(-dir): {B.support(-dir)}')
        P = A.support(dir) - B.support(-dir)
        OP = -P
        # print(f'P: {P}')
        simp.add(P)
        if simp.num_points() > 1 and OP.T.dot(dir) < 0:
            res = False
            done = True
        simp.process()
        if simp.contains_origin:
            res = True
            done = True
        simp, dir = simp.get_next()
    return res

def get_rotation_mtx(angle_deg):
    theta = np.radians(angle_deg)
    c, s = np.cos(theta), np.sin(theta)
    R = np.array(((c, -s), (s, c)))
    return R

def normalize(x, axis=0, ord=2):
    return x/np.linalg.norm(x, axis=axis)

def drawMinkowskiDifference(A, B, resolution=100):
    xs, ys = [], []
    A_xs, A_ys = [], []
    B_xs, B_ys = [], []
    theta_x, theta_y = [], []
    for theta in np.linspace(-np.pi*9/10, np.pi*9/10, resolution):
        print(f'theta :{theta}')
        dir = np.array([[np.cos(theta)], [np.sin(theta)], [0]])
        
        theta_x.append(dir[0, 0])
        theta_y.append(dir[1, 0])

        Apt = A.support(dir, dim='2D', exact=True)
        Bpt_neg = B.support(dir, dim='2D', exact=True)
        P = Apt + Bpt_neg

        A_xs.append(Apt[0, 0])
        A_ys.append(Apt[1, 0])
        B_xs.append(Bpt_neg[0, 0])
        B_ys.append(Bpt_neg[1, 0])
        xs.append(P[0, 0])
        ys.append(P[1, 0])

    # plt.plot(A_xs, A_ys)    
    # plt.plot(B_xs, B_ys)
    # plt.plot(xs, ys)
    plt.scatter(A_xs, A_ys)    
    plt.scatter(B_xs, B_ys)
    plt.scatter(xs, ys)
    plt.scatter(theta_x, theta_y)

def plot_GJK(e_x=0.0, e_y=0.0, e_width=5.0, e_height=2.0, e_angle=80.0, r_x =-1.0, r_y=-0.5, r_width=2.0, r_height=1.0, r_angle=0.0):

    plt.figure(figsize=(10, 10))
    ax = plt.gca()
    ax.axis([-5, 5, -5, 5])

    rotate = get_rotation_mtx(e_angle)
    e_mtx = np.linalg.inv(rotate@np.diag(((2/e_width)**2, (2/e_height)**2))@rotate.T)
    e = Ellipse(np.array([[e_x], [e_y]]), e_mtx)
    e.w = e_width
    e.h = e_height
    e.angle = e_angle
    r = Rectangle(np.array([[r_x], [r_y]]), r_width, r_height, r_angle, get_poly=False)

    drawMinkowskiDifference(r, e, resolution=100)
    halfmtx_pts = e.getHalfMtxPts()
    plt.scatter(halfmtx_pts[0, :], halfmtx_pts[1, :])

    #pdb.set_trace()
    intersect = collisionGJK(r, e)
    print(f'intersect: {intersect}')
    if intersect:
        e_color = 'red'
        r_color = 'red'
    else:
        e_color = 'cyan'
        r_color = 'grey'        

    e.drawEllipse(color=e_color, fill=False)
    r.drawRectangle(color=r_color, fill=False)

interact(plot_GJK)