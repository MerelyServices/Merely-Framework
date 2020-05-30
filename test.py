import unittest, importlib

class Utils_Test(unittest.TestCase):
	def __init__(self, methodName):
		super().__init__(methodName)
		self.utils = importlib.import_module('utils')
	
	def test_time_fold(self):
		assert self.utils.time_fold(-100) == ""
		assert self.utils.time_fold(0) == "0 seconds"
		assert self.utils.time_fold(59) == "59 seconds"
		assert self.utils.time_fold(60) == "1 minute, 0 seconds"
		assert self.utils.time_fold(1249812481924) == "40 millenia, 18 decades, 3 years, 0 months, 5 days, 4 hours, 58 minutes, 44 seconds"

	def test_findurls(self):
		assert self.utils.FindURLs("(http://www.example.com)") == ["http://www.example.com"]
		assert self.utils.FindURLs("http://192.168.1.100/src/test.png") == ["http://192.168.1.100/src/test.png"]

	def test_cached(self):
		testvar = self.utils.Cached("test", age=300, threshold=300)
		assert testvar.old == True
		testvar.data = "test2"
		assert testvar.old == False

class Meme_Test(unittest.TestCase):
	def __init__(self, methodName):
		super().__init__(methodName)
		self.meme = importlib.import_module('meme')
	
	def test_querybuilder(self):
		dudmeme = self.meme.DudMeme()
		db = self.meme.Meme.DB(dudmeme)
		assert db.selectquery(selects=['meme.*','IFNULL(AVG(edge.Value),4)','SUM(memevote.Value)'], _from='meme', joins=['LEFT JOIN edge on edge.memeId = meme.Id','LEFT JOIN memevote ON memevote.memeId = meme.Id'], wheres=['meme.Id = 1'], groups=['meme.Id'], limit='1') == """SELECT meme.*,IFNULL(AVG(edge.Value),4),SUM(memevote.Value) FROM ((meme LEFT JOIN edge on edge.memeId = meme.Id) LEFT JOIN memevote ON memevote.memeId = meme.Id) WHERE meme.Id = 1 GROUP BY meme.Id LIMIT 1"""
		assert db.insertquery(into='meme', inserts=['Id', 'DiscordOrigin', 'Type', 'CollectionParent', 'Url', 'Nsfw'], values=[(1, 302695523360440322, 'image', None, "http://test.com/", 0),(2, 302695523360440322, 'image', None, "http://debug.com/", 0)], ignore=True, on_duplicate="Url = Url") == """INSERT IGNORE INTO meme(Id,DiscordOrigin,Type,CollectionParent,Url,Nsfw) VALUES(1,302695523360440322,"image",null,"http://test.com/",0),(2,302695523360440322,"image",null,"http://debug.com/",0) ON DUPLICATE KEY UPDATE Url = Url"""
		assert db.insertquery(into='meme', inserts=['Id', 'DiscordOrigin', 'Type', 'CollectionParent', 'Url', 'Nsfw'], values=[1, 302695523360440322, 'image', None, "http://test.com/", 0]) == """INSERT INTO meme(Id,DiscordOrigin,Type,CollectionParent,Url,Nsfw) VALUES(1,302695523360440322,"image",null,"http://test.com/",0)"""
		assert db.updatequery(table='meme', sets={'Type': "image", 'Nsfw': False}, wheres=["Id = 1"], limit='1') == """UPDATE meme SET Type = "image",Nsfw = False WHERE Id = 1 LIMIT 1"""
	
if __name__ == '__main__':
	unittest.main()