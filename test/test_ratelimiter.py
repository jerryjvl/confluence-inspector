import unittest
from datetime import datetime, timedelta
from utils.ratelimiter import create_ratelimiter, ZERO_DURATION

TWO_SECONDS = timedelta(seconds = 2)

class TestRateLimiter(unittest.TestCase):
	def _run(self, delta, results):
		result = {}
		result['delta'] = delta
		result['results'] = results
		return result

	def _exec(self, rate, window, runs):
		to_test = create_ratelimiter(rate, window)

		sum_delta = 0
		now = datetime.now()
		for run in runs:
			count = 0
			sum_delta += run['delta']
			with self.subTest(delta = sum_delta):
				now += timedelta(seconds = run['delta'])
				for result in run['results']:
					count += 1
					with self.subTest(run = count):
						self.assertEqual(to_test(now), timedelta(milliseconds = result))

	def test_create(self):
		to_test = create_ratelimiter(rate_per_second = 1, window_in_seconds = 0)
	
	def test_slow_no_window(self):
		self._exec(1, 0, [self._run(0, [0, 1000, 2000, 3000, 4000])])

	def test_slow_windowed(self):
		self._exec(1, 2, [self._run(0, [0, 0, 0, 1000, 2000, 3000])])

	def test_slow_no_window_multiple(self):
		self._exec(1, 0, [
			self._run(0, [0, 1000, 2000]),
			self._run(2, [1000, 2000, 3000]),
			self._run(20, [0, 1000, 2000])])

	def test_slow_windowed_multiple(self):
		self._exec(1, 2, [
			self._run(0, [0, 0, 0, 1000, 2000]),
			self._run(2, [1000, 2000, 3000]),
			self._run(2, [2000, 3000, 4000])])

	def test_fast_no_window_multiple(self):
		self._exec(4, 0, [
			self._run(0, [0, 250, 500, 750, 1000, 1250]),
			self._run(1, [500, 750, 1000, 1250, 1500, 1750]),
			self._run(2, [0, 250, 500, 750])])

if __name__ == '__main__':
    unittest.main()
