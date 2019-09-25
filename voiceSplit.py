# -*- coding: utf-8 -*-
# @Time    : 2019年09月25日 09:51
# @Author  : 李思原
# @Email   : shulisiyuan@163.com
# @File    : voiceSplit.py
# @Software: PyCharm
# @Describe: 将声音进行切片.


import wave
import soundfile as sf
import struct
import os
from tqdm import tqdm
from retry import retry




class Voicesplit(object):
    def __init__(self, musicFileName, outFilePath):
        # 音频文件名称
        self.musicFileName = musicFileName
        # 文件输出路径
        self.outFilePath = outFilePath
        # 最小音量
        self.voiceMinValue = 0.01
        # 两句话之间最大时间间隔（秒）
        self.voiceMaxDistanceSecond = 0.1
        # 单个音频最小时间长度（秒）
        self.voiceMinSecond = 0.1



    # wav文件写入,分时间间隔
    def wavWriteByTime(self, musicFileName, outData, voiceTime1, voiceTime2):
        outData = outData[voiceTime1:voiceTime2]
        fileAbsoluteName = os.path.splitext(os.path.split(musicFileName)[-1])[0]
        fileSavePath = os.path.join(self.outFilePath, fileAbsoluteName)

        if not os.path.exists(fileSavePath):
            os.makedirs(fileSavePath)

        outfile = os.path.join(fileSavePath,os.path.splitext(os.path.split(musicFileName)[-1])[0] + '_%d_%d_%s_split.wav' % (voiceTime1, voiceTime2, self.sample_rate))


        # 判断文件是否存在
        if not os.path.exists(outfile):
            print('正在生成文件：', outfile)
            with wave.open(outfile, 'wb') as outwave:  # 定义存储路径以及文件名
                nchannels = 1
                sampwidth = 2
                fs = 8000
                data_size = len(outData)
                framerate = int(fs)
                nframes = data_size
                comptype = "NONE"
                compname = "not compressed"
                outwave.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
                for v in outData:
                    outwave.writeframes(struct.pack('h', int(v * 64000 / 2)))


    # 分割声音，分段保存
    @retry(tries=5, delay=2)
    def splitVoiceAndSave(self):
        sig, self.sample_rate = sf.read(self.musicFileName)
        print('正在读取文件:%s' % musicFileName)
        print("采样率：%d" % self.sample_rate)
        print("时长：%s" % (sig.shape[0] / self.sample_rate), '秒')

        # 我的音频文件有两个通道，这里读取第一个通道，你需要根据你的音频文件是否是双通道，进行修改
        inputData = sig.T[0]

        dd = {}
        for k, v in tqdm(enumerate(inputData)):
            if abs(v) < self.voiceMinValue:
                dd[k] = 0
            else:
                dd[k] = v

        x = [i / self.sample_rate for i in range(len(inputData))]
        y = list(dd.values())

        # 删除空白部分
        for key in list(dd):
            if dd[key] == 0:
                dd.pop(key)

        # 判断声音间隔
        voiceSignalTime = list(dd.keys())
        list1 = []
        list2 = []
        for k, v in enumerate(voiceSignalTime[:-2]):
            list2.append(v)
            if voiceSignalTime[k + 1] - v > self.voiceMaxDistanceSecond * self.sample_rate:
                list1.append(list2)
                list2 = []

        if len(list1) == 0:
            list1.append(list2)

        if len(list1) > 0 and (
                voiceSignalTime[-1] - voiceSignalTime[-2]) < self.voiceMaxDistanceSecond * self.sample_rate:
            list1[-1].append(voiceSignalTime[-2])

        voiceTimeList = [x for x in list1 if len(x) > self.voiceMinSecond * self.sample_rate]
        print('分解出声音片段：', len(voiceTimeList))

        for voiceTime in voiceTimeList:
            voiceTime1 = int(max(0, voiceTime[0] - 0.8 * self.sample_rate))
            voiceTime2 = int(min(sig.shape[0], voiceTime[-1] + 0.8 * self.sample_rate))
            self.wavWriteByTime(musicFileName=self.musicFileName, outData=inputData, voiceTime1=voiceTime1, voiceTime2=voiceTime2)


if __name__ == '__main__':
    # 在此输入你的音频文件
    musicFileName = '***'
    voice = Voicesplit(musicFileName=musicFileName, outFilePath='outFile')
    voice.splitVoiceAndSave()
