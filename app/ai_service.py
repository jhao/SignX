from __future__ import annotations

import json
from typing import Any
from urllib import request as urlrequest

from .models import SystemSetting

AI_MODEL_SETTING_KEY = 'ai_model'


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

    req = urlrequest.Request(
        f'{base_url.rstrip("/")}/chat/completions',
        data=payload,
        method='POST',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
    )
    with urlrequest.urlopen(req, timeout=20) as response:
        body = response.read().decode('utf-8')
    data = json.loads(body)
    return data['choices'][0]['message']['content'].strip()
