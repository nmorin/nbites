#include "nbfuncs.h"
#include <assert.h>
#include <vector>
#include <string>
#include <iostream>
#include <map>

using nblog::Log;
using nblog::SExpr;

int test_func() {
    assert(args.size() == 2);
    for (int i = 0; i < args.size(); ++i) {
        printf("test_func(): %s\n", args[i]->description().c_str());
    }
    
    return 0;
}

int arg_test_func() {
    printf("arg_test_func()\n");
    assert(args.size() == 2);
    for (int i = 0; i < 2; ++i) {
        printf("\t%s\n", args[i]->description().c_str());
        rets.push_back(new Log(args[i]));
    }
    
    return 0;
}

int CrossBright_func() {
    assert(args.size() == 1);
    printf("CrossBright_func()\n");
    //work on a copy of the arg so we can safely push to rets.
    
    Log * copy = new Log(args[0]);
    size_t length = copy->data().size();
    uint8_t buf[length];
    memcpy(buf, copy->data().data(), length);
    
    for (int i = 0; i < length; i += 2) {
        *(buf + i) = 240;
    }
    std::string buffer((const char *) buf, length);
    copy->setData(buffer);
    
    rets.push_back(copy);
    
    return 0;
}

// struct yuvColor {
//     int y1;
//     int y2;
//     int u;
//     int v;
// };

// struct colorAndCount {
//     yuvColor color;
//     int count;
// };

// bool closeToColor(yuvColor color1, yuvColor color2) {
//     int yThresh = 10;
//     int uThresh = 10;
//     int vThresh = 10;

//     if (abs(color1.y1 - color2.y1) < yThresh
//         && abs(color1.y2 - color2.y2) < yThresh
//         && abs(color1.v - color2.v) < vThresh
//         && abs(color1.u - color2.u) < uThresh)
//         return true;

//     return false;
// }

// yuvColor findMostCommon(uint8_t *buf, size_t length) {
//     std::vector<colorAndCount> colors;
//     yuvColor mostCommon;
//     bool foundMatch = false;

//     for (int i = 0; i < length; i += 4) {
//         yuvColor newColor = {*(buf + i), *(buf + i + 1), *(buf + i + 2), *(buf + i + 3)};

//         std::vector<std::string, colorAndCount>::iterator it;
//         for(it = colors.begin(); it != colors.end(); it++) {
//             colorAndCount *temp = &(it->second);
//             if (closeToColor(temp->color, newColor)) {
//                 std::cout << "Was close enough!" << std::endl;
//                 temp->count += 1;
//                 foundMatch = true;
//                 break;
//             }
//         }
//         if (!foundMatch) {
//             colorAndCount newColorCountPair = {newColor, 0};
//             colors.push_back(newColorCountPair);
//         }
//     }

//     // std::map<std::

//     return mostCommon;
// } 

