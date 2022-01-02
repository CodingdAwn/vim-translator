#! /usr/bin/env python
# -*- coding:utf-8 -*-
# 网友的建议：https://github.com/VictorZhang2014/free-google-translate/issues/6
# 

import subprocess
import sys
import os
import platform
from gtts import gTTS

def sayIt(working_dir, text):
    f = open(working_dir + "/temp/say.log", "w")
    f.write("dir: " + working_dir + "\n")
    f.write("sayIt: " + text + "\n")

    tts = gTTS(text, lang='en')
    tts.save(working_dir + '/temp/temp.mp3')

    f.write("call: " + working_dir + '/tools/cmdmp3.exe' + "\n")
    f.write("call: " + working_dir + '/temp/temp.mp3' + "\n")

    cwd = os.getcwd()
    os.chdir(working_dir)
    system_name = platform.system()
    f.write("system: " + system_name)
    f.close()
    if platform.system() == "Darwin":
        subprocess.call(['afplay', working_dir + '/temp/temp.mp3'])
    else:
        # 使用cmdmp3.exe的话 如果mp3文件在wsl中 而当前工作目录在mnt目录 执行会失败找不到文件
        subprocess.call([working_dir + '/tools/cmdmp3.exe', working_dir + '/temp/temp.mp3'])

    os.chdir(cwd)

if __name__ == '__main__':
    working_dir = sys.argv[1]
    text = sys.argv[2]
    sayIt(working_dir, text)
