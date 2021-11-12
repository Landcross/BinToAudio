# BinToAudio
 
This is a simple script to convert bin/cue images into audio (wav/flac/mp3).

## Usage
Install the packages listed in requirements.txt. Then run main.py with the desired arguments (see below).

`main.py [input] [output] [options]`

## Arguments
### Mandatory

`input`
The path to either a cuesheet or a directory containing subfolders with cuesheets.

`output`
The path where the exported files will be saved. The script creates a subfolder per cuesheet. WARNING: at the time of writing the script will overwrite any existing files without warning.

### Optional
`-si | --separate-indexes`

Default: False. By setting this flag, the script will export all indexes within a track separately.

`-ht | --hidden-track`

Default: False. By setting this flag, the script will (try to) detect and extract any hidden track in the pregap of Track 1.

`-p | --pregap [skip start end]`

Default: end. This flag changes how the script handles pregap. Skip skips pregaps completely. Start adds pregaps (where applicable) to the start of the track. End adds pregaps to the end of the previous track (this is the 'standard' EAC/AccurateRip way of handling pregaps).

`-f | --format [wav flac mp3]`

Default: flac. This flag changes the audio format that is being exported.
