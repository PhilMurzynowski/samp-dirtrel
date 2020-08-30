"""
Simulating both Car RERRT and Car RRT to compare robustness.
Code in examples provide more documentation to understand layout.
"""

import numpy as np
import matplotlib.pyplot as plt

from trees.rrt import RRT
from trees.rerrt import RERRT
from utils.shapes import Rectangle, Ellipse
from utils.metrics import l2norm2D
from utils.collision import CollisionDetection
from systems.primitives import Input
from systems.examples import Car
from simulation.simulators import RRTSimulator, RERRTSimulator
from visuals.helper import pickRandomColor
from visuals.plotting import (Scene, drawScene, drawTree, drawPath,
                              drawReachable, drawEllipsoids, drawEllipsoidTree)

start = [12.5, 12.5]
goal = [0, 0]
region = Rectangle([-5, -5], 20, 20)
start_state = np.array(start + [-np.pi*2/3, 5, 0]).reshape(5, 1)
goal_state = np.array(goal + [-np.pi*2/3, 5, 0]).reshape(5, 1)

obstacles = []
obstacles.append(Rectangle([7, 11], 3, 1.5, angle=120.0))
obstacles.append(Rectangle([7, 4], 2.5, 1.5, angle=30.0))
scene = Scene(start, goal, region, obstacles)

sys_opts = {
    'dt': 0.005,
    'nx': 5,
    'nu': 2,
    'nw': 2
    }
sys = Car(sys_opts)

dist_metric = l2norm2D
col = CollisionDetection()
collision_function = col.selectCollisionChecker('erHalfMtxPts')

# rrt setup
rrt_input = Input(dim=sys_opts['nu'], type_='random')
rrt_input.setLimits(np.array([[10, 10]]).T)
rrt_input.determinePossibleActions(range_=0.5, resolutions=np.array([5, 5]))
rrt_input.setNumSamples(10)
rrt_tree = RRT(start=start_state,
           goal=goal_state,
           system=sys,
           input_=rrt_input,
           scene=scene,
           dist_func=dist_metric)
# rerrt setup
rerrt_input = Input(dim=sys_opts['nu'], type_='deterministic')
rerrt_input.setLimits(np.array([[10, 10]]).T)
rerrt_input.determinePossibleActions(range_=0.5, resolutions=np.array([2, 3]))
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
    'max_iter':         150,                             # :int:                         iterations
    'direction':        'backward',                     # :'backward'/'forward':        determine tree growth direction
    'track_children':   True,                           # :bool:                        keep record of children of node
    'extend_by':        20,                             # :int:                         num timesteps to simulate in steer function with each extension
    'goal_sample_rate': 0.20,                           # :float:                       goal sample freq. (out of 1)
    'sample_dim':       2,                              # :int:                         Determine how many dimensions to sample in, e.g. 2 for 2D
    'D':                1e-3*np.eye(sys_opts['nw']),    # :nparray: (nw x nw)           ellipse describing uncertainty
    'E0':               1e-9*np.eye(sys_opts['nx']),    # :nparray: (nx x nx)           initial state uncertainty
    'max_dims':         np.array([1, 1]),               # :nparray: (2,)                maximum axis length of ellipse in each dimension
                                                        #                               currently only 2D supported
    'Q':                np.diag((1, 1, 0, 0, 0)),   # :nparray: (nx x nx)           TVLQR Q
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
plt.suptitle('Car RRT',fontsize=25, y=0.925)
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
plt.suptitle('Car RERRT',fontsize=25, y=0.925)
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
"""
num_simulations
    Number of simulations for each trajectory in tree
    ie sampling different w
vis_rrt/vis_rerrt
    whether to visualize simulation
    much faster without visualization
goal_epsilon
    Reaching the goal is currently defined as being with goal_epsilon of the
    final state within the last two extensions.
    This metric was chosen with highly sensitive systems like the furuta
    pendulum in mind, in which a system may come exceedingly close and then
    rapidly accelerate away.
"""
num_simulations=10
vis_rrt, vis_rerrt = True, True
# basically testing if stayed within ellipsoids
# but only as a heuristic, as likely using different distanceMetric than l2norm
# as the ellipse size is defined in theta1, theta2 space
goal_epsilon = options['max_dims'][0]/2
print(f"Simulating RRT with{'' if vis_rrt else 'out'} visualization...")
if vis_rrt: drawScene(scene, size=(15, 15))
sim1.assessTree(num_simulations, goal_epsilon, vis_rrt)
if vis_rrt:
    plt.xlabel('Theta1 (Radians)', fontsize=20)
    plt.ylabel('Theta2 (Radians)', fontsize=20)
    plt.title('Note: Positions are modulo 2pi',fontsize=16)
    plt.suptitle('Furuta RRT Simulation',fontsize=25, y=0.925)
    plt.draw()
    plt.pause(0.001)
print(f"\nSimulating RERRT with{'' if vis_rerrt else 'out'} visualization...")
if vis_rerrt: drawScene(scene, size=(15, 15))
sim2.assessTree(num_simulations, goal_epsilon, vis_rerrt)
if vis_rerrt:
    plt.xlabel('Theta1 (Radians)', fontsize=20)
    plt.ylabel('Theta2 (Radians)', fontsize=20)
    plt.title('Note: Positions are modulo 2pi',fontsize=16)
    plt.suptitle('Furuta RERRT Simulation',fontsize=25, y=0.925)
    plt.draw()
    plt.pause(0.001)


print('\nFinished\n')
plt.show()





