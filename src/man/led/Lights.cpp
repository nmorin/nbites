#include "Lights.h"
const std::string Lights::LED_NAMES[Lights::NUM_LED_NAMES] = {
    "LeftCalibration1","LeftCalibration2","LeftCalibration3","LeftCalibration4","LeftCalibration5",
    "RightCalibration1","RightCalibration2","RightCalibration3","RightCalibration4","RightCalibration5",
    "LeftDodge1","LeftDodge2","LeftDodge3","LeftDodge4","LeftDodge5","RightDodge1","RightDodge2",
    "RightDodge3","RightDodge4","RightDodge5","LeftComm1","LeftComm2","LeftComm3", "LeftComm4",
    "LeftComm5","RightComm1","RightComm2","RightComm3","RightComm4","RightComm5",
    "Role",                       // Left Eye
    "Ball", "GoalBox",            // Right Eye
    "Chest",
    "LeftFoot", "RightFoot"};


Lights::Lights(){};
Lights::~Lights(){};
