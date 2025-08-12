#!/usr/bin/env python3
"""
智能上下文压缩演示

演示如何使用智能压缩功能来管理长对话历史，
避免硬编码压缩导致的信息丢失。
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.unified_context import get_context
from utils.compression_manager import compression_manager
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown


async def demo_compression():
    """演示智能压缩功能"""
    console = Console()
    context = get_context()
    
    console.print(Panel(
        Markdown("""
# 🗜️ 智能上下文压缩演示

本演示将展示：
1. 创建长对话历史
2. 查看压缩状态和建议
3. 执行智能压缩
4. 对比压缩前后的效果
        """),
        title="智能压缩演示",
        border_style="blue"
    ))
    
    # 1. 创建演示会话
    console.print("\n📝 [bold blue]步骤1: 创建演示会话[/bold blue]")
    session_id = context.create_session("智能压缩演示")
    console.print(f"✅ 创建会话: {session_id}")
    
    # 2. 添加大量消息模拟长对话
    console.print("\n📝 [bold blue]步骤2: 模拟长对话历史[/bold blue]")
    
    # 模拟用户需求分析对话
    messages = [
        ("user", "我想开发一个电商网站，需要什么功能？"),
        ("assistant", "电商网站需要以下核心功能：\n1. 用户注册登录\n2. 商品展示和搜索\n3. 购物车管理\n4. 订单处理\n5. 支付集成\n6. 库存管理\n7. 用户评价系统"),
        ("user", "用户注册登录需要考虑哪些安全因素？"),
        ("assistant", "用户认证安全需要考虑：\n1. 密码强度要求\n2. 多因素认证(2FA)\n3. 防暴力破解\n4. 会话管理\n5. 密码加密存储\n6. OAuth第三方登录\n7. 账户锁定机制"),
        ("user", "商品搜索功能应该如何设计？"),
        ("assistant", "商品搜索功能设计要点：\n1. 全文搜索引擎(如Elasticsearch)\n2. 分类筛选\n3. 价格区间筛选\n4. 品牌筛选\n5. 智能推荐\n6. 搜索历史\n7. 热门搜索\n8. 搜索结果排序算法"),
        ("user", "支付系统需要集成哪些支付方式？"),
        ("assistant", "支付系统集成建议：\n1. 支付宝\n2. 微信支付\n3. 银联支付\n4. 信用卡支付\n5. 数字钱包\n6. 分期付款\n7. 货到付款\n8. 企业转账"),
        ("user", "订单管理系统需要什么功能？"),
        ("assistant", "订单管理系统功能：\n1. 订单创建和确认\n2. 订单状态跟踪\n3. 发货管理\n4. 退换货处理\n5. 订单搜索和筛选\n6. 批量操作\n7. 订单统计分析\n8. 自动化流程"),
        ("user", "库存管理有什么最佳实践？"),
        ("assistant", "库存管理最佳实践：\n1. 实时库存同步\n2. 安全库存设置\n3. 自动补货提醒\n4. 库存预警机制\n5. 多仓库管理\n6. 库存盘点\n7. 库存报表\n8. 供应商管理"),
        ("user", "用户评价系统如何防止刷评？"),
        ("assistant", "防刷评机制：\n1. 实名认证\n2. 购买验证\n3. 评价时间限制\n4. IP地址检测\n5. 行为模式分析\n6. 机器学习检测\n7. 人工审核\n8. 举报机制"),
        ("user", "网站性能优化有什么建议？"),
        ("assistant", "性能优化建议：\n1. CDN加速\n2. 图片压缩和懒加载\n3. 数据库优化\n4. 缓存策略\n5. 代码分割\n6. 服务器负载均衡\n7. 监控和分析\n8. 移动端优化"),
    ]
    
    for role, content in messages:
        if role == "user":
            context.add_user_message(content)
        else:
            context.add_assistant_message(content)
        console.print(f"  ➕ 添加{role}消息: {content[:30]}...")
    
    console.print(f"✅ 已添加 {len(messages)} 条消息")
    
    # 3. 显示压缩前状态
    console.print("\n📊 [bold blue]步骤3: 查看压缩前状态[/bold blue]")
    compression_manager.print_status()
    
    # 4. 显示压缩建议
    console.print("\n💡 [bold blue]步骤4: 获取压缩建议[/bold blue]")
    compression_manager.print_suggestions()
    
    # 5. 启动压缩服务
    console.print("\n🚀 [bold blue]步骤5: 启动压缩服务[/bold blue]")
    await compression_manager.start_service()
    
    # 6. 执行不同级别的压缩演示
    compression_levels = ["light", "medium", "heavy"]
    
    for level in compression_levels:
        console.print(f"\n🗜️ [bold blue]步骤6.{compression_levels.index(level)+1}: 执行{level}级别压缩[/bold blue]")
        
        # 记录压缩前的消息数量
        before_count = len(context.messages)
        
        # 执行压缩
        success = await compression_manager.manual_compress(level)
        
        if success:
            # 等待压缩完成（简单等待）
            await asyncio.sleep(3)
            
            # 显示压缩后状态
            after_count = len(context.messages)
            console.print(f"  📊 压缩前: {before_count} 条消息")
            console.print(f"  📊 压缩后: {after_count} 条消息")
            console.print(f"  📊 压缩比: {(before_count - after_count) / before_count * 100:.1f}%")
        else:
            console.print(f"  ❌ {level}级别压缩失败")
        
        # 为下一次压缩添加更多消息
        if level != compression_levels[-1]:
            console.print(f"  ➕ 为下一次压缩添加更多消息...")
            for i in range(5):
                context.add_user_message(f"这是第{i+1}个额外的用户问题，用于测试{level}压缩后的效果")
                context.add_assistant_message(f"这是对第{i+1}个问题的详细回答，包含了丰富的技术细节和实施建议")
    
    # 7. 显示最终状态
    console.print("\n📊 [bold blue]步骤7: 最终状态[/bold blue]")
    compression_manager.print_status()
    
    # 8. 演示配置管理
    console.print("\n⚙️ [bold blue]步骤8: 配置管理演示[/bold blue]")
    
    console.print("  🔧 调整压缩配置...")
    compression_manager.configure(
        compression_threshold=20,  # 降低阈值
        preserve_recent=8,         # 保留更多最近消息
        auto_compress=True         # 启用自动压缩
    )
    
    console.print("  📊 配置调整后的状态:")
    compression_manager.print_status()
    
    # 9. 停止压缩服务
    console.print("\n🛑 [bold blue]步骤9: 停止压缩服务[/bold blue]")
    await compression_manager.stop_service()
    
    # 10. 总结
    console.print(Panel(
        Markdown("""
# 🎉 演示完成

## 主要特性展示：

1. **智能压缩**: 基于LLM的智能压缩，保留关键信息
2. **多级压缩**: 支持light/medium/heavy/summary四个级别
3. **异步处理**: 不阻塞主流程的后台压缩
4. **配置灵活**: 可调整压缩阈值、保留消息数等参数
5. **状态监控**: 实时查看压缩状态和建议

## 使用建议：

- 在CLI中使用 `/compress` 命令查看状态
- 使用 `/compress now medium` 手动触发压缩
- 通过 `/compress config` 查看详细配置
- 启用自动压缩让系统智能管理上下文长度

智能压缩有效解决了硬编码压缩导致的信息丢失问题！
        """),
        title="演示总结",
        border_style="green"
    ))


async def main():
    """主函数"""
    try:
        await demo_compression()
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
