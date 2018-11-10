import maestro
from time import sleep

m = maestro.Controller('/dev/ttyACM0')

m.setSpeed(0, 60)
m.setSpeed(1, 60)
m.setSpeed(2, 60)
m.setSpeed(3, 60)
m.setSpeed(4, 60)

trajectory = [
    [[1500, 1692, 1773, 1228, 904],  2],
    [[1477, 1185, 864,  1228, 904],  1],
    [[1477, 1185, 864,  1228, 1671], 1],
    [[1477, 2100, 864,  1228, 1671], 1],
    [[802,  826,  1775, 1228, 1671], 1],
    [[802,  826,  1775, 1228, 904],  1],
    [[802,  1692, 1775, 1228, 904],  1],
    [[1500, 1692, 1773, 1228, 904],  1]
]
for pos in trajectory:
    m.set_target_vector(pos[0], pos[1])

m.close()