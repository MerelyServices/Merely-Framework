import unittest
import utils

class Tester(unittest.TestCase):
	def test_time_fold(self):
		assert utils.time_fold(-100) == ""
		assert utils.time_fold(0) == "0 seconds"
		assert utils.time_fold(59) == "59 seconds"
		assert utils.time_fold(60) == "1 minute, 0 seconds"
		assert utils.time_fold(1249812481924) == "40 millenia, 18 decades, 3 years, 0 months, 5 days, 4 hours, 58 minutes, 44 seconds"

	def test_findurls(self):
		assert utils.FindURLs("(http://www.example.com)") == ["http://www.example.com"]
		assert utils.FindURLs("http://192.168.1.100/src/test.png") == ["http://192.168.1.100/src/test.png"]

	def test_cached(self):
		testvar = utils.Cached("test", age=300, threshold=300)
		assert testvar.old == True
		testvar.data = "test2"
		assert testvar.old == False
	
if __name__ == '__main__':
	unittest.main()