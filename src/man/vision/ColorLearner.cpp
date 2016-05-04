#include "ColorLearner.h"

#include <algorithm>
#include <iostream>


using std::to_string;

namespace man {
namespace vision {

	ColorLearner::ColorLearner()
	{
	}

	ColorLearner::~ColorLearner() { }

	HRColors* ColorLearner::run(FieldLineList* fieldLines, bool topCamera, 
		HRColors* colors, ImageLiteU8 uImage, ImageLiteU8 vImage)
	{

		std::cout << "[COLORLEARNER DEBUG] Entering ColorLearner.run()\n";
		if (topCamera) { std::cout << "[COLORLEARNER DEBUG] TOPCAMERA\n"; }
		else { std::cout << "[COLORLEARNER DEBUG] BOTTOMCAMERA\n"; }
		// prep
		int lineCenterY = uImage.height() / 2;
		int lineCenterX = uImage.width() / 2;

		// Create statistics
		std::map<int, int> uLineVals, vLineVals;

		int pixLineX, pixLineY;
		double houghLine1X0, houghLine1Y0, houghLine1X1, houghLine1Y1;
        double houghLine2X0, houghLine2Y0, houghLine2X1, houghLine2Y1;

        // Collect the pixel information from the lines
		for (int y = 0; y < uImage.height(); y++) {
			for (int x = 0; x < uImage.width(); x++) {
				int u_val = *uImage.pixelAddr(x,y);
				int v_val = *vImage.pixelAddr(x,y);

				for (int i = 0; i < fieldLines->size(); i++) {
					FieldLine& line = (*fieldLines)[i];
					HoughLine& houghLine1 = line[0];
					HoughLine& houghLine2 = line[1];
					pixLineX = x - lineCenterX;
					pixLineY = lineCenterY - y;

					houghLine1.rawEndPoints(0, 0, houghLine1X0, houghLine1Y0, houghLine1X1, houghLine1Y1);
	                houghLine2.rawEndPoints(0, 0, houghLine2X0, houghLine2Y0, houghLine2X1, houghLine2Y1);
                
	                if (houghLine1.pDist(pixLineX, pixLineY) > 0 && 
	                    houghLine2.pDist(pixLineX, pixLineY) > 0 &&
	                    houghLine1.qDist(pixLineX, pixLineY) < houghLine1.ep1() &&
	                    houghLine2.qDist(pixLineX, pixLineY) < houghLine2.ep1()
	                    ) 
	                {
	                	if (uLineVals.count(u_val))
	                        uLineVals[u_val]++;
	                    else
	                        uLineVals.insert(std::pair<int, int>(u_val, 1));

	                    if (vLineVals.count(v_val))
	                        vLineVals[v_val]++;
	                    else
	                        vLineVals.insert(std::pair<int, int>(v_val, 1));
	                }	
				}
			}
		}

		// Create statistics
		StatsColor *uStat = new StatsColor(uLineVals);
		StatsColor *vStat = new StatsColor(vLineVals);
		double uAvg = uStat->getAvg();
		double vAvg = vStat->getAvg();
		int uMin = uStat->getMin();
		int uMax = uStat->getMax();
		int vMin = vStat->getMin();
		int vMax = vStat->getMax();

		std::cout << "[COLORLEARNER DEBUG] uStats for WHITE: \n";
		uStat->print();
		std::cout << "[COLORLEARNER DEBUG] vStats for WHITE: \n";
		vStat->print();

		std::cout << "[COLORLEARNER DEBUG] uAvg UVSCALE for WHITE: " << mapToUVScale(uAvg) << "\n";
		std::cout << "[COLORLEARNER DEBUG] vAvg UVSCALE for WHITE: " << mapToUVScale(vAvg) << "\n";

		std::cout << "[COLORLEARNER DEBUG] uMin UVSCALE for WHITE: " << mapToUVScale(uMin) << "\n";
		std::cout << "[COLORLEARNER DEBUG] uMax UVSCALE for WHITE: " << mapToUVScale(uMax) << "\n\n";
		std::cout << "[COLORLEARNER DEBUG] vMin UVSCALE for WHITE: " << mapToUVScale(vMin) << "\n";
		std::cout << "[COLORLEARNER DEBUG] vMax UVSCALE for WHITE: " << mapToUVScale(vMax) << "\n";


		std::cout << "_________________________________\n";

		std::cout << "[COLORLEARNER DEBUG] Original params: \n";
		colors->print();
		std::cout << "_________________________________\n";
		std::cout << "FOR STAT GATHERING: \n";


		// Adjust color parameters of visionModule

		HRColors* ret = colors; //new man::vision::HRColors; //new man::vision::Colors;
		// ret->setWhite(0.3, 0.3, 0.3, 0.3, 0.3, 0.3);
		// ret->setOrange(0.3, 0.3, 0.3, 0.3, 0.3, 0.3);
		// ret->setGreen(0.3, 0.3, 0.3, 0.3, 0.3, 0.3);
		// TODO adjust for top and bottom camera
		// ret->white.load(float darkU0, float darkV0, float lightU0, 
		// 	float lightV0, float fuzzyU, float fuzzyV);
		// ret->green.load(float darkU0, float darkV0, float lightU0, 
		// 	float lightV0, float fuzzyU, float fuzzyV);
		// ret->orange.load(float darkU0, float darkV0, float lightU0, 
		// 	float lightV0, float fuzzyU, float fuzzyV);

		std::cout << "[COLORLEARNER DEBUG] Exiting ColorLearner.run()\n";

		std::cout << "**************************************\n";

		return ret;
	}

	// Maps from a 0-255 value to a -0.5-0.5 value
	float ColorLearner::mapToUVScale(int uv) {
		float ret = ((float)uv) / 255;
		return ret - 0.5;
	}



// 	bool BallDetector::findBall(ImageLiteU8 orange, double cameraHeight)
// 	{
// 		const double CONFIDENCE = 0.5;

// 		if (debugBall) {
// 			candidates.clear();
// 		}

// 		blobber.run(orange.pixelAddr(), orange.width(), orange.height(),
// 					orange.pitch());

// 		Ball reset;
// 		_best = reset;
// 		width = orange.width();
// 		height = orange.height();

// 		// TODO: Sort blobber list by size
// 		for (auto i=blobber.blobs.begin(); i!=blobber.blobs.end(); i++) {
// 			int centerX = static_cast<int>((*i).centerX());
// 			int centerY = static_cast<int>((*i).centerY());
// 			int principalLength = static_cast<int>((*i).firstPrincipalLength());
// 			int principalLength2 = static_cast<int>((*i).secondPrincipalLength());
// 			bool occludedSide = false;
// 			bool occludedTop = false;
// 			bool occludedBottom = false;

// 			double x_rel, y_rel;

// 			double bIX = ((*i).centerX() - width/2);
// 			double bIY = (height / 2 - (*i).centerY()) -
// 				(*i).firstPrincipalLength();

// 			bool belowHoriz = homography->fieldCoords(bIX, bIY, x_rel, y_rel);

// 			if (preScreen(centerX, centerY, principalLength, principalLength2,
// 						  occludedSide, occludedTop, occludedBottom)) {
// 				continue;
// 			}

// 			Ball b((*i), x_rel, -1 * y_rel, cameraHeight, height,
// 				   width, topCamera, occludedSide, occludedTop,
// 				   occludedBottom);

// 			if (b.confidence() > CONFIDENCE) {
// #ifdef OFFLINE
// 				// we always want to draw the ball, even when not debugging it
// 				candidates.push_back(b);
// #endif
// 				if (debugBall) {
// 					std::cout << "accepted ball at: " << centerX << " " <<
// 						centerY << " because:\n" << b.properties()
// 							  << std::endl;
// 				}
// 				if (b.dist < _best.dist) {
// 					_best = b;
// 				}
// 			}
// 			else {
// 				if (debugBall) {
// 					std::cout << "declined ball at " << centerX << " " <<
// 						centerY << " because:\n" << b.properties()
// 							  << std::endl;
// 				}
// 			}
// 		}
// 		if (_best.confidence() > CONFIDENCE) {
// 			return true;
// 		}
// 		else {
// 			return false;
// 		}
// 	}

}
}
