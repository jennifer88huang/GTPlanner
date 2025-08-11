"""
OpenAI SDK配置管理模块

提供统一的OpenAI SDK配置管理，支持多环境配置、参数验证和默认值设置。
保持与现有Dynaconf配置系统的兼容性。
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from dynaconf import Dynaconf


@dataclass
class OpenAIConfig:
    """OpenAI SDK配置类"""
    
    # 基础配置
    api_key: str
    base_url: Optional[str] = None
    organization: Optional[str] = None
    project: Optional[str] = None
    
    # 模型配置
    model: str = "gpt-4"
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: Optional[int] = None
    
    # 超时和重试配置
    timeout: float = 120.0
    max_retries: int = 3
    retry_delay: float = 2.0
    
    # Function Calling配置
    function_calling_enabled: bool = True
    parallel_tool_calls: bool = True
    tool_choice: str = "auto"  # "auto", "none", "required", or specific tool
    
    # 流式输出配置
    stream_enabled: bool = True
    stream_chunk_size: int = 1024
    
    # 日志和调试配置
    debug_enabled: bool = False
    log_requests: bool = True
    log_responses: bool = False
    
    # 高级配置
    response_format: Optional[Dict[str, Any]] = None
    seed: Optional[int] = None
    user: Optional[str] = None
    
    def __post_init__(self):
        """配置验证和后处理"""
        self._coerce_types()
        self._validate_config()
        self._set_defaults()

    def _coerce_types(self) -> None:
        """在加载配置后进行类型纠正，防止环境变量/配置文件以字符串形式注入导致运行期类型错误"""
        def to_int(value, default=None):
            if isinstance(value, int) or value is None:
                return value if value is not None else default
            try:
                return int(value)
            except Exception:
                return default if default is not None else value

        def to_float(value, default=None):
            if isinstance(value, float) or isinstance(value, int) or value is None:
                return float(value) if value is not None else default
            try:
                return float(value)
            except Exception:
                return default if default is not None else value

        def to_bool(value, default=None):
            if isinstance(value, bool) or value is None:
                return value if value is not None else default
            if isinstance(value, str):
                v = value.strip().lower()
                if v in {"true", "1", "yes", "y", "on"}:
                    return True
                if v in {"false", "0", "no", "n", "off"}:
                    return False
            return default if default is not None else value

        # 基础数值类型
        self.temperature = to_float(self.temperature, 0.0)
        self.top_p = to_float(self.top_p, 1.0)
        self.max_tokens = to_int(self.max_tokens)
        self.timeout = to_float(self.timeout, 120.0)
        self.max_retries = to_int(self.max_retries, 3)
        self.retry_delay = to_float(self.retry_delay, 2.0)
        self.parallel_tool_calls = to_bool(self.parallel_tool_calls, True)
        self.stream_enabled = to_bool(self.stream_enabled, True)
        self.stream_chunk_size = to_int(self.stream_chunk_size, 1024)
        self.seed = to_int(self.seed)
    
    def _validate_config(self):
        """验证配置参数"""
        if not self.api_key:
            raise ValueError("API key is required")
        
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
        
        if self.top_p < 0 or self.top_p > 1:
            raise ValueError("Top_p must be between 0 and 1")
        
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
    
    def _set_defaults(self):
        """设置默认值"""
        if self.base_url is None:
            self.base_url = "https://api.openai.com/v1"
    
    def to_openai_client_kwargs(self) -> Dict[str, Any]:
        """转换为OpenAI客户端初始化参数"""
        kwargs = {
            "api_key": self.api_key,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }
        
        if self.base_url:
            kwargs["base_url"] = self.base_url
        
        if self.organization:
            kwargs["organization"] = self.organization
        
        if self.project:
            kwargs["project"] = self.project
        
        return kwargs
    
    def to_chat_completion_kwargs(self) -> Dict[str, Any]:
        """转换为chat completion调用参数"""
        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        
        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        
        if self.response_format:
            kwargs["response_format"] = self.response_format
        
        if self.seed:
            kwargs["seed"] = self.seed
        
        if self.user:
            kwargs["user"] = self.user
        
        if self.function_calling_enabled:
            kwargs["parallel_tool_calls"] = self.parallel_tool_calls
            kwargs["tool_choice"] = self.tool_choice
        
        return kwargs


class OpenAIConfigManager:
    """OpenAI配置管理器"""
    
    def __init__(self, settings: Optional[Dynaconf] = None):
        """
        初始化配置管理器
        
        Args:
            settings: Dynaconf设置对象，如果为None则创建新的
        """
        if settings is None:
            self.settings = Dynaconf(
                settings_files=["settings.toml", "settings.local.toml", ".secrets.toml"],
                environments=True,
                env_switcher="ENV_FOR_DYNACONF",
                load_dotenv=True,
            )
        else:
            self.settings = settings
        
        self._config_cache: Optional[OpenAIConfig] = None
    
    def get_config(self, force_reload: bool = False) -> OpenAIConfig:
        """
        获取OpenAI配置
        
        Args:
            force_reload: 是否强制重新加载配置
            
        Returns:
            OpenAI配置对象
        """
        if self._config_cache is None or force_reload:
            self._config_cache = self._load_config()
        
        return self._config_cache
    
    def _load_config(self) -> OpenAIConfig:
        """从设置中加载配置"""
        # 优先使用新的openai配置，如果不存在则使用旧的llm配置
        config_data = {}
        
        # 基础配置
        config_data["api_key"] = self._get_setting(
            ["openai.api_key", "llm.api_key"], 
            os.getenv("OPENAI_API_KEY")
        )
        
        config_data["base_url"] = self._get_setting(
            ["openai.base_url", "llm.base_url"],
            None
        )
        
        config_data["organization"] = self._get_setting(
            ["openai.organization"],
            os.getenv("OPENAI_ORG_ID")
        )
        
        config_data["project"] = self._get_setting(
            ["openai.project"],
            os.getenv("OPENAI_PROJECT_ID")
        )
        
        # 模型配置
        config_data["model"] = self._get_setting(
            ["openai.model", "llm.model"],
            "gpt-4"
        )
        
        config_data["temperature"] = self._get_setting(
            ["openai.temperature", "llm.temperature"],
            0.0
        )
        
        config_data["top_p"] = self._get_setting(
            ["openai.top_p", "llm.top_p"],
            1.0
        )
        
        config_data["max_tokens"] = self._get_setting(
            ["openai.max_tokens", "llm.max_tokens"],
            None
        )
        
        # 超时和重试配置
        config_data["timeout"] = self._get_setting(
            ["openai.timeout", "llm.timeout"],
            120.0
        )
        
        config_data["max_retries"] = self._get_setting(
            ["openai.max_retries", "llm.max_retries"],
            3
        )
        
        config_data["retry_delay"] = self._get_setting(
            ["openai.retry_delay", "llm.retry_delay"],
            2.0
        )
        
        # Function Calling配置
        config_data["function_calling_enabled"] = self._get_setting(
            ["openai.function_calling_enabled"],
            True
        )
        
        config_data["parallel_tool_calls"] = self._get_setting(
            ["openai.parallel_tool_calls"],
            True
        )
        
        config_data["tool_choice"] = self._get_setting(
            ["openai.tool_choice"],
            "auto"
        )
        
        # 流式输出配置
        config_data["stream_enabled"] = self._get_setting(
            ["openai.stream_enabled", "llm.stream_enabled"],
            True
        )
        
        config_data["stream_chunk_size"] = self._get_setting(
            ["openai.stream_chunk_size"],
            1024
        )
        
        # 日志和调试配置
        config_data["debug_enabled"] = self._get_setting(
            ["openai.debug_enabled", "debug"],
            False
        )
        
        config_data["log_requests"] = self._get_setting(
            ["openai.log_requests"],
            True
        )
        
        config_data["log_responses"] = self._get_setting(
            ["openai.log_responses"],
            False
        )
        
        # 高级配置
        response_format = self._get_setting(["openai.response_format"], None)
        if response_format:
            config_data["response_format"] = response_format
        
        config_data["seed"] = self._get_setting(["openai.seed"], None)
        config_data["user"] = self._get_setting(["openai.user"], None)
        
        return OpenAIConfig(**config_data)
    
    def _get_setting(self, paths: List[str], default: Any = None) -> Any:
        """
        从多个路径中获取设置值
        
        Args:
            paths: 配置路径列表，按优先级排序
            default: 默认值
            
        Returns:
            配置值
        """
        for path in paths:
            try:
                value = self.settings.get(path)
                if value is not None:
                    return value
            except Exception:
                continue
        
        return default
    
    def update_config(self, **kwargs) -> None:
        """
        更新配置（运行时）
        
        Args:
            **kwargs: 要更新的配置项
        """
        if self._config_cache is None:
            self._config_cache = self._load_config()
        
        # 创建新的配置对象
        current_data = {
            "api_key": self._config_cache.api_key,
            "base_url": self._config_cache.base_url,
            "organization": self._config_cache.organization,
            "project": self._config_cache.project,
            "model": self._config_cache.model,
            "temperature": self._config_cache.temperature,
            "top_p": self._config_cache.top_p,
            "max_tokens": self._config_cache.max_tokens,
            "timeout": self._config_cache.timeout,
            "max_retries": self._config_cache.max_retries,
            "retry_delay": self._config_cache.retry_delay,
            "function_calling_enabled": self._config_cache.function_calling_enabled,
            "parallel_tool_calls": self._config_cache.parallel_tool_calls,
            "tool_choice": self._config_cache.tool_choice,
            "stream_enabled": self._config_cache.stream_enabled,
            "stream_chunk_size": self._config_cache.stream_chunk_size,
            "debug_enabled": self._config_cache.debug_enabled,
            "log_requests": self._config_cache.log_requests,
            "log_responses": self._config_cache.log_responses,
            "response_format": self._config_cache.response_format,
            "seed": self._config_cache.seed,
            "user": self._config_cache.user,
        }
        
        current_data.update(kwargs)
        self._config_cache = OpenAIConfig(**current_data)


# 全局配置管理器实例
_config_manager: Optional[OpenAIConfigManager] = None


def get_config_manager(settings: Optional[Dynaconf] = None) -> OpenAIConfigManager:
    """
    获取全局配置管理器实例
    
    Args:
        settings: Dynaconf设置对象
        
    Returns:
        配置管理器实例
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = OpenAIConfigManager(settings)
    
    return _config_manager


def get_openai_config(force_reload: bool = False) -> OpenAIConfig:
    """
    获取OpenAI配置的便捷函数
    
    Args:
        force_reload: 是否强制重新加载配置
        
    Returns:
        OpenAI配置对象
    """
    return get_config_manager().get_config(force_reload)
