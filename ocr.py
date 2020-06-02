#!/usr/bin/env python3
"""
Perform ocr on pdf with pytesseract.
"""

__author__ = "Richard Zhang"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
from PIL import Image
from pdf2image import convert_from_path, convert_from_bytes
import pytesseract
import PyPDF2
import os, shutil, sys
import concurrent.futures, threading

class AtomicCounter(object):
    
        def __init__(self, initial=0):
            self._value = initial
            self._lock = threading.Lock()
    
        def inc(self, num=1):
            with self._lock:
                self._value += num
                return self._value
    
        @property
        def val(self):
            return self._value


def main(args):
    """ Main entry point of the app """
    if args.source is None:
        inputFile=[]
        for filename in os.listdir("."):
            if filename.endswith('.pdf'):
                inputFile.append(filename)
        if len(inputFile)>1:
            print("More than 1 pdf file, choosing first one")
        source=inputFile[0]
    else: source = args.source
    tempfolder=args.tempfolder
    chunk=args.chunk
    if args.replace:
        args.dest=source

    try:
        os.makedirs(tempfolder)
        print("Processing...")
        images_from_path = convert_from_path(source, output_folder=tempfolder)
    except:
        print("tempfolder already exists, trying to use existing files")
        k=input("press any key to continue")

    ppmFiles = []
    for filename in os.listdir(tempfolder):
        if filename.endswith('.ppm'):
            ppmFiles.append(filename)
    ppmFiles.sort(key=str.lower)
    total=len(ppmFiles)
    progress=[int((x+1)*total/chunk) for x in range(chunk)]
    count=AtomicCounter()

    def ocr(i):
        pdf = pytesseract.image_to_pdf_or_hocr(tempfolder+i, extension='pdf')
        count.inc()
        with open(tempfolder+i[-9:-4]+'.pdf', 'w+b') as f:
            f.write(pdf)
        try:
            k=progress.index(count.val)
            print(f"Finished {int(count/total*100)}%: {count.val} pages")
        except:
            pass

    print("Starting conversion...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        executor.map(ocr,ppmFiles)
    pdfFiles = []
    for filename in os.listdir(tempfolder):
        if filename.endswith('.pdf'):
            pdfFiles.append(filename)
    pdfFiles.sort(key=str.lower)
    pdfWriter = PyPDF2.PdfFileWriter()

    for file in pdfFiles:
        rfile = open(tempfolder+file, 'rb')
        pdfReader = PyPDF2.PdfFileReader(rfile)
        pdfWriter.addPage(pdfReader.getPage(0))

    with open(args.dest, 'wb') as outputFile:
        pdfWriter.write(outputFile)

    if args.keep:
        shutil.rmtree(tempfolder)

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser(description="Perform ocr on pdf with pytesseract. Requires tesseract to be installed and has PIL, pytesseract and pdf2image as python dependencies")

    parser.add_argument("--chunk", type=int, default=10, dest="chunk")
    parser.add_argument("-t", type=int, default=2, dest="threads")
    parser.add_argument("--temp", default="tempfolder/", dest="tempfolder")
    parser.add_argument("-in", dest="source")
    parser.add_argument("-out", default="processed.pdf", dest="dest")
    parser.add_argument("-k", "--keep", action="store_false", default=True, dest="keep")
    parser.add_argument("-r", "--replace", action="store_false", default=True, dest="replace")

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    main(args)
