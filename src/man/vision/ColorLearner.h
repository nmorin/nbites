#pragma once

#include <vector>
#include <string>
#include <map>
#include <math.h>

#include "Images.h"
#include "Camera.h"
#include "FastBlob.h"
#include "Homography.h"
#include "Field.h"
#include "FrontEnd.h"
#include "Vision.h"
#include "Hough.h"
#include "StatsColor.h"


namespace man {
	namespace vision {

		class ColorLearner {
		public:
			ColorLearner();
			~ColorLearner();
			HRColors* run(FieldLineList* fieldLines, bool topCamera, HRColors* colors, 
				ImageLiteU8 uImage, ImageLiteU8 vImage);
			float mapToUVScale(int uv);

// #ifdef OFFLINE
// #endif
		private:

		};

	}
}
