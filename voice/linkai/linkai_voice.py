"""
google voice service
"""
import json
import os
import random

import openai
import requests

from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from voice.voice import Voice
from common import const
import datetime

class LinkAIVoice(Voice):
    def __init__(self):
        pass

    def voiceToText(self, voice_file):
        logger.debug("[LinkVoice] voice file name={}".format(voice_file))
        try:
            url = conf().get("linkai_api_base", "https://api.link-ai.chat") + "/v1/audio/transcriptions"
            headers = {"Authorization": "Bearer " + conf().get("linkai_api_key")}
            model = None
            if not conf().get("text_to_voice") or conf().get("voice_to_text") == "openai":
                model = const.WHISPER_1
            file = open(voice_file, "rb")
            file_body = {
                "file": file
            }
            data = {
                "model": model
            }
            res = requests.post(url, files=file_body, headers=headers, data=data, timeout=(5, 60))
            if res.status_code == 200:
                text = res.json().get("text")
            else:
                res_json = res.json()
                logger.error(f"[LinkVoice] voiceToText error, status_code={res.status_code}, msg={res_json.get('message')}")
                return None
            reply = Reply(ReplyType.TEXT, text)
            logger.info(f"[LinkVoice] voiceToText success, text={text}, file name={voice_file}")
        except Exception as e:
            logger.error(e)
            reply = Reply(ReplyType.ERROR, "我暂时还无法听清您的语音，请稍后再试吧~")
        return reply

    def textToVoice(self, text):
        try:
            url = conf().get("linkai_api_base", "https://api.link-ai.chat") + "/v1/audio/speech"
            headers = {"Authorization": "Bearer " + conf().get("linkai_api_key")}
            model = const.TTS_1
            if not conf().get("text_to_voice") or conf().get("text_to_voice") in ["openai", const.TTS_1, const.TTS_1_HD]:
                model = conf().get("text_to_voice_model") or const.TTS_1
            data = {
                "model": model,
                "input": text,
                "voice": conf().get("tts_voice_id")
            }
            res = requests.post(url, headers=headers, json=data, timeout=(5, 120))
            if res.status_code == 200:
                tmp_file_name = "tmp/" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0, 1000)) + ".mp3"
                with open(tmp_file_name, 'wb') as f:
                    f.write(res.content)
                reply = Reply(ReplyType.VOICE, tmp_file_name)
                logger.info(f"[LinkVoice] textToVoice success, input={text}, model={model}, voice_id={data.get('voice')}")
                return reply
            else:
                res_json = res.json()
                logger.error(f"[LinkVoice] textToVoice error, status_code={res.status_code}, msg={res_json.get('message')}")
                return None
        except Exception as e:
            logger.error(e)
            reply = Reply(ReplyType.ERROR, "遇到了一点小问题，请稍后再问我吧")
        return reply
