import mutagen
from mutagen import id3
from mutagen.id3 import PictureType
from datetime import timedelta
from os import path

from helpers import image_is_valid


class ID3TagEditor:

    def __init__(self, path: str):
        self.path = path
        self.open_file(path)

    def open_file(self, path: str):
        self.tags = id3.ID3(path)

    def read(self) -> dict:
        return {
            "title": self.get_title(),
            "genre": self.get_genre(),
            "artists": self.get_artists(),
            "album": self.get_album(),
            "albumArtist": self.get_album_artist(),
            "trackNumber": self.get_track_number(),
            "releaseYear": self.get_release_year(),
            "images": self.get_images()
        }

    def write(self, tags: dict, embed_images: bool):
        frames = []

        if title := tags.get("title"):
            frames.append(id3.TIT2(text=title))
        if genre := tags.get("genre"):
            frames.append(id3.TCON(text=genre))
        if year := tags.get("releaseYear"):
            frames.append(id3.TDRL(text=year))

        if "album" in tags.keys():
            frames.append(id3.TALB(text=tags["album"]))
            if 'number' in tags.keys():
                frames.append(id3.TRCK(text=tags['number']))
            # Use album artist as lead artist
            if 'albumArtist' in tags.keys():
                frames.append(id3.TPE1(text=tags['albumArtist']))
            others = [x for x in tags.get(
                'artists', []) if x != tags.get('albumArtist', '')]
            frames.append(id3.TPE2(text=others))

        elif artists := tags.get('artists'):
            frames.append(id3.TPE1(text=artists))

        if embed_images:
            for desc, info in tags.get("images", {}).items():
                frames.append(
                    id3.APIC(
                        type=info['type'], data=info['data'], mime=info['mime'], desc=desc
                    )
                )

        new_tags = id3.ID3(self.path)
        new_tags.delete()
        for frame in frames:
            new_tags.add(frame)
        new_tags.save()

    def get_title(self) -> str:
        if tag := self.tags.get('TIT2'):
            return tag.text[0]
        return ""

    def get_genre(self) -> str:
        if tag := self.tags.get('TCON'):
            return tag.genres[0]
        return ""

    def get_artists(self) -> set:
        artists = set()

        for tname in ['TPE1', 'TPE2']:
            if tag := self.tags.get(tname):
                for artist in tag.text:
                    artists.add(artist)
        return artists

    def get_album(self) -> str:
        if tag := self.tags.get('TALB'):
            return tag.text[0]
        return ""

    def get_album_artist(self) -> str:
        '''Lead artist is used for album artist'''
        if tag := self.tags.get('TPE1'):
            return tag.text[0]
        return ""

    def get_track_number(self) -> int:
        if tag := self.tags.get('TRCK'):
            data = tag.text[0].split('/')
            return int(data[0])
        return 1

    def get_release_year(self) -> int:
        if tag := self.tags.get('TDRL'):
            return int(tag.text[0].get_text()[:4])
        # Alternatively use recording time
        if tag := self.tags.get('TDRC'):
            return int(tag.text[0].get_text()[:4])
        return 0

    def get_images(self) -> dict:
        image_keys = [x for x in self.tags.keys() if x.startswith('APIC')]
        images = {}

        for key in image_keys:
            tag = self.tags.get(key)
            if tag.type in [PictureType.COVER_FRONT, PictureType.MEDIA,
                            PictureType.LEAD_ARTIST, PictureType.ARTIST,
                            PictureType.BAND, PictureType.BAND_LOGOTYPE]:
                if image_is_valid(buffer=tag.data):
                    images[tag.desc] = {
                        'mime': tag.mime,
                        'type': tag.type,
                        'data': tag.data,
                    }
        return images


def read_tags(file: mutagen.FileType, path: str):
    # file param is necessary to obtain the duration
    if isinstance(file.tags, id3.ID3):
        data = ID3TagEditor(path).read()
        data["duration"] = timedelta(seconds=file.info.length)
        return data
    return None


def write_tags(filepath: str, tags: dict, embed_images: bool = False):
    mfile = mutagen.File(filepath)
    fname, ext = path.splitext(filepath)
    if isinstance(mfile.tags, id3.ID3):
        ID3TagEditor(filepath).write(tags, embed_images)
