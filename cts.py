#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "John Doe"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
import os, re
from copy import copy
import chess.pgn
from easytts import to_voice, list_voices

nag_dict=['!','?','!!','??','!?','?!']
piece_dict=['','Pawn','Knight','Bishop','Rook','Queen','King']
comment_dict={
    'P':'Pawn ',
    'N':'Knight ',
    'B':'Bishop ',
    'R':'Rook ',
    'Q':'Queen ',
    'K':'King ',
    'x':' takes ',
    'X':' takes ',
    '+':' check ',
    '#':' checkmate '
}

def none_to_empty(k):
    if k is None:
        return ''
    return k

def process_comment(string):
    r=re.compile("([PNBRQK]|[a-e])(x?)([a-h][1-8])([+#]?)")
    string=re.sub(r'O-O',"castles",string)
    string=re.sub(r'O-O-O',"long castles",string)
    k=re.split(r,string)
    for i in range(len(k)):
        if i%5 in [1,2,4]:
            if k[i]:
                k[i]=comment_dict.get(k[i],k[i])
    
    return ''.join(k)

class Moveobj(object):
    def __init__(self,move,piece,capture,index=0.0,comment="",starting_comment="",nags=""):
        self.move=move
        self.comment=process_comment(comment.strip())
        self.starting_comment=process_comment(starting_comment.strip())
        self.nags=nags
        self.piece=piece
        self.capture=capture
        self.index=index
    def addstarting(self,comment):
        self.starting_comment=process_comment(comment.strip())
    def addcomment(self,comment):
        self.comment=process_comment(comment.strip())
    def addnag(self,nags):
        # comment=" ".join([nag_dict[x] for x in nags])+comment
        pass
    def __str__(self):
        try:
            return self.move.uci()
        except: return ("Root")
    def __repr__(self):
        try:
            return self.move.uci()
        except: return ("Root")

def to_movelist(node,index,nocomments,l=[]):
    if node.move:
        board=copy(node.board())
        board.pop()
        piece=board.piece_at(node.move.from_square)
        capture=board.piece_at(node.move.to_square)
        move=Moveobj(node.move,piece,capture,index=index)
        index+=.5
    else: move=Moveobj('',None,None)
    if not nocomments:
        if node.comment:
            move.addcomment(node.comment)
        if node.starting_comment:
            move.addstarting(node.starting_comment)
        if node.nags:
            move.addnag(node.nags)
    l.append(move)
    if node.is_end():
        return l
    else:
        variations=[]
        for i in node.variations:
            if i.is_main_variation():
                main=i
            else:
                variations.append(i)
        for i in variations:
            l.append(to_movelist(i,index,nocomments,l=[]))
        to_movelist(main,index,nocomments,l=l)
    return l

def to_text(movelist, noindex, break_duration, startsvariation=False):
    textlist=[]
    for i in movelist:
        if isinstance(i, list):
            textlist.append(to_text(i, noindex, break_duration, startsvariation=True))
            textlist.append("returning to the previous board:")
            continue
        sentence=i.starting_comment
        if sentence and not sentence[-1] in ['.','!','?']:
                sentence+="."
        if startsvariation:
            sentence+="If "
            if i.index.is_integer:
                sentence+=str(int(i.index))
            else:
                sentence+=str(i.index)
            sentence+="."
        elif not noindex and i.index.is_integer():
            sentence+=str(int(i.index))+"."
        if i.piece.piece_type==6 and (i.move.uci()=='e1g1' or i.move.uci()=='e8g8'):
            sentence+=" castles "
        elif i.piece.piece_type==6 and (i.move.uci()=='e1c1' or i.move.uci()=='e8c8'):
            sentence+=" long castles "
        else:
            sentence+=" "+piece_dict[i.piece.piece_type]+" "
            sentence+=chess.SQUARE_NAMES[i.move.from_square]
            if i.capture:
                sentence+=" takes "
                sentence+=piece_dict[i.capture.piece_type]+" "
            else:
                sentence+=" to "
            sentence+=chess.SQUARE_NAMES[i.move.to_square]
        sentence+=f'. <break time="{break_duration}"/>'
        if i.comment:
            sentence+=i.comment
            sentence+=f'<break time="{break_duration*.75}"/>'
        if startsvariation:
            sentence+=" Then"
            startsvariation=False
        textlist.append(sentence)
    result='\n'.join(textlist)
    return result
def getFileType(sdir,types=['.pgn']):
    files=[]
    for filename in os.listdir(sdir):
            for ending in types:
                if filename.endswith(ending):
                    files.append(os.path.join(sdir,filename))
    return files

def main(args):
    """ Main entry point of the app """
    if args.verbose>=1:
        print(args)
    if args.listvoices:
        q=input("to list all voices enter a, otherwise voices according to set and default parameters will be listed")
        if q=='a':
            print(list_voices(allvoices=True))
        else:
            k=list_voices(wavenet=args.wavenet,gender=args.gender,lancode=args.lancode)
            for x in k:
                print(x)
    else:
        if args.source:
            with open(args.source,'r') as file:
                while True:
                    Game=chess.pgn.read_game(file)
                    if Game is None:
                        break
                    output=Game.headers["Event"]+": "+Game.headers["White"]+" - "+Game.headers["Black"]
                    movelist=to_movelist(Game,1.0,args.nocomments,l=[])[1:]
                    if args.verbose>=1:
                        print(output)
                        print(movelist)
                    text=to_text(movelist,args.noindex,args.pause)
                    if args.transcript:
                        with open(args.transcript,'a') as tfile:
                            tfile.write(output+'\n')
                            tfile.write(text)
                    if not args.silent:
                        to_voice(text,speed=args.speed, pitch=args.pitch, lancode=args.lancode, gender=args.gender,letter=args.choice,name=args.name,wavenet=args.wavenet,output=args.folder+output+'.mp3', verbose=args.verbose)
        else:
            k=getFileType(sdir=args.directory)
            for filename in k:
                with open(filename,'r') as file: 
                    Game=chess.pgn.read_game(file)
                movelist=to_movelist(Game,1.0,args.nocomments)[1:]
                text=to_text(movelist,args.noindex,args.pause)
                if args.transcript:
                        with open(args.transcript,'a') as tfile:
                            tfile.write(output+'\n')
                            tfile.write(text)
                if not args.silent:
                    to_voice(text,speed=args.speed, pitch=args.pitch, lancode=args.lancode, gender=args.gender,letter=args.choice,name=args.name,wavenet=args.wavenet,output=args.folder+filename[:-4]+'.mp3',verbose=args.verbose)


if __name__ == "__main__":
    """ Read pgn files aloud """
    parser = argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group()
    group.add_argument("-i", "--input", action="store", dest="source")
    group.add_argument("-d", "--directory", help="default .", action="store", default=".")
    group.add_argument("--folder", help="specify path to folder (ends with '/')", action="store", default="")
    parser.add_argument("--noindex", help="Don't say move index", action="store_true", default=False)
    parser.add_argument("--nocomments", help="Don't say comments", action="store_true", default=False)
    parser.add_argument("--silent", help="No audio", action="store_true", default=False)
    parser.add_argument("-t","--transcript", action="store")
    parser.add_argument("-s", "--speed", action="store", default=0.66, help="0.25 -> 4, default 0.8", type=float)
    parser.add_argument("--breaklength", action="store", default=2.5, help="length of pause between moves", type=float, dest='pause')
    parser.add_argument("-g", "--gender", action="store", help="1: MALE, 2: FEMALE, default 1", default=1, type=int)
    parser.add_argument("-p", "--pitch", action="store", help="[-20,20]", default=0, type=float)
    parser.add_argument("-l", "--lancode", action="store", help="BCP-47", default='en-US')
    parser.add_argument("-c", "--choice", action="store", help="Which voice satisfying givern Standard/Wavenet and Language code", type=int)
    parser.add_argument("-w", "--wavenet", help="Whether to use wavenet technology when using the choice flag", action="store_true", default=False)
    parser.add_argument("--listvoices", help="lists language and name options", action="store_true", default=False)
    parser.add_argument("-n","--name", action="store", help="cloud.google.com/text-to-speech/docs/voices")

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
