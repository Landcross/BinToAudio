import argparse
import io
import os
import pathlib
import sys

from pydub import AudioSegment

from cuesheet import parse_cuesheet, get_track_tags


def length_to_bytes(length: str) -> int:
    minutes, seconds, frames = (int(i) for i in length.split(':'))
    return ((minutes * 60 + seconds) * 75 + frames) * 2352


def export(data: bytes, tags: dict, location, filename: str, output_format: str) -> None:
    path = pathlib.Path(location, filename + '.' + output_format)
    pathlib.Path(location).mkdir(parents=True, exist_ok=True)

    audio = AudioSegment.from_raw(io.BytesIO(data), sample_width=2, frame_rate=44100, channels=2)
    audio.export(path, format=output_format, tags=tags)


def parse_filepath(input_path: pathlib.Path, output_path: pathlib.Path, pregap_handling: str, separate_indexes: bool, output_format: str):
    if not input_path.name.endswith('.cue'):
        print('Not a cuesheet')
        sys.exit(-1)

    cuesheet = parse_cuesheet(input_path)

    if separate_indexes:
        for file in cuesheet.files:
            print('    Converting file ' + file.name)
            with open(os.path.join(input_path.parents[0], file.name), 'rb') as bin_file:
                for track_i, track in enumerate([t for t in file.tracks if t.type == 'AUDIO']):
                    next_track = file.tracks[track_i + 1] if track_i + 1 < len(file.tracks) else None

                    if pregap_handling == 'skip':
                        indexes = [i for i in track.indexes if i.number > 0]
                    else:
                        indexes = track.indexes

                    for index_i, index in enumerate(indexes):
                        next_index = indexes[index_i + 1] if index_i + 1 < len(indexes) else None
                        offset = length_to_bytes(index.length)

                        if next_index:
                            size = length_to_bytes(next_index.length) - offset
                        elif next_track:
                            size = length_to_bytes(next_track.indexes[0].length) - offset
                        else:
                            bin_file.seek(0, 2)
                            size = bin_file.tell() - offset

                        bin_file.seek(offset)
                        filename = file.name.rsplit('.', 1)[0] + f' (Index {str(index.number).zfill(2)})'
                        export(bin_file.read(size), get_track_tags(cuesheet, track.number), os.path.join(output_path, input_path.stem), filename, output_format)

    else:  # No separate indexes
        if pregap_handling == 'skip':
            for file in cuesheet.files:
                print('    Converting file ' + file.name)
                with open(os.path.join(input_path.parents[0], file.name), 'rb') as bin_file:
                    for track_i, track in enumerate([t for t in file.tracks if t.type == 'AUDIO']):
                        next_track = file.tracks[track_i + 1] if track_i + 1 < len(file.tracks) else None

                        start_index = next(i for i in track.indexes if i.number == 1)
                        offset = length_to_bytes(start_index.length)

                        if next_track:
                            size = length_to_bytes(next_track.indexes[0].length) - offset
                        else:
                            bin_file.seek(0, 2)
                            size = bin_file.tell() - offset

                        bin_file.seek(offset)
                        filename = file.name.rsplit('.', 1)[0]
                        export(bin_file.read(size), get_track_tags(cuesheet, track.number), os.path.join(output_path, input_path.stem), filename, output_format)

        elif pregap_handling == 'start':
            for file in cuesheet.files:
                print('    Converting file ' + file.name)
                with open(os.path.join(input_path.parents[0], file.name), 'rb') as bin_file:
                    for track_i, track in enumerate([t for t in file.tracks if t.type == 'AUDIO']):
                        next_track = file.tracks[track_i + 1] if track_i + 1 < len(file.tracks) else None

                        start_index = track.indexes[0]
                        offset = length_to_bytes(start_index.length)

                        if next_track:
                            size = length_to_bytes(next_track.indexes[0].length) - offset
                        else:
                            bin_file.seek(0, 2)
                            size = bin_file.tell() - offset

                        bin_file.seek(offset)
                        filename = file.name.rsplit('.', 1)[0]
                        export(bin_file.read(size), get_track_tags(cuesheet, track.number), os.path.join(output_path, input_path.stem), filename, output_format)

        elif pregap_handling == 'end':
            for file_i, file in enumerate(cuesheet.files):
                print('    Converting file ' + file.name)
                next_file = cuesheet.files[file_i + 1] if file_i + 1 < len(cuesheet.files) else None

                for track_i, track in enumerate([t for t in file.tracks if t.type == 'AUDIO']):
                    next_track = file.tracks[track_i + 1] if track_i + 1 < len(file.tracks) else None

                    start_index = next(i for i in track.indexes if i.number == 1)
                    offset = length_to_bytes(start_index.length)

                    if next_track:
                        end_index = next(i for i in next_track.indexes if i.number == 1)
                        size = length_to_bytes(end_index.length) - offset

                        with open(os.path.join(input_path.parents[0], file.name), 'rb') as bin_file:
                            bin_file.seek(offset)
                            filename = file.name.rsplit('.', 1)[0]
                            export(bin_file.read(size), get_track_tags(cuesheet, track.number), os.path.join(output_path, input_path.stem), filename, output_format)
                    else:
                        with open(os.path.join(input_path.parents[0], file.name), 'rb') as bin_file:
                            bin_file.seek(offset)
                            track_data = bin_file.read()

                        if next_file:
                            try:
                                pregap_start_index = next(i for i in next_file.tracks[0].indexes if i.number == 0)
                                pregap_end_index = next(i for i in next_file.tracks[0].indexes if i.number == 1)

                                with open(os.path.join(input_path.parents[0], next_file.name), 'rb') as bin_file:
                                    bin_file.seek(length_to_bytes(pregap_start_index.length))
                                    track_data += bin_file.read(length_to_bytes(pregap_end_index.length))
                            except StopIteration:
                                pass

                        filename = file.name.rsplit('.', 1)[0]
                        export(track_data, get_track_tags(cuesheet, track.number), os.path.join(output_path, input_path.stem), filename, output_format)
        else:
            pass


def parse_dirpath(input_path: pathlib.Path, output_path: pathlib.Path, pregap_handling, separate_indexes, output_format):
    subdirs = [f for f in os.listdir(input_path) if os.path.isdir(os.path.join(input_path, f))]

    for subdir in subdirs:
        for f in os.listdir(os.path.join(input_path, subdir)):
            if not f.endswith('.cue'):
                continue

            print('Parsing ' + f)
            parse_filepath(pathlib.Path(input_path) / subdir / f, output_path, pregap_handling, separate_indexes, output_format)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=pathlib.Path, help='Path to single cuesheet or folder containing subfolders with cuesheets')
    parser.add_argument('output', type=pathlib.Path, help='Path to folder for exported files')
    parser.add_argument('-si', '--separate-indexes', action='store_true', help='Export indexes as separate files')
    parser.add_argument('-p', '--pregap', choices=['skip', 'start', 'end'], default='end', help='Pregap handling')
    parser.add_argument('-f', '--format', choices=['wav', 'flac', 'mp3'], default='flac', help='Output format')
    # parser.add_argument('-t', '--tags', choices=['none', 'mbid', 'cue'], default='none', help='Tags')

    args = parser.parse_args()

    path: pathlib.Path = args.input

    if path.is_file():
        parse_filepath(path, args.output, args.pregap, args.separate_indexes, args.format)
    elif path.is_dir():
        parse_dirpath(path, args.output, args.pregap, args.separate_indexes, args.format)
    else:
        pass


if __name__ == '__main__':
    main()
