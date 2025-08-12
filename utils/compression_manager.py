"""
压缩管理工具

提供便捷的压缩管理功能，包括：
1. 压缩状态查看
2. 手动压缩触发
3. 压缩配置管理
4. 压缩服务控制
"""

import asyncio
from typing import Dict, Any, Optional
from core.unified_context import get_context
from core.context_compressor import get_compressor, start_compression_service, stop_compression_service


class CompressionManager:
    """压缩管理器"""
    
    def __init__(self):
        """初始化压缩管理器"""
        self.context = get_context()
        self.compressor = get_compressor()
    
    async def start_service(self) -> bool:
        """启动压缩服务"""
        try:
            await start_compression_service()
            print("🗜️ 智能压缩服务已启动")
            return True
        except Exception as e:
            print(f"❌ 启动压缩服务失败: {e}")
            return False
    
    async def stop_service(self) -> bool:
        """停止压缩服务"""
        try:
            await stop_compression_service()
            print("🗜️ 智能压缩服务已停止")
            return True
        except Exception as e:
            print(f"❌ 停止压缩服务失败: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取压缩状态"""
        context_status = self.context.get_compression_status()
        compressor_stats = self.compressor.get_compression_stats()
        
        return {
            "context": context_status,
            "compressor": compressor_stats,
            "service_running": compressor_stats["is_running"],
            "queue_size": compressor_stats["queue_size"]
        }
    
    def print_status(self) -> None:
        """打印压缩状态"""
        status = self.get_status()
        
        print("\n🗜️ 智能压缩状态报告")
        print("=" * 50)
        
        # 上下文状态
        ctx = status["context"]
        print(f"📊 上下文状态:")
        print(f"  - 压缩功能: {'✅ 启用' if ctx['enabled'] else '❌ 禁用'}")
        print(f"  - 消息数量: {ctx['message_count']}")
        print(f"  - 估算tokens: {ctx.get('estimated_tokens', 'N/A')}")
        print(f"  - 消息阈值: {ctx['config']['compression_threshold']}")
        print(f"  - Token阈值: {ctx['config'].get('token_threshold', 'N/A')}")
        print(f"  - 保留最近: {ctx['config']['preserve_recent']} 条")
        print(f"  - 需要压缩: {'是' if ctx['compression_needed'] else '否'}")
        print(f"  - 紧急程度: {ctx.get('compression_urgency', 'N/A')}")
        
        # 压缩器状态
        comp = status["compressor"]
        print(f"\n🔧 压缩器状态:")
        print(f"  - 服务状态: {'🟢 运行中' if comp['is_running'] else '🔴 已停止'}")
        print(f"  - 队列大小: {comp['queue_size']}")
        print(f"  - 最大上下文: {comp['config']['max_context_length']} tokens")
        print(f"  - 压缩阈值: {comp['config']['compression_threshold']} tokens")
        
        print("=" * 50)
    
    async def manual_compress(self, level: str = "medium") -> bool:
        """手动触发压缩"""
        print(f"🗜️ 开始手动压缩，级别: {level}")
        
        # 确保服务运行
        if not self.compressor.is_running:
            await self.start_service()
        
        # 执行压缩
        success = await self.context.manual_compress(level)
        
        if success:
            print("✅ 手动压缩任务已提交")
        else:
            print("❌ 手动压缩失败")
        
        return success
    
    def configure(self, **kwargs) -> None:
        """配置压缩参数"""
        print("🔧 更新压缩配置:")
        
        # 更新上下文配置
        context_keys = ["auto_compress", "compression_threshold", "preserve_recent", "token_threshold", "compression_ratio_target"]
        context_updates = {k: v for k, v in kwargs.items() if k in context_keys}
        
        if context_updates:
            self.context.configure_compression(**context_updates)
        
        # 更新压缩器配置
        compressor_keys = ["max_context_length", "compression_threshold", "min_messages_to_compress"]
        compressor_updates = {k: v for k, v in kwargs.items() if k in compressor_keys}
        
        if compressor_updates:
            for key, value in compressor_updates.items():
                if key in self.compressor.config:
                    self.compressor.config[key] = value
                    print(f"  - {key} = {value}")
    
    def enable(self, enabled: bool = True) -> None:
        """启用/禁用压缩"""
        self.context.enable_compression(enabled)
    

    
    async def force_compress_now(self, level: str = "medium") -> bool:
        """立即强制压缩（忽略数量限制）"""
        print(f"⚡ 强制立即压缩，级别: {level}")

        # 临时修改配置以强制压缩
        original_msg_threshold = self.context.compression_config["compression_threshold"]
        original_token_threshold = self.context.compression_config["token_threshold"]

        try:
            # 设置极低阈值强制触发压缩
            self.context.compression_config["compression_threshold"] = 1
            self.context.compression_config["token_threshold"] = 1

            # 执行压缩
            success = await self.manual_compress(level)

            return success

        finally:
            # 恢复原始配置
            self.context.compression_config["compression_threshold"] = original_msg_threshold
            self.context.compression_config["token_threshold"] = original_token_threshold
    
    def get_compression_suggestions(self) -> Dict[str, Any]:
        """获取压缩建议"""
        status = self.get_status()
        ctx = status["context"]

        suggestions = {
            "should_compress": False,
            "recommended_level": "medium",
            "reasons": [],
            "benefits": []
        }

        message_count = ctx["message_count"]
        estimated_tokens = ctx.get("estimated_tokens", 0)
        msg_threshold = ctx["config"]["compression_threshold"]
        token_threshold = ctx["config"].get("token_threshold", 6000)
        urgency = ctx.get("compression_urgency", "low")

        # 基于消息数量和token数量判断
        msg_over_threshold = message_count >= msg_threshold
        token_over_threshold = estimated_tokens >= token_threshold

        if msg_over_threshold or token_over_threshold:
            suggestions["should_compress"] = True

            # 添加原因
            if msg_over_threshold:
                suggestions["reasons"].append(f"消息数量 ({message_count}) 超过阈值 ({msg_threshold})")
            if token_over_threshold:
                suggestions["reasons"].append(f"Token数量 ({estimated_tokens}) 超过阈值 ({token_threshold})")

            # 根据紧急程度推荐压缩级别
            if urgency == "critical":
                suggestions["recommended_level"] = "heavy"
                suggestions["reasons"].append("上下文严重超标，建议重度压缩")
            elif urgency == "high":
                suggestions["recommended_level"] = "medium"
                suggestions["reasons"].append("上下文明显超标，建议中度压缩")
            elif urgency == "medium":
                suggestions["recommended_level"] = "light"
                suggestions["reasons"].append("上下文轻度超标，建议轻度压缩")
            else:
                suggestions["recommended_level"] = "light"
                suggestions["reasons"].append("预防性压缩，建议轻度压缩")

            # 计算预期收益
            level_reductions = {
                "light": 0.1,
                "medium": 0.3,
                "heavy": 0.5,
                "summary": 0.7
            }

            expected_reduction = level_reductions.get(suggestions["recommended_level"], 0.3)
            expected_new_count = int(message_count * (1 - expected_reduction))
            expected_token_reduction = int(estimated_tokens * expected_reduction)

            suggestions["benefits"].append(f"预期减少 {int(message_count * expected_reduction)} 条消息")
            suggestions["benefits"].append(f"预期减少 {expected_token_reduction} tokens")
            suggestions["benefits"].append(f"压缩后约 {expected_new_count} 条消息")
            suggestions["benefits"].append("提高响应速度，降低API成本")

            # 根据内容特征添加额外建议
            if message_count > 100:
                suggestions["benefits"].append("大幅提升上下文处理效率")
            if estimated_tokens > 10000:
                suggestions["benefits"].append("显著降低token消耗成本")

        return suggestions
    
    def print_suggestions(self) -> None:
        """打印压缩建议"""
        suggestions = self.get_compression_suggestions()
        
        print("\n💡 压缩建议")
        print("=" * 30)
        
        if suggestions["should_compress"]:
            print("🎯 建议执行压缩")
            print(f"📊 推荐级别: {suggestions['recommended_level']}")
            
            print("\n📋 原因:")
            for reason in suggestions["reasons"]:
                print(f"  • {reason}")
            
            print("\n✨ 预期收益:")
            for benefit in suggestions["benefits"]:
                print(f"  • {benefit}")
            
            print(f"\n🚀 执行命令: await compression_manager.manual_compress('{suggestions['recommended_level']}')")
        else:
            print("✅ 当前无需压缩")
        
        print("=" * 30)


# 全局实例
compression_manager = CompressionManager()


# 便捷函数
async def start_compression() -> bool:
    """启动压缩服务"""
    return await compression_manager.start_service()


async def stop_compression() -> bool:
    """停止压缩服务"""
    return await compression_manager.stop_service()


def show_compression_status() -> None:
    """显示压缩状态"""
    compression_manager.print_status()


def show_compression_suggestions() -> None:
    """显示压缩建议"""
    compression_manager.print_suggestions()


async def compress_now(level: str = "medium") -> bool:
    """立即压缩"""
    return await compression_manager.manual_compress(level)


def configure_compression(**kwargs) -> None:
    """配置压缩参数"""
    compression_manager.configure(**kwargs)


def enable_compression(enabled: bool = True) -> None:
    """启用/禁用压缩"""
    compression_manager.enable(enabled)
