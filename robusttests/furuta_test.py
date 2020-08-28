"""
Simulating both Furuta RERRT and Furta RRT to compare robustness.
Code in examples provide more documentation to understand layout.
"""

import numpy as np
import matplotlib.pyplot as plt

from trees.rrt import RRT
from trees.rerrt import RERRT
from utils.shapes import Rectangle, Ellipse
from utils.metrics import l2norm2D, furutaDistanceMetric
from utils.collision import CollisionDetection
from systems.primitives import Input
from systems.examples import Furuta
from simulation.simulators import RRTSimulator, RERRTSimulator
from visuals.helper import pickRandomColor
from visuals.plotting import (Scene, drawScene, drawTree, drawPath,
                              drawReachable, drawEllipsoids, drawEllipsoidTree)

# general setup for both rrt and rerrt
start = [np.pi, 0]
goal = [0, np.pi]
region = Rectangle([-2*np.pi, -2*np.pi], 4*np.pi, 4*np.pi)
start_state = np.array(start + [0, 0]).reshape(4, 1)
goal_state = np.array(goal + [0, 0]).reshape(4, 1)
obstacles = []
scene = Scene(start, goal, region, obstacles)

# system setup
# Note: a small timestep appears to be necessary for this system
# as otherwise error blows up when switching from backward
# to forward integration
sys_opts = {
    'dt': 0.005,
    'nx': 4,
    'nu': 2,
    'nw': 2,
    'm1': 1.300,
    'm2': 0.075,
    'l1': 0.150,
    'l2': 0.148,
    'L1': 0.278,
    'L2': 0.300,
    'b1': 1e-4,
    'b2': 2.8e-4,
    'J1': 2.48e-2,
    'J2': 3.86e-3
    }
sys = Furuta(sys_opts)

# pick metric and collision detection
dist_metric = furutaDistanceMetric
col = CollisionDetection()
collision_function = col.selectCollisionChecker('erHalfMtxPts')

# rrt setup
rrt_input = Input(dim=sys_opts['nu'], type_='random')
rrt_input.setLimits(np.array([[4, 0]]).T)
rrt_input.determinePossibleActions(range_=0.25, resolutions=np.array([10, 1]))
rrt_input.setNumSamples(3)
rrt_tree = RRT(start=start_state,
           goal=goal_state,
           system=sys,
           input_=rrt_input,
           scene=scene,
           dist_func=dist_metric)
# rerrt setup
rerrt_input = Input(dim=sys_opts['nu'], type_='deterministic')
rerrt_input.setLimits(np.array([[4, 0]]).T)
rerrt_input.determinePossibleActions(range_=0.25, resolutions=np.array([3, 1]))
rerrt_tree = RERRT(start=start_state,
             goal=goal_state,
             system=sys,
             input_=rerrt_input,
             scene=scene,
             dist_func=dist_metric,
             collision_func=collision_function)
# use same options for both, RERRT will use all
options = {
    'min_dist':         1e-3,                           # :float:                       min dist to goal
    'max_iter':         50,                             # :int:                         iterations
    'direction':        'backward',                     # :'backward'/'forward':        determine tree growth direction
    'track_children':   True,                           # :bool:                        keep record of children of node
    'extend_by':        20,                             # :int:                         num timesteps to simulate in steer function with each extension
    'goal_sample_rate': 0.20,                           # :float:                       goal sample freq. (out of 1)
    'sample_dim':       2,                              # :int:                         Determine how many dimensions to sample in, e.g. 2 for 2D
    'D':                0.10*np.eye(sys_opts['nw']),    # :nparray: (nw x nw)           ellipse describing uncertainty
    'E0':               0.10*np.eye(sys_opts['nx']),    # :nparray: (nx x nx)           initial state uncertainty
    'max_dims':         np.array([5, 5]),               # :nparray: (2,)                maximum axis length of ellipse in each dimension
                                                        #                               currently only 2D supported
    'Q':                10*np.diag((1, 1, 0.5, 0.5)),   # :nparray: (nx x nx)           TVLQR Q
    'R':                np.eye(sys_opts['nu']),         # :nparray: (nu x nu)           TVLQR R
}

# run rrt
print('\nRRT Expanding...')
rrt_tree.treeExpansion(options)
print('\nPlotting...')
rrt_final_path = rrt_tree.finalPath()
drawScene(scene, size=(15, 15))
plt.xlabel('Theta1 (Radians)', fontsize=20)
plt.ylabel('Theta2 (Radians)', fontsize=20)
plt.title('Note: Positions are modulo 2pi',fontsize=16)
plt.suptitle('Furuta RRT',fontsize=25, y=0.925)
drawTree(rrt_tree, color='blue')
drawPath(rrt_final_path, color='red')
print('Finished\n')
plt.draw()
plt.pause(0.001)    # hack to show plots realtime

# run rerrt
print('RERRT Expanding...')
rerrt_tree.treeExpansion(options)
print('\nPlotting...')
rerrt_final_path = rerrt_tree.finalPath()
drawScene(scene, size=(15, 15))
plt.xlabel('Theta1 (Radians)', fontsize=20)
plt.ylabel('Theta2 (Radians)', fontsize=20)
plt.title('Note: Positions are modulo 2pi',fontsize=16)
plt.suptitle('Furuta RERRT',fontsize=25, y=0.925)
drawTree(rerrt_tree, color='blue')
drawPath(rerrt_final_path, color='red')
drawEllipsoidTree(rerrt_tree, options)
print('Finished\n')
plt.draw()
plt.pause(0.001)

print('Comparing Robustness...')
# ok to use options if parameters the same, hacky for now
sim1 = RRTSimulator(tree=rrt_tree,
                    opts=options)
sim2 = RERRTSimulator(tree=rerrt_tree,
                      opts=options)
# number of simulations for each trajectory in tree
# ie sampling different w
# much faster without visualization
num_simulations=1
vis_rrt, vis_rerrt = True, True
print(f"Simulating RRT with{'' if vis_rrt else 'out'} visualization...")
if vis_rrt: drawScene(scene, size=(15, 15))
sim1.assessTree(num_simulations, vis_rrt)
if vis_rrt:
    plt.xlabel('Theta1 (Radians)', fontsize=20)
    plt.ylabel('Theta2 (Radians)', fontsize=20)
    plt.title('Note: Positions are modulo 2pi',fontsize=16)
    plt.suptitle('Furuta RRT Simulation',fontsize=25, y=0.925)
    plt.draw()
    plt.pause(0.001)
print(f"\nSimulating RERRT with{'' if vis_rerrt else 'out'} visualization...")
if vis_rerrt: drawScene(scene, size=(15, 15))
sim2.assessTree(num_simulations, vis_rerrt)
if vis_rerrt:
    plt.xlabel('Theta1 (Radians)', fontsize=20)
    plt.ylabel('Theta2 (Radians)', fontsize=20)
    plt.title('Note: Positions are modulo 2pi',fontsize=16)
    plt.suptitle('Furuta RERRT Simulation',fontsize=25, y=0.925)
    plt.draw()
    plt.pause(0.001)


print('\nFinished\n')
plt.show()





