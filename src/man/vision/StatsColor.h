#include <vector>
#include <map>
#pragma once

// namespace man {
// namespace vision {

class StatsColor {
	int n;
	int sum;
	int max;
	int min;
	double avg;
	double stdDev;

	std::vector<int> nums;

	void init() {
		n = nums.size();
		setSum();
		avg = getAvg();
		setStdDev();
		if (n < 1) {
			min = 0;
			max = 0;

		} else {
			min = nums[0];
			max = nums[n-1];
		}
	}

	void setSum() {
		sum = 0;
		for (int i = 0; i < n; i++) {
			sum += nums[i];
		}
	}

	void setStdDev() {
		double stdSum = 0;
		for (int i = 0; i < n; i++) {
			stdSum += std::pow(nums[i] - avg,2);
		}
		double stdMean = n > 0 ? stdSum / n : 0;
		stdDev = std::sqrt(stdMean);
	}

public:
	StatsColor() {}

	StatsColor(std::vector<int> &vals) {
		nums = vals;
		init();
	}

	StatsColor(std::map<int, int> &vals) {
		std::map<int, int>::iterator it;
		int count, value;
		for (it = vals.begin(); it != vals.end(); it++) {
			value = it->first;
			count = it->second;

			for (int i = 0; i < count; i++) {
				nums.push_back(value);
			}
		}
		init();
	}

	int getCount() {
		return n;
	}

	int getSum() {
		return sum;
	}

	int getMin() {
		return min;
	}

	int getMax() {
		return max;
	}

	double getAvg() {
		return n > 0 ? sum / n : 0;
	}

	double getStdDev() {
		return stdDev;
	}

	void print() {
		std::cout << "AVG: " << getAvg() << "\n";
		std::cout << "stdDev: " << getStdDev() << "\n";
		std::cout << "Count: " << getCount() << "\n";
	}

};
// }
// }