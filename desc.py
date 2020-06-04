#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "John Doe"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
import re
import chess.pgn
import sys

class Config(object):
    def __init__(self, sep_capture='x', sep_move='-—', check_sign=['ch','dbl ch','+','#','mate'], start_fen='', index=.5,verbose=0):
        self.sep_capture=sep_capture
        self.sep_move=sep_move
        self.check_sign=check_sign
        self.start_fen=start_fen
        self.index=index
        self.punctuation=[',','.','(',')']
        self.move_regex=re.compile("(\(?[0-9]{0,3}\)?\s?\.{0,3})?\s*(?:([KQ]?(?:[QKRBNP]|Kt))([.\/][QK]?(?:[RBN]|Kt)?[1-8]|\((?:[QK]?(?:[RBN]|Kt)?[1-8])\)|[1-8]?)?\s*(["+sep_move+sep_capture+"])\s*(?:([KQ]?(?:[QKRBN]|Kt)[1-8])|([KQ]?(?:[RBN]|Kt)?(?:[QRBNP]|Kt))([.\/][QK]?(?:[RBN]|Kt)?[1-8]|\((?:[QK]?(?:[RBN]|Kt)?[1-8])\)|[1-8]?)?)(\((?:[QRBN]|Kt)\)|=(?:[QRBN]|Kt)|\/(?:[QRBN]|Kt))?|(O-O-O|O-O|0-0|0-0-0|castles|long castles))\s*\(?(ch|dbl ch|mate|[+\-=!?≠∓±#]{1,2})?",flags=re.I)
        self.nag_dict={
            '!':1,
            '?':2,
            '!!':3,
            '??':4,
            '!?':5,
            '?!':6
        }
        self.verbose=verbose

class move_c():
    def __init__(self,f_c=set('abcdefgh'),f_r=set('12345678'),t_c=set('abcdefgh'),t_r=set('12345678'),moves=None):
        self.f_c=f_c
        self.f_r=f_r
        self.t_c=t_c
        self.t_r=t_r
        self.f_m=None
        self.t_m=None
        self.moves=moves
    def set_rc(self,case,val):
        cases={
            0:'f_c',
            1:'f_r',
            2:'t_c',
            3:'t_r'
        }
        setattr(self,cases[case],val)
    def set_moves(self,case,val):
        cases={
            0:'f_m',
            1:'t_m',
            2:'moves'
        }
        k=getattr(self,cases[case])
        if k: setattr(self,cases[case],k.intersection(val))
        else: setattr(self,cases[case],val)
    def possibles(self,promotion=''):
        if self.f_m and self.t_m:
            l=set()
            for i1 in self.f_m:
                for i2 in self.t_m:
                    k=i1+i2+promotion
                    if k in self.moves:
                        l.add(k)
        else:
            l={x for x in self.moves if (not self.f_m or x[:2] in self.f_m) and (not self.t_m or x[2:4] in self.t_m)}
        if promotion:
            l={x for x in l if x[-1]==promotion and x[0] in self.f_c and x[1] in self.f_r and x[2] in self.t_c and x[3] in self.t_r}
        else:
            l={x for x in l if x[0] in self.f_c and x[1] in self.f_r and x[2] in self.t_c and x[3] in self.t_r}
        return l
    def printstuff(self):
        print("---")
        print(self.f_c)
        print(self.f_r)
        print(self.t_c)
        print(self.t_r)
        print(self.f_m)
        print(self.t_m)
        print(self.moves)
        print("---")

def squareset_uci(i):
    letter_dict='abcdefgh'
    return letter_dict[i%8]+str(i//8+1)

def arr_to_comment(arr):
    move_arr=arr.copy()
    if move_arr[0] and move_arr[0][-1]!=' ':
        move_arr[0]+=' '
    if move_arr[10] and move_arr[10][0]!=' ':
        move_arr[10]=' '+move_arr[10]
    if move_arr[3] is not None:
        move_arr[3]=move_arr[3].lower()
    return ' '+''.join([x for x in move_arr if x is not None])+' '

def only_punctuation(s,pset):
    for i in s:
        if i not in pset:
            return s
    else:
        return ''
    

def number_to_index(num,index,move):
    try:
        k=int(''.join([x for x in num if x.isdigit()]))
        if '..' in num or num.strip()=='':
            return k+.5
        return k
    except:
        if isinstance(index,float) and not index.is_integer():
            print(f'Index {index} needs disambiguation. Assuming value of {index}. Move: {move}')
            return index+.5
        return index+.5
    
            
def none_to_empty(k):
    if k is None:
        return ''
    return k

def to_nag(s,config):
    s=none_to_empty(s)
    val=re.findall(re.compile("(!!|!\?|\?!|\?\?|!|\?)"),s)
    s=re.sub('\(?(!!|!\?|\?!|\?\?|!|\?)\)?', '', s)
    nags={config.nag_dict[x] for x in val}
    return nags,s

class qerror(object):
    def __init__(self,index,move,verbose,board=None):
        self.verbose=verbose
        self.index=index
        self.move=move
        self.errors=[]
        self.board=board
    def add(self,*args):
        self.errors.append(list(args))
    def spit(self):
        if self.verbose==0:
            pass
        if self.verbose>=1 and len(self.errors)>0:
            for i in self.errors:
                print(i)
        if self.verbose>=2:
            for i in self.board:
                    print(i.uci()+' ',end='')

def colorc(i,color):
    if color:
        return i
    else:
        return str(9-int(i))

s_dict={
    'R':{'a','h'},
    'N':{'b','g'},
    'B':{'c','f'},
    'Q':{'d'},
    'K':{'e'},
    'QR':{'a'},
    'QN':{'b'},
    'QB':{'c'},
    'KR':{'h'},
    'KN':{'g'},
    'KB':{'f'}
}

pt_dict={
    'P':1,
    'N':2,
    'B':3,
    'R':4,
    'Q':5,
    'K':6
}

def convert_to_set(move,board,config,qe):
    color=True
    promotion=''
    legalmoves={x.uci() for x in board.legal_moves}
    move_object=move_c(moves=legalmoves)
    if '..' in move[0] or move[0].strip()=='':
        color=False
    for i in range(1,len(move[:-1])):
        if move[i] is not None:
            if i==3:
                move[i]=move[i].lower()
            else:
                move[i]=move[i].upper()
            move[i]=move[i].replace('KT','N')
    if move[8] in ['O-O','0-0','CASTLES']:
        if color: return {'e1g1'}
        else: return {'e8g8'}
    elif move[8] in ['O-O-O','0-0-0','LONG CASTLES']:
        if color: return {'e1c1'}
        else: return {'e8c8'}
    else:
        if move[7]:
            i=0
            l=[x for x in move[6] if x in ['N','B','R','Q']]
            if len(l)!=1:
                qe.add('promotion error')
            else:
                promotion=l[0].lower()
        squareset=board.pieces(piece_type=pt_dict[move[1][-1]],color=color)
        fromsquares={squareset_uci(x) for x in squareset}
        move_object.set_moves(0,fromsquares)
        if len(move[1])>1:
            if move[2]:
                qe.add("possible from_move redudancy/error")
            if move[1][0]=='Q':
                move_object.set_rc(0,{'a','b','c','d'})
            else:
                move_object.set_rc(0,{'e','f','g','h'})
        if move[2]:
            try:
                val=re.search(re.compile("([QK]?(?:[RBN]|Kt))?([0-9])"),move[2])
                if val.group(1):
                    move_object.set_rc(0,s_dict[val.group(1)])
                move_object.set_rc(1,colorc(val.group(2),color))
            except:
                qe.add("from_move error")
        if move[5]:
            if move[3] not in config.sep_capture:
                c=s_dict[move[5]]
                move_object.set_rc(2,c)
            else:
                squareset=board.pieces(piece_type=pt_dict[move[5][-1]],color=not color)
                tosquares={squareset_uci(x) for x in squareset}
                move_object.set_moves(1,tosquares)
                if len(move[5])>1:
                    if move[6]: qe.add("possible to_move redudancy/error")
                    move_object.set_rc(2,s_dict[move[5][:-1]])
            if move[6]:
                try:
                    val=re.search(re.compile("([QK]?(?:[RBN]|Kt))?([0-9])"),move[6])
                    if val.group(1):
                        move_object.set_rc(2,s_dict[val.group(1)])
                    move_object.set_rc(3,colorc(val.group(2),color))
                except:
                    qe.add("to_move disambugate error")
        else:
            move_object.set_rc(3,colorc(move[4][-1],color))
            try:
                c=s_dict[move[4][:-1]]
                move_object.set_rc(2,c)
            except:
                qe.add("to_move error")
        possibles=move_object.possibles(promotion)
        if move[9] in config.check_sign:
            possibles={x for x in possibles if board.gives_check(chess.Move.from_uci(x))}
        if len(possibles)==0:
            qe.add('No possible moves found')
            if config.verbose>=1:
                move_object.printstuff()
        return possibles

def pgn_builder(movelist,config,output):
    index=config.index
    if config.start_fen:
        game = chess.Board(setup=config.start_fen)
    else:
        game = chess.Board()
    rootnode=chess.pgn.Game(setup=game)
    node=rootnode
    savednode=None
    savedmove=None
    side_index=0.0
    temp_index=0.0
    commentline=''
    sideline_depth=0

    for move_arr in movelist:
        if config.verbose>=1:
            print(move_arr)
        if temp_index:
            k=number_to_index(move_arr[0],temp_index,move_arr)
        elif side_index:
            k=number_to_index(move_arr[0],side_index,move_arr)
        else:
            k=number_to_index(move_arr[0],index,move_arr)
        qe=qerror(k,move_arr,config.verbose,board=game.move_stack)
        if k==index+.5 and k!=side_index+.5 and k!=temp_index+.5:
            if config.verbose>=1:
                print(k,index,side_index,temp_index,"level 1")
            node.comment+=only_punctuation(commentline,config.punctuation)
            commentline=''
            if side_index:
                node=savednode
                savednode=None
                for t in range(sideline_depth):
                    game.pop()
                game.push(savedmove)
                savedmove=None
                sideline_depth=0
                side_index=0.0
            temp_index=0.0
            moveuci=convert_to_set(move_arr[0:-1],game,config,qe)
            if len(moveuci)!=1:
                qe.add('Error',str(moveuci))
                temp_index=k
                commentline+=arr_to_comment(move_arr)
                continue
            move=chess.Move.from_uci(moveuci.pop())
            game.push(move)
            node = node.add_variation(move)
            nag,remainder=to_nag(move_arr[-2],config)
            node.comment=only_punctuation(remainder+none_to_empty(move_arr[-1]),config.punctuation)
            node.nags.update(nag)
            index+=.5
        elif k==index and k!=temp_index+.5:
            if config.verbose>=1:
                print(k,index,side_index,temp_index,"level 2")
            node.comment+=only_punctuation(commentline,config.punctuation)
            commentline=''
            for t in range(sideline_depth):
                game.pop()
            if savednode is not None and savedmove is not None:
                node=savednode
                game.push(savedmove)
            sideline_depth=0
            side_index=0.0
            temp_index=0.0
            savednode=node
            savedmove=game.pop()
            side_index=k
            moveuci=convert_to_set(move_arr[0:-1],game,config,qe)
            if len(moveuci)!=1:
                qe.add('Error',str(moveuci))
            move=chess.Move.from_uci(moveuci.pop())
            game.push(move)
            sideline_depth+=1
            node = node.parent.add_variation(move)
            nag,remainder=to_nag(move_arr[-2],config)
            node.comment=only_punctuation(remainder+none_to_empty(move_arr[-1]),config.punctuation)
            node.nags.update(nag)
        elif k==side_index+.5 and k!=temp_index+.5:
            temp_index=0
            if config.verbose>=1:
                print(k,index,side_index,temp_index,"level 3")
            try:
                moveuci=convert_to_set(move_arr[0:-1],game,config,qe)
                if len(moveuci)!=1:
                    temp_index=k
                    commentline+=arr_to_comment(move_arr)
                    continue
            except:
                temp_index=k
                commentline+=arr_to_comment(move_arr)
                continue
            node.comment+=only_punctuation(commentline,config.punctuation)
            commentline=''
            move=chess.Move.from_uci(moveuci.pop())
            game.push(move)
            sideline_depth+=1
            node = node.add_variation(move)
            nag,remainder=to_nag(move_arr[-2],config)
            node.comment=only_punctuation(remainder+none_to_empty(move_arr[-1]),config.punctuation)
            node.nags.update(nag)
            side_index+=.5
        else:
            if config.verbose>=1:
                print(k,index,side_index,temp_index,"level 4")
            temp_index=k
            commentline+=arr_to_comment(move_arr)
        qe.spit()
    node.comment+=only_punctuation(commentline,config.punctuation)
    new_pgn = open(output, "w", encoding="utf-8")
    exporter = chess.pgn.FileExporter(new_pgn)
    rootnode.accept(exporter)

def to_movelist(source,config):
    split_list=re.split(config.move_regex,source)
    split_list.pop(0)
    split_list=[x.strip() if x is not None else x for x in split_list]
    movelist=[]
    for i in range(0,len(split_list),11):
        movelist.append(split_list[i:i+11])
    if config.verbose>1:
        for i in movelist:
            print(i)
    return movelist

def formatinput(args):
    config=Config(verbose=args.verbose)
    try:
        with open(args.input,'r') as file:
            source=file.read()
    except:
        print("File not found")
    movelist=to_movelist(source,config)
    try:
        with open(args.input+".tsv",'w') as file:
            for i in range(len(movelist)):
                file.write('\t'.join([none_to_empty(x) for x in movelist[i]])+'\n')
        return
    except:
        print("writing error")

def main(args):
    """ Main entry point of the app """
    config=Config(verbose=args.verbose, setup=args.setup)
    if args.test:
        source="""10 Alekhine—Chajes 
        Carlsbad 1923, 
        Queen’s Gambit 

1P-Q4 N-KB3 2P-QB4 P-K3 3 N-KB P-Q4 4 N-B3 QN-Q2 5 B-N5 B-K2 6P-K3 0-0 7 R-B1 p-B3 8 Q-B2 P-QR3 9 P-QR3 R-K1 10 P-R3 P-N4 11 P-B5 N-R4 12 B-KB4! NxB 13 PxN P-QR4 14 B-Q3 P-N3 15 P-KR4! B-B3 16 P-R5 N-B1 17 P-KN3 R-R2 18 N-Q1! B-KN2 19 N-K3  P-B4 20 Q-K2! P-R5? 21 N-B2 R2-K2 22 K-B1 B-B3 23 N-K5 BxN (?) better was 
(?) 23 ... Q-B2! when White would have to continue 24 N-B3 followed by N-N4, B-N1, N-Q3 and N-K5 
24 QxB Q-B2 25 Q-B6! R-B2 26 Q-R4 Q-K2 27 PxP! NxP 28 Q-R5 Q-B3 29 B-K2 R-KN2 30 Q-B3 N-B1 31  Q-K3   R1-K2  32 N-N4 B-Q2 33 B-R5 N-N3 (15) """
        print(source)
        print("")
        print(vars(config))
    else:
        with open(args.input,'r') as file: 
            source=file.read()
    source=source.replace('\t','')
    source=source.replace('\n',' ')
    movelist=to_movelist(source,config)
    pgn_builder(movelist, config, args.output)

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--format", help="format the text as regex would parse it and return a tsv file", action="store_true", default=False)
    parser.add_argument("-t", "--test", help="Parse an example input", action="store_true", default=False)
    parser.add_argument("-i", "--input", help="Defaults to a file called input", action="store", default="input")
    parser.add_argument("-o", "--output", action="store", help="Defaults to a file called output", default="output.pgn", dest="output")
    parser.add_argument("-s", "--setup", help="fen starting position", action="store", default='')

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
    if args.format:
        formatinput(args)
    else: main(args)
