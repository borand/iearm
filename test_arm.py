import maestro
from time import sleep

m = maestro.Controller('/dev/ttyACM0')
print(m.getPosition(0))
m.setSpeed(0, 70)
m.setSpeed(1, 70)
m.setSpeed(2, 70)
m.setSpeed(3, 60)
m.setSpeed(4, 60)
#
trajectory = [
    [1500, 1500, 1500, 1500, 1500], 
    [1000, 1800, 2500, 1500, 1500], 
    [1000, 1500, 1500, 1500, 1500], 
    [2500, 1500, 1500, 1500, 1500], 
    [2500, 1800, 2500, 1500, 1500], 
    [1500, 1500, 1500, 1500, 1500], 
]
 
m.run_trajectory(trajectory)

# for pos in trajectory:
#     m.set_target_vector(pos[0], pos[1])
#     print(pos[0])
#     while m.getMovingState():
#         print(m.get_all_positions())
#
# m.set_target_vector([1900, 1692, 1773, 1228, 900],0)
# print(m.getPosition(0))
m.close()