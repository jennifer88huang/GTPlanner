#!/bin/bash

# GTPlanner Langfuse 配置脚本

echo "🔧 GTPlanner Langfuse 配置向导"
echo "=================================="

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "📋 创建 .env 文件..."
    cp .env.example .env
fi

echo ""
echo "请选择配置方式："
echo "1. 配置 Langfuse Cloud（推荐）"
echo "2. 临时禁用 Tracing"
echo "3. 手动配置"

read -p "请输入选项 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "📝 Langfuse Cloud 配置"
        echo "----------------------"
        echo "1. 访问：https://cloud.langfuse.com"
        echo "2. 注册账号并创建项目"
        echo "3. 在 Settings → API Keys 中创建密钥"
        echo ""
        
        read -p "请输入 Secret Key: " secret_key
        read -p "请输入 Public Key: " public_key
        
        # 更新 .env 文件
        sed -i.bak "s|LANGFUSE_SECRET_KEY=.*|LANGFUSE_SECRET_KEY=$secret_key|" .env
        sed -i.bak "s|LANGFUSE_PUBLIC_KEY=.*|LANGFUSE_PUBLIC_KEY=$public_key|" .env
        sed -i.bak "s|LANGFUSE_HOST=.*|LANGFUSE_HOST=https://cloud.langfuse.com|" .env
        sed -i.bak "s|POCKETFLOW_TRACING_DEBUG=.*|POCKETFLOW_TRACING_DEBUG=true|" .env
        
        echo "✅ Langfuse 配置完成！"
        ;;
        
    2)
        echo ""
        echo "🚫 禁用 Tracing 配置"
        echo "-------------------"
        
        # 注释掉 Langfuse 配置
        sed -i.bak "s|LANGFUSE_SECRET_KEY=|# LANGFUSE_SECRET_KEY=|" .env
        sed -i.bak "s|LANGFUSE_PUBLIC_KEY=|# LANGFUSE_PUBLIC_KEY=|" .env
        sed -i.bak "s|LANGFUSE_HOST=|# LANGFUSE_HOST=|" .env
        
        echo "✅ Tracing 已禁用！"
        echo "⚠️  注意：这样可以避免错误，但不会记录执行轨迹"
        ;;
        
    3)
        echo ""
        echo "📝 手动配置说明"
        echo "---------------"
        echo "请手动编辑 .env 文件，配置以下变量："
        echo ""
        echo "LANGFUSE_SECRET_KEY=你的-secret-key"
        echo "LANGFUSE_PUBLIC_KEY=你的-public-key"
        echo "LANGFUSE_HOST=https://cloud.langfuse.com"
        echo ""
        echo "或者访问 https://langfuse.com 了解更多信息"
        ;;
        
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "🎉 配置完成！"
echo ""
echo "📋 下一步："
echo "1. 重启应用程序"
echo "2. 测试功能是否正常"
echo "3. 如果配置了 Langfuse，可以在 Langfuse 仪表板中查看执行轨迹"

# 清理备份文件
rm -f .env.bak
