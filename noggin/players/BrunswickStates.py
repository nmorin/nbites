from ..playbook.PBConstants import DEFAULT_CHASER_NUMBER, GOALIE
import man.motion.SweetMoves as SweetMoves
###
# Reimplementation of Game Controller States for pBrunswick
###

def gamePenalized(player):
    if player.firstFrame():
        if player.squatting:
            player.executeMove(SweetMoves.GOALIE_SQUAT_STAND_UP)
            player.squatting = False
        else:
            player.stopWalking()
        player.penalizeHeads()

    if (player.stateTime >=
        SweetMoves.getMoveTime(SweetMoves.GOALIE_SQUAT_STAND_UP)):
        player.stopWalking()

    return player.stay()

def gameReady(player):
    """
    Stand up, and pan for localization
    """
    if player.firstFrame():
        player.brain.CoA.setRobotGait(player.brain.motion)
    if player.brain.gameController.ownKickOff:
        player.hasKickedOffKick = True
    else:
        player.hasKickedOffKick = True
    player.standup()
    player.brain.tracker.locPans()
    if player.lastDiffState == 'gameInitial':
        return player.goLater('relocalize')
    if player.firstFrame() and \
            player.lastDiffState == 'gamePenalized':
        player.brain.resetLocalization()

    return player.goLater('playbookPosition')

def gameSet(player):
    """
    Fixate on the ball, or scan to look for it
    """
    if player.firstFrame():
        player.brain.CoA.setRobotGait(player.brain.motion)
    if player.firstFrame() and player.lastDiffState == 'gamePenalized':
        player.brain.resetLocalization()

    if player.firstFrame():
        player.stopWalking()
        player.brain.loc.resetBall()

        if player.brain.playbook.role == GOALIE:
            player.brain.resetGoalieLocalization()
            if player.squatting:
                return player.goLater('squatted')
            return player.goLater('squat')

        if player.brain.my.playerNumber == DEFAULT_CHASER_NUMBER:
            player.brain.tracker.trackBall()
        else:
            player.brain.tracker.activeLoc()

    return player.stay()

def gamePlaying(player):
    if player.firstFrame():
        player.brain.CoA.setRobotGait(player.brain.motion)
    if player.firstFrame() and \
            player.lastDiffState == 'gamePenalized':
        player.brain.resetLocalization()

    roleState = player.getRoleState(player.currentRole)
    return player.goNow(roleState)

def penaltyShotsGameReady(player):
    if player.firstFrame():
        player.brain.CoA.setRobotGait(player.brain.motion)
    if player.firstFrame():
        if player.lastDiffState == 'gamePenalized':
            player.brain.resetLocalization()
        player.brain.tracker.locPans()
        player.walkPose()
        if player.brain.playbook.role == GOALIE:
            player.brain.resetGoalieLocalization()
    return player.stay()

def penaltyShotsGameSet(player):
    if player.firstFrame():
        player.brain.CoA.setRobotGait(player.brain.motion)
    if player.firstFrame():
        player.stopWalking()
        player.brain.loc.resetBall()

        if player.lastDiffState == 'gamePenalized':
            player.brain.resetLocalization()
        if player.brain.playbook.role == GOALIE:
            player.brain.tracker.trackBall()
        else:
            player.brain.tracker.activeLoc()
    return player.stay()

def penaltyShotsGamePlaying(player):
    if player.firstFrame():
        player.brain.CoA.setRobotGait(player.brain.motion)
    if player.lastDiffState == 'gamePenalized' and \
            player.firstFrame():
        player.brain.resetLocalization()

    if player.brain.playbook.role == GOALIE:
        return player.goNow('penaltyGoalie')
    return player.goNow('penaltyKick')
