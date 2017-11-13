import unittest
from SI507project5_code import *


# Tumblr's API documentation provides two succesful examples
# of a blog's post returned in JSON format:
# https://api.tumblr.com/v2/blog/peacecorps.tumblr.com/posts/text?api_key=fuiKNFp9vQFvjLNvx4sUwti4Yb5yGutBN4Xh10LXZhhRKjWlV4&notes_info=true
# https://api.tumblr.com/v2/blog/pitchersandpoets.tumblr.com/posts/photo?tag=new+york+yankees


# do desired keys in the response dictionary exist
class Cache(unittest.TestCase):

    def setUp(self):
        self.json_cache = open(CACHE_FNAME, "r")
        # sometimes get error that tumblr_result not defined (but sometimes not)
        # --> hardcoding it below
        self.tumblr_result = get_data_from_api("http://api.tumblr.com/v2/blog/starwarsmemes.tumblr.com/posts", "Tumblr", {"api_key": CLIENT_KEY, "notes_info": True})
        self.posts = self.tumblr_result["response"]["posts"]

    def test_json_cache_exists(self):
        self.assertTrue(self.json_cache, "Testing that the JSON cache exists")

    def test_of_post_key_in_cache(self):
        self.assertTrue(self.posts, "Testing that cache has ['posts'] key")
        self.assertEqual(type(self.posts), list, "Testing that the value associated with the ['posts'] key is a list")
        self.assertEqual(len(self.posts), 20, "Testing that len(['posts']) = 20")
        for post in self.posts:
            self.assertEqual(type(post), dict, "Testing that each element in the ['posts'] list is a dictionary")

    def test_of_note_count_key_in_cache(self):
        for post in self.posts:
            self.assertTrue(post["note_count"], "Testing that each post has a ['note_count'] key")
            self.assertEqual(type(post["note_count"]), int, "Testing that the value of each post's ['note_count'] key is an integer")

    def test_of_note_key_in_cache(self):  # this key is something you have to ask for in the Tumblr API, so did I pull it off
        for post in self.posts:
            self.assertTrue(post["notes"], "Testing that each post has a ['notes'] key")
            self.assertEqual(type(post["notes"]), list, "Testing that the value associated with the ['notes'] key is a list")
            for note in post["notes"]:
                self.assertEqual(type(note), dict, "Testing that every element in the list associated with the ['notes'] key is a dictionary")
                self.assertTrue(note["type"], "Testing that each dictionary in the list associated with the ['notes'] key has a ['type'] key")

    def tearDown(self):
        self.json_cache.close()


# do CSVs exist
class CSVs(unittest.TestCase):

    def setUp(self):
        self.post_popularity_csv = open("post_popularity.csv", "r")
        self.post_types_csv = open("post_types.csv", "r")

    def test_csv_files_exist(self):
        self.assertTrue(self.post_popularity_csv, "Testing that post_popularity.csv exists")
        self.assertTrue(self.post_types_csv, "Testing that post_types.csv exists")

    def tearDown(self):
        self.post_popularity_csv.close()
        self.post_types_csv.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
