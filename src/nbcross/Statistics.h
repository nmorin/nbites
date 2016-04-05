#include <vector>
#include <map>

class Statistics {
	int n;
	int sum;
	double avg;
	double stdDev;

	std::vector<int> nums;

	void init() {
		n = nums.size();
		setSum();
		avg = getAvg();
		setStdDev();
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
	Statistics() {}

	Statistics(std::vector<int> &vals) {
		nums = vals;
		init();
	}

	Statistics(std::map<int, int> &vals) {
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

	double getAvg() {
		return n > 0 ? sum / n : 0;
	}

	double getStdDev() {
		return stdDev;
	}

};