from ..navigator import BrunswickSpeeds as speeds

MAX_X_SPEED = speeds.MAX_X_SPEED
MAX_Y_SPEED = speeds.MAX_Y_SPEED
MAX_SPIN_SPEED = speeds.MAX_SPIN_SPEED

# Component Switches
USE_LOC_CHASE = True
USE_DRIBBLE = False

# Transitions' Constants
# Ball on and off frame thresholds
BALL_ON_THRESH = 2
BALL_OFF_THRESH = 30
BALL_OFF_ACTIVE_LOC_THRESH = 200
# Value to stop spinning to ball and approach
BALL_APPROACH_BEARING_THRESH = 30
# Value to start spinning to ball
BALL_APPROACH_BEARING_OFF_THRESH = 40

# Should position for kick
BALL_POS_KICK_DIST_THRESH = 15.0
BALL_POS_KICK_BEARING_THRESH = 10
BALL_POS_KICK_LEFT_Y = 11.0
BALL_POS_KICK_RIGHT_Y = -BALL_POS_KICK_LEFT_Y
BALL_POS_KICK_MAX_X = 35
BALL_POS_KICK_MIN_X = 5

# Should dribble should and should stop dribbling
SHOULD_DRIBBLE_X = BALL_POS_KICK_MAX_X
SHOULD_DRIBBLE_Y = BALL_POS_KICK_LEFT_Y
SHOULD_DRIBBLE_BEARING = 30.0
STOP_DRIBBLE_X = SHOULD_DRIBBLE_X + 20
STOP_DRIBBLE_Y = SHOULD_DRIBBLE_Y + 20
STOP_DRIBBLE_BEARING = 40.0

# States' constants
# turnToBall
FIND_BALL_SPIN_SPEED = speeds.MAX_SPIN_SPEED
BALL_SPIN_SPEED = speeds.MAX_SPIN_SPEED
BALL_SPIN_GAIN = 0.9
MIN_BALL_SPIN_MAGNITUDE = speeds.MIN_SPIN_MAGNITUDE

# approachBall() values
APPROACH_X_GAIN = 0.1
APPROACH_SPIN_SPEED = speeds.MAX_SPIN_WHILE_X_SPEED
MIN_APPROACH_SPIN_MAGNITUDE = speeds.MIN_SPIN_MAGNITUDE
APPROACH_SPIN_GAIN = 1.1
MAX_APPROACH_X_SPEED = speeds.MAX_X_SPEED
MIN_APPROACH_X_SPEED = speeds.MIN_X_SPEED
APPROACH_WITH_GAIN_DIST = 50

# approachBallWithLoc() values
IN_FRONT_SLOPE = 5.6
APPROACH_DIST_TO_BALL = 25
APPROACH_NO_LOC_THRESH = 4
APPROACH_NO_MORE_LOC_DIST = 150
APPROACH_OMNI_DIST = 25
APPROACH_ACTIVE_LOC_DIST = 35
APPROACH_ACTIVE_LOC_BEARING = 55

# shouldKick()
BALL_KICK_LEFT_Y_L = 10.
BALL_KICK_RIGHT_Y_R = -BALL_KICK_LEFT_Y_L
BALL_KICK_LEFT_Y_R = 4.
BALL_KICK_LEFT_X_CLOSE = 10.
BALL_KICK_LEFT_X_FAR = 20.
POSITION_FOR_KICK_DIST_THRESH = 5.
POSITION_FOR_KICK_BEARING_THRESH = 10.
PFK_X_FAR = 25.
PFK_X_CLOSE = 4.


# Values for controlling the strafing
PFK_MAX_Y_SPEED = speeds.MAX_Y_SPEED
PFK_MIN_Y_SPEED = speeds.MIN_Y_SPEED
PFK_MAX_X_SPEED = speeds.MAX_X_SPEED
PFK_MIN_X_SPEED = speeds.MIN_X_MAGNITUDE
PFK_MIN_Y_MAGNITUDE = speeds.MIN_Y_MAGNITUDE
PFK_X_GAIN = 0.12
PFK_Y_GAIN = 0.6

# Keep track of what gait we're using
FAST_GAIT = "fastGait"
NORMAL_GAIT = "normalGait"

TURN_LEFT = 1
TURN_RIGHT = -1

CHASE_AFTER_KICK_FRAMES = 100

# find ball
WALK_TO_BALL_LOC_POS_FRAMES = 500
SCAN_FIND_BEARING_THRESH = 50
SCAN_FIND_DIST_THRESH = 40

# Orbit ball
ORBIT_BALL_STEP_FRAMES = 150
ORBIT_OFFSET_DIST = 35          # from the ball to the center of the body
ORBIT_STEP_ANGLE = 15
ORBIT_Y_GAIN = .3
ORBIT_X_GAIN = .15
ORBIT_SPIN_GAIN = 0.7
STOP_ORBIT_BEARING_THRESH = 30.0
STOP_ORBIT_BALL_DIST = 50.0

MAX_ORBIT_Y_SPEED = 7
MIN_ORBIT_Y_SPEED = -MAX_ORBIT_Y_SPEED
MIN_ORBIT_Y_MAGNITUDE = 2
MAX_ORBIT_X_SPEED = 7
MIN_ORBIT_X_SPEED = -MAX_ORBIT_X_SPEED
MIN_ORBIT_SPIN_SPEED = -20
MAX_ORBIT_SPIN_SPEED = 20

STOP_PENALTY_DRIBBLE_COUNT = 120
