#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SenseVoice ASR 服务客户端示例

这个示例展示了如何使用 SenseVoice ASR 服务进行语音识别。
支持多种音频格式和语言，包括中文、英文、粤语、日语、韩语等。

使用方法：
    python asr_client_example.py --audio_file test.wav --lang auto
"""

import requests
import argparse
import json
import os
from pathlib import Path


class SenseVoiceASRClient:
    """SenseVoice ASR 服务客户端"""
    
    def __init__(self, base_url="http://192.168.1.218:50000"):
        """
        初始化ASR客户端
        
        Args:
            base_url (str): ASR服务的基础URL
        """
        self.base_url = base_url
        self.asr_endpoint = f"{base_url}/api/v1/asr"
    
    def recognize_audio(self, audio_file_path, lang="auto", key=None, hotwords=None, use_itn=True):
        """
        识别音频文件中的语音
        
        Args:
            audio_file_path (str): 音频文件路径
            lang (str): 语言代码 (zh/en/yue/ja/ko/auto)
            key (str): 音频文件标识键，默认使用文件名
            hotwords (str): 热词列表，用空格分隔
            use_itn (bool): 是否使用逆文本标准化
            
        Returns:
            dict: 识别结果
        """
        # 检查文件是否存在
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")
        
        # 设置默认key
        if key is None:
            key = Path(audio_file_path).stem
        
        # 准备请求数据
        files = {'files': open(audio_file_path, 'rb')}
        data = {
            'keys': key,
            'lang': lang,
            'use_itn': use_itn
        }
        
        # 添加热词（如果提供）
        if hotwords:
            data['hotwords'] = hotwords
        
        try:
            # 发送请求
            response = requests.post(
                self.asr_endpoint,
                files=files,
                data=data,
                timeout=30  # 30秒超时
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析JSON响应
            result = response.json()
            return result
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"请求失败: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"响应解析失败: {e}")
        finally:
            # 关闭文件
            files['files'].close()
    
    def batch_recognize(self, audio_files, lang="auto", hotwords=None):
        """
        批量识别多个音频文件
        
        Args:
            audio_files (list): 音频文件路径列表
            lang (str): 语言代码
            hotwords (str): 热词列表
            
        Returns:
            list: 识别结果列表
        """
        results = []
        for audio_file in audio_files:
            try:
                result = self.recognize_audio(audio_file, lang=lang, hotwords=hotwords)
                results.append({
                    'file': audio_file,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'file': audio_file,
                    'success': False,
                    'error': str(e)
                })
        return results


def print_result(result, audio_file):
    """格式化打印识别结果"""
    print(f"\n{'='*50}")
    print(f"音频文件: {audio_file}")
    print(f"{'='*50}")
    
    if result.get('code') == 0:
        # 成功响应
        results = result.get('result', [])
        for item in results:
            print(f"标识键: {item.get('key', 'N/A')}")
            print(f"识别文本: {item.get('text', 'N/A')}")
            print(f"检测语言: {item.get('language', 'N/A')}")
            print(f"情感分析: {item.get('emotion', 'N/A')}")
            print(f"声学事件: {item.get('event', [])}")
            print(f"置信度: {item.get('confidence', 'N/A')}")
            print(f"音频时长: {item.get('duration', 'N/A')}秒")
    else:
        # 错误响应
        print(f"错误代码: {result.get('code', 'N/A')}")
        print(f"错误信息: {result.get('message', 'N/A')}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SenseVoice ASR 服务客户端示例')
    parser.add_argument('--audio_file', '-f', required=True, help='音频文件路径')
    parser.add_argument('--lang', '-l', default='auto', 
                       choices=['zh', 'en', 'yue', 'ja', 'ko', 'auto'],
                       help='语言代码 (默认: auto)')
    parser.add_argument('--hotwords', '-w', help='热词列表，用空格分隔')
    parser.add_argument('--base_url', '-u', default='http://192.168.1.218:50000',
                       help='ASR服务基础URL (默认: http://192.168.1.218:50000)')
    parser.add_argument('--key', '-k', help='音频文件标识键')
    parser.add_argument('--no_itn', action='store_true', help='禁用逆文本标准化')
    
    args = parser.parse_args()
    
    # 创建ASR客户端
    client = SenseVoiceASRClient(base_url=args.base_url)
    
    try:
        # 执行语音识别
        print(f"正在识别音频文件: {args.audio_file}")
        print(f"语言设置: {args.lang}")
        if args.hotwords:
            print(f"热词: {args.hotwords}")
        
        result = client.recognize_audio(
            audio_file_path=args.audio_file,
            lang=args.lang,
            key=args.key,
            hotwords=args.hotwords,
            use_itn=not args.no_itn
        )
        
        # 打印结果
        print_result(result, args.audio_file)
        
    except Exception as e:
        print(f"识别失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
