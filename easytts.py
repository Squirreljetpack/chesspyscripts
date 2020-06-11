#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "John Doe"
__version__ = "0.1.0"
__license__ = "MIT"

from functools import reduce
from time import sleep
import argparse, re, tempfile, time
from google.cloud import texttospeech
from pydub import AudioSegment

class VoiceName(object):
    def __init__(self,letter,lancode='en-US',wavenet=True):
        self.lancode=lancode
        self.wavenet=wavenet
        self.letter=letter
    def spit(self):
        if self.wavenet:
            tech='Wavenet'
        else:
            tech='Standard'
        return '-'.join([self.lancode,tech,'ABCDEFGHIJK'[self.letter]])

def write_file(source, dest):
    with open(dest, 'wb') as out:
        out.write(source)
        print(f'Audio content written to file {dest}')
    return

def to_voice_wrapper(text,speed=1,pitch=0, lancode='en-US', gender=1, letter=None, name=None,wavenet=False,output='output.mp3',verbose=0,retry=60):
    while True:
        try:
            to_voice(text,speed=speed, pitch=pitch, lancode=lancode, gender=gender,letter=letter,name=name,wavenet=wavenet,output=output,verbose=verbose)
            return
        except Exception as e:
            if verbose:
                print(str(e))
            print(f"Failed. Retrying in {retry} seconds...")
            sleep(retry)


def to_voice(text,speed=1,pitch=0, lancode='en-US', gender=1, letter=None, name=None,wavenet=False,output='output.mp3',verbose=0):
    client = texttospeech.TextToSpeechClient()

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("Male")
    if letter:
        voicename=VoiceName(letter,lancode=lancode,wavenet=wavenet)

        voice = texttospeech.types.VoiceSelectionParams(
            name=voicename.spit(), language_code=lancode)
    else:
        voice = texttospeech.types.VoiceSelectionParams(
        language_code=lancode,
        #No neutral voices
        ssml_gender=gender,name=name)
    
    # Select the type of audio file you want returned
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3, speaking_rate=speed, pitch=pitch)

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type

    if verbose:
        print("Requesting response...")
        print(voice)

    if len(text)>5000:
        text_stack=[]
        while len(text)>4992:
            i=4983
            while text[i]!="\n":
                i-=1
            text_stack.append(text[:i+1])
            text=text[i+1:]
        text_stack.append('<speak>'+text)
        text_stack[0]+='</speak>'
        for i in range(1,len(text_stack)-1):
            text_stack[i]='<speak>'+text_stack[i]+'</speak>'
        fnames=[]
        with tempfile.TemporaryDirectory() as tmpdirname:
            for i in range(len(text_stack)):
                synthesis_input = texttospeech.types.SynthesisInput(ssml=text_stack[i])
                response = client.synthesize_speech(synthesis_input, voice, audio_config)
                fname=tmpdirname+'/'+str(i)+'.mp3'
                write_file(response.audio_content,fname)
                fnames.append(fname)
            if verbose:
                print("Stitching audio together...")
            segments = [AudioSegment.from_mp3(f) for f in fnames]
        audio = reduce(lambda a, b: a + b, segments)
        audio.export(output, format='mp3')
        print(f'Audio content written to file {output}')
    else:
        # Set the text input to be synthesized
        synthesis_input = texttospeech.types.SynthesisInput(ssml=text)
        response = client.synthesize_speech(synthesis_input, voice, audio_config)
        # The response's audio_content is binary.
        write_file(response.audio_content,output)
def list_voices(wavenet=None,lancode=None,gender=None,allvoices=False):
    client = texttospeech.TextToSpeechClient()
    request = client.list_voices(language_code=lancode).voices
    if allvoices:
        return [x.name for x in request]
    else:
        if wavenet is not None:
            r=re.compile("Wavenet",flags=re.I)
            if wavenet:
                request=[x for x in request if r.search(x.name)]
            else:
                request=[x for x in request if not r.search(x.name)]
        if gender is not None:
            request=[x for x in request if x.ssml_gender==gender]
        return [x for x in request]

def main(args):
    if args.list:
        print(list_voices())
    else:
        to_voice(args.input,verbose=args.verbose)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('input',nargs='?',default='<speak> Hello <break time="2.5s"/> There </speak>')
    parser.add_argument("-l", "--list", action="store_true", default=False)

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbosity (-v, -vv, etc)")

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    main(args)
