# Chess Tools
> Work in progress

Some simple python scripts.

Descriptive to algebraic converter. Use OCR on your pdf and copy the text to an input file. Supports comments, nags.

Text to speech converter. Processes chess pgns into readable text and converts to audio via Google tts

## Installation

#### Descriptive to Algebraic

##### 	ocr.py

Requires: tesseract. [Installation](https://github.com/tesseract-ocr/tesseract)

OS X & Linux:

```sh
pip install pytesseract PyPDF2 pillow
```

##### 	desc.py

OS X & Linux:

```sh
pip install python-chess
```

#### Read pgn

##### 		easytts.py

OS X & Linux:

```sh
pip install --upgrade google-cloud-texttospeech pydub
```

Follow https://cloud.google.com/text-to-speech/docs/reference/libraries to set up authentication.

##### 	cts.py

Needs easytts.py importable

OS X & Linux:

```sh
pip install python-chess
```

## Usage

#### Descriptive to Algebraic

##### 	ocr.py

Standalone ocr script.

use -h for help.

##### 	desc.py

Flexible descriptive to algebraic notation converter.

Can parse variations, [different forms of descriptive notation](https://en.wikipedia.org/wiki/Descriptive_notation), comments reasonably intelligently. Supports 1 level of variations, further variations become comments. Verbose mode shows more information about errors and Regex groups used in parsing. Moves can be commented out by prefixing with # (not including the move number).

#### Pgn to speech

##### 	tts.py

Standalone text to speech library. Takes [ssml](https://cloud.google.com/text-to-speech/docs/ssml). Pieces ssml over 5000 characters long to overcome Google api limitations.

use -h for help.

##### 	cts.py

Converts pgn files to normal speech and uses tts.py to read the result. Try using it as blindfold training.

use -h for help.

## Release History

* 0.1.0
    * The first release

## Meta

Anonymous (for now) 

Distributed under the CC-BY-NC license. See ``LICENSE`` for more information.

## Contributing

1. Fork it (<https://github.com/yourname/yourproject/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request
