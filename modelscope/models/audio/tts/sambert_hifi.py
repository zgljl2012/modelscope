from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import io
import os
import time
import zipfile
from typing import Any, Dict, Optional, Union

import json
import numpy as np
import torch

from modelscope.metainfo import Models
from modelscope.models.base import Model
from modelscope.models.builder import MODELS
from modelscope.utils.audio.tts_exceptions import (
    TtsFrontendInitializeFailedException,
    TtsFrontendLanguageTypeInvalidException, TtsModelConfigurationExcetion,
    TtsVocoderMelspecShapeMismatchException, TtsVoiceNotExistsException)
from modelscope.utils.constant import ModelFile, Tasks
from .voice import Voice

import tensorflow as tf  # isort:skip

__all__ = ['SambertHifigan']


@MODELS.register_module(
    Tasks.text_to_speech, module_name=Models.sambert_hifigan)
class SambertHifigan(Model):

    def __init__(self, model_dir, *args, **kwargs):
        super().__init__(model_dir, *args, **kwargs)
        if 'am' not in kwargs:
            raise TtsModelConfigurationExcetion(
                'configuration model field missing am!')
        if 'vocoder' not in kwargs:
            raise TtsModelConfigurationExcetion(
                'configuration model field missing vocoder!')
        if 'lang_type' not in kwargs:
            raise TtsModelConfigurationExcetion(
                'configuration model field missing lang_type!')
        am_cfg = kwargs['am']
        voc_cfg = kwargs['vocoder']
        # initialize frontend
        import ttsfrd
        frontend = ttsfrd.TtsFrontendEngine()
        zip_file = os.path.join(model_dir, 'resource.zip')
        self.__res_path = os.path.join(model_dir, 'resource')
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(model_dir)
        if not frontend.initialize(self.__res_path):
            raise TtsFrontendInitializeFailedException(
                'resource invalid: {}'.format(self.__res_path))
        if not frontend.set_lang_type(kwargs['lang_type']):
            raise TtsFrontendLanguageTypeInvalidException(
                'language type invalid: {}'.format(kwargs['lang_type']))
        self.__frontend = frontend
        zip_file = os.path.join(model_dir, 'voices.zip')
        self.__voice_path = os.path.join(model_dir, 'voices')
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(model_dir)
        voice_cfg_path = os.path.join(self.__voice_path, 'voices.json')
        with open(voice_cfg_path, 'r') as f:
            voice_cfg = json.load(f)
        if 'voices' not in voice_cfg:
            raise TtsModelConfigurationExcetion('voices invalid')
        self.__voice = {}
        for name in voice_cfg['voices']:
            voice_path = os.path.join(self.__voice_path, name)
            if not os.path.exists(voice_path):
                continue
            self.__voice[name] = Voice(name, voice_path, am_cfg, voc_cfg)
        if voice_cfg['voices']:
            self.__default_voice_name = voice_cfg['voices'][0]
        else:
            raise TtsVoiceNotExistsException('voices is empty in voices.json')

    def __synthesis_one_sentences(self, voice_name, text):
        if voice_name not in self.__voice:
            raise TtsVoiceNotExistsException(f'Voice {voice_name} not exists')
        return self.__voice[voice_name].forward(text)

    def forward(self, text: str, voice_name: str = None):
        voice = self.__default_voice_name
        if voice_name is not None:
            voice = voice_name
        result = self.__frontend.gen_tacotron_symbols(text)
        texts = [s for s in result.splitlines() if s != '']
        audio_total = np.empty((0), dtype='int16')
        for line in texts:
            line = line.strip().split('\t')
            audio = self.__synthesis_one_sentences(voice, line[1])
            audio_total = np.append(audio_total, audio, axis=0)
        return audio_total