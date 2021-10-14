#! /usr/bin/env python
# -*- coding:utf-8 -*-
# 网友的建议：https://github.com/VictorZhang2014/free-google-translate/issues/6
# 

import subprocess
import sys
import os
from gtts import gTTS

def sayIt(text):
    f = open("say.log", "w")
    f.write("sayIt: " + text + "\n")
    cwd = os.getcwd()
    f.write("dir: " + cwd + "\n")
    f.close()

    tts = gTTS(text, lang='en')
    tts.save('../temp/temp.mp3')
    subprocess.call(['../tools/cmdmp3.exe', '../temp/temp.mp3'])

if __name__ == '__main__':
    text = sys.argv[1]
    sayIt(text)
