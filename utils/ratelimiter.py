"""Rate-limiting is used to ensure (multi-threaded) workers do not overly
tax the resources they are interacting with. Functions in this module are
factories that return rate-limiting implementation functions.

Attributes:
  ZERO_DURATION (timedelta): this is an internal helper constant set to
    a zero-length time delay.
"""

from datetime import datetime, timedelta
from threading import Lock
from time import sleep

ZERO_DURATION = timedelta(0)

def create_ratelimit_waiter(rate_per_second, window_in_seconds = 0):
	"""Construct a rate-limiting waiter that will sleep the minimum amount of
	time to continue satisfying the specified rate-limiting constraints.

	Non-default constraints for "overshoot" and "window" allow extra flexibility
	in the short-term request rate; otherwise strict adherence to the stated rate
	will be followed.

	Args:
	  rate_per_second (int): Number of requests to allow to pass per second
	  window_in_seconds (int): Length of time window to amortize request rate over

	Returns:
	  Parameter-less and result-less function that honours the defined rate-limiting
	  constraints by sleeping the minimum amount of time for them to be satisfied.
	"""
	ratelimiter = create_ratelimiter(rate_per_second, window_in_seconds)

	def waiter():
		wait = ratelimiter(datetime.now())
		sleep(wait.total_seconds())

	return waiter

def create_ratelimiter(rate_per_second, window_in_seconds = 0):
	"""Helper-method that builds the underlying rate-limiter function in a testable form.

	Args:
	  rate_per_second (int): Number of requests to allow to pass per second
	  window_in_seconds (int): Length of time window to amortize request rate over

	Returns:
	  Function taking the 'datetime' a rate-limited event takes place at, and returning
	  a 'timedelta' describing the amount of delay required to satisfy rate-limiting.
	"""
	count = 0
	last = None
	lock = Lock()
	max = rate_per_second * window_in_seconds

	def _seconds(delta):
		return delta.days * 86400 + delta.seconds

	def ratelimiter(timestamp):
		nonlocal count
		nonlocal last

		with lock:
			if last is None:
				last = timestamp
			else:
				delta = timestamp - last
				if delta > ZERO_DURATION:
					last += timedelta(delta.days, delta.seconds)
					count -= (delta.days * 86400 + delta.seconds) * rate_per_second
					if count < 0:
						count = 0
			result = ZERO_DURATION if count <= max else timedelta(microseconds = ((count - max) * 1000000) // rate_per_second)
			count += 1

		return result

	return ratelimiter