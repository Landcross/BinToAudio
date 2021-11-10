import io
import pathlib
from dataclasses import dataclass, field
from typing import List, Optional, Union, IO


@dataclass
class Index:
    number: int
    length: str


@dataclass
class Track:
    number: int
    type: str
    title: Optional[str] = None
    performer: Optional[str] = None
    songwriter: Optional[str] = None
    flags: List[str] = field(default_factory=list)
    isrc: str = None
    pregap: str = None
    postgap: str = None
    indexes: List[Index] = field(default_factory=list)


@dataclass
class File:
    name: str
    type: str
    tracks: List[Track] = field(default_factory=list)


@dataclass
class CueSheet:
    catalog: Optional[str] = None
    cdtextfile: Optional[str] = None
    title: Optional[str] = None
    performer: Optional[str] = None
    songwriter: Optional[str] = None
    files: List[File] = field(default_factory=list)


def parse_cuesheet(file: Union[pathlib.Path, IO]) -> CueSheet:
    if isinstance(file, io.IOBase):
        lines = [l.decode('utf-8').strip() for l in file.readlines()]
    else:
        with open(file, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines()]

    cuesheet = CueSheet()

    current_file = None
    current_track = None

    for line in lines:
        command, data = line.split(' ', 1)

        if command == 'CATALOG':
            cuesheet.catalog = data

        elif command == 'CDTEXTFILE':
            cuesheet.cdtextfile = data

        elif command == 'TITLE':
            clean_data = data.replace('"', '')
            if current_track:
                current_track.title = clean_data

            cuesheet.title = clean_data

        elif command == 'PERFORMER':
            clean_data = data.replace('"', '')
            if current_track:
                current_track.performer = clean_data

            cuesheet.performer = clean_data

        elif command == 'SONGWRITER':
            clean_data = data.replace('"', '')
            if current_track:
                current_track.songwriter = clean_data

            cuesheet.songwriter = clean_data

        elif command == 'FILE':
            if current_file:
                current_file.tracks.append(current_track)
                cuesheet.files.append(current_file)
                current_track = None

            file_name, file_type = data.rsplit(' ', 1)
            clean_file_name = file_name.replace('"', '')
            current_file = File(clean_file_name, file_type)

        elif command == 'TRACK':
            if current_track:
                current_file.tracks.append(current_track)

            track_number, track_type = data.split(' ')
            current_track = Track(int(track_number), track_type)

        elif command == 'FLAGS':
            current_track.flags = data.split(' ')

        elif command == 'ISRC':
            current_track.isrc = data

        elif command == 'PREGAP':
            current_track.pregap = data

        elif command == 'INDEX':
            index_number, index_length = data.split(' ')
            current_track.indexes.append(Index(int(index_number), index_length))

        elif command == 'POSTGAP':
            current_track.postgap = data

        elif command == 'REM':
            pass

        else:
            pass

    current_file.tracks.append(current_track)
    cuesheet.files.append(current_file)

    return cuesheet


def get_track_tags(cuesheet: CueSheet, track_number: int) -> dict:
    tags = {}
    track = None
    track_total = 0

    for f in cuesheet.files:
        for t in f.tracks:
            track_total += 1

            if not track and t.number == track_number:
                track = t

    if not track:
        return tags

    tags['track'] = f'{track.number}/{track_total}'

    if cuesheet.title:
        tags['album'] = cuesheet.title

    if cuesheet.performer:
        tags['album_artist'] = cuesheet.performer

    if cuesheet.songwriter:
        tags['lyricist'] = cuesheet.songwriter

    # if cuesheet.catalog:
    #     tags['catalog'] = cuesheet.catalog

    if track.title:
        tags['title'] = track.title

    if track.performer:
        tags['artist'] = track.performer

    if track.songwriter:
        tags['lyricist'] = track.songwriter

    if track.isrc:
        tags['isrc'] = track.isrc

    return tags
