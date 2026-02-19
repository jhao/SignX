from __future__ import annotations

import json
from typing import Any
from urllib import request as urlrequest

from .models import SystemSetting

AI_MODEL_SETTING_KEY = 'ai_model'

MODEL_PRESETS: list[dict[str, str]] = [
    {
        'id': 'openai-gpt-4o-mini',
        'label': 'OpenAI GPT-4o mini',
        'provider': 'openai',
        'model_type': 'chat',
        'base_url': 'https://api.openai.com/v1',
        'model': 'gpt-4o-mini',
    },
    {
        'id': 'openai-gpt-4.1',
        'label': 'OpenAI GPT-4.1',
        'provider': 'openai',
        'model_type': 'chat',
        'base_url': 'https://api.openai.com/v1',
        'model': 'gpt-4.1',
    },
    {
        'id': 'anthropic-claude-3-5-sonnet',
        'label': 'Anthropic Claude 3.5 Sonnet (OpenAI兼容)',
        'provider': 'anthropic',
        'model_type': 'chat',
        'base_url': 'https://api.anthropic.com/v1',
        'model': 'claude-3-5-sonnet-latest',
    },
    {
        'id': 'deepseek-chat',
        'label': 'DeepSeek Chat',
        'provider': 'deepseek',
        'model_type': 'chat',
        'base_url': 'https://api.deepseek.com/v1',
        'model': 'deepseek-chat',
    },
    {
        'id': 'qwen-plus',
        'label': 'Qwen Plus (DashScope兼容)',
        'provider': 'qwen',
        'model_type': 'chat',
        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'model': 'qwen-plus',
    },
]


def get_model_presets() -> list[dict[str, str]]:
    return MODEL_PRESETS


def get_model_preset(preset_id: str | None) -> dict[str, str] | None:
    if not preset_id:
        return None
    return next((preset for preset in MODEL_PRESETS if preset['id'] == preset_id), None)


def get_ai_model_settings() -> dict[str, Any]:
    setting = SystemSetting.query.get(AI_MODEL_SETTING_KEY)
    return (setting.value or {}) if setting else {}


def save_ai_model_settings(payload: dict[str, Any]):
    setting = SystemSetting.query.get(AI_MODEL_SETTING_KEY)
    if not setting:
        setting = SystemSetting(key=AI_MODEL_SETTING_KEY, value={})
    setting.value = payload
    return setting


def generate_employee_agent_prompt(name: str, primary_tasks: str | None, company_role: str) -> str:
    settings = get_ai_model_settings()
    base_url = (settings.get('base_url') or '').strip()
    api_key = (settings.get('api_key') or '').strip()
    model = (settings.get('model') or '').strip()
    if not base_url or not api_key or not model:
        raise ValueError('ai_model_not_configured')

    prompt = (
        '请根据以下员工信息，生成一段简洁实用的智能体系统提示词，'
        '用于指导该员工的AI助手工作。输出中文，100-180字。\n'
        f'员工姓名: {name}\n'
        f'公司角色: {company_role}\n'
        f'岗位职责: {primary_tasks or "未提供"}'
    )

    payload = json.dumps(
        {
            'model': model,
            'messages': [
                {'role': 'system', 'content': '你是企业组织管理顾问，擅长编写角色智能体提示词。'},
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0.3,
        }
    ).encode('utf-8')

    return _call_chat_completion(base_url=base_url, api_key=api_key, payload=payload)


def generate_structured_chat_completion(system_prompt: str, user_prompt: str) -> str:
    settings = get_ai_model_settings()
    base_url = (settings.get('base_url') or '').strip()
    api_key = (settings.get('api_key') or '').strip()
    model = (settings.get('model') or '').strip()
    if not base_url or not api_key or not model:
        raise ValueError('ai_model_not_configured')

    payload = json.dumps(
        {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': 0.2,
        }
    ).encode('utf-8')
    return _call_chat_completion(base_url=base_url, api_key=api_key, payload=payload)


def _call_chat_completion(base_url: str, api_key: str, payload: bytes) -> str:
    req = urlrequest.Request(
        f'{base_url.rstrip("/")}/chat/completions',
        data=payload,
        method='POST',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
    )
    with urlrequest.urlopen(req, timeout=30) as response:
        body = response.read().decode('utf-8')
    data = json.loads(body)
    return data['choices'][0]['message']['content'].strip()
