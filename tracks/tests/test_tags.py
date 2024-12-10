from helpers import TestHelper
from tracks.tags import read_tags, write_tags

import mutagen
import unittest
import os

song_name = 'song.mp3'
song_output = 'song2.mp3'


def track_file_exists(name):
    return os.path.isfile(os.path.join(TestHelper.DATA_DIR, name))


class TestTags(TestHelper):

    @unittest.skipUnless(track_file_exists(song_name), 'TEST DATA dir does not contain mp3 file')
    def test_id3_tags_can_be_read_from_files(self):
        path = self.get_fp(song_name)
        tags = read_tags(mutagen.File(path), path)

        self.assertEqual(tags['title'].lower(), "she's got a way")
        self.assertEqual(tags['album'].lower(), "cold spring harbor")
        self.assertEqual(tags['genre'].lower(), "rock")
        self.assertEqual(tags['artists'], set(['Billy Joel']))
        self.assertEqual(tags['albumArtist'].lower(), 'billy joel')
        self.assertEqual(tags['trackNumber'], 1)
        self.assertEqual(tags['releaseYear'], 1971)

    @unittest.skipUnless(track_file_exists(song_output), 'TEST DATA dir does not contain mp3 file')
    def test_id3_tags_can_be_written_to_file(self):
        opath = self.get_fp(song_output)
        with open(self.get_fp('image.jpg'), 'rb') as fp:
            pic_data = fp.read()
        tags = {
            'title': 'Why, Judy why',
            'images': {
                'cover': {
                    'mime': 'image/jpeg',
                    'data': pic_data,
                    'type': 3
                }
            }
        }
        write_tags(opath, tags, True)
        written_tags = read_tags(mutagen.File(opath), opath)

        self.assertEqual(written_tags['title'], tags['title'])
        self.assertEqual(len(written_tags['images']), 1)
