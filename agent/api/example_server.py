"""
GTPlanner SSE API 示例服务器

展示如何在实际的Web应用中使用SSE API，提供HTTP接口和SSE流式响应。
"""

import asyncio
import json
import sys
import os
from typing import Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from aiohttp import web, web_request, web_response
    from aiohttp.web_ws import WSMsgType
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("⚠️ aiohttp 未安装，将使用模拟服务器")

from agent.api.agent_api import SSEGTPlannerAPI


class GTPlannerSSEServer:
    """GTPlanner SSE 服务器"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.api = SSEGTPlannerAPI(verbose=True)
        
        if AIOHTTP_AVAILABLE:
            self.app = web.Application()
            self._setup_routes()
        else:
            self.app = None
    
    def _setup_routes(self):
        """设置路由"""
        if not AIOHTTP_AVAILABLE:
            return
            
        # 静态文件和页面
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/health', self.health_handler)
        
        # API 端点
        self.app.router.add_post('/api/chat', self.chat_handler)
        self.app.router.add_get('/api/chat/stream', self.chat_stream_handler)
        
        # CORS 支持
        self.app.router.add_options('/api/chat', self.cors_handler)
        self.app.router.add_options('/api/chat/stream', self.cors_handler)
    
    async def index_handler(self, request: web_request.Request) -> web_response.Response:
        """首页处理器"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>GTPlanner SSE API Demo</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .input-area { margin: 20px 0; }
                .input-area input { width: 70%; padding: 10px; }
                .input-area button { padding: 10px 20px; margin-left: 10px; }
                .output { border: 1px solid #ccc; padding: 20px; height: 400px; overflow-y: auto; background: #f9f9f9; }
                .event { margin: 5px 0; padding: 5px; border-left: 3px solid #007cba; background: white; }
                .error { border-left-color: #d32f2f; }
                .success { border-left-color: #388e3c; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 GTPlanner SSE API Demo</h1>
                <div class="input-area">
                    <input type="text" id="userInput" placeholder="输入您的需求..." />
                    <button onclick="sendRequest()">发送</button>
                    <button onclick="clearOutput()">清空</button>
                </div>
                <div id="output" class="output"></div>
            </div>
            
            <script>
                function addEvent(content, type = 'info') {
                    const output = document.getElementById('output');
                    const div = document.createElement('div');
                    div.className = `event ${type}`;
                    div.innerHTML = `<small>${new Date().toLocaleTimeString()}</small><br>${content}`;
                    output.appendChild(div);
                    output.scrollTop = output.scrollHeight;
                }
                
                function clearOutput() {
                    document.getElementById('output').innerHTML = '';
                }
                
                async function sendRequest() {
                    const input = document.getElementById('userInput');
                    const userInput = input.value.trim();
                    
                    if (!userInput) {
                        addEvent('请输入内容', 'error');
                        return;
                    }
                    
                    addEvent(`发送请求: ${userInput}`, 'info');
                    input.value = '';
                    
                    try {
                        const response = await fetch('/api/chat/stream?' + new URLSearchParams({
                            user_input: userInput,
                            include_metadata: 'true'
                        }));
                        
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                        }
                        
                        const reader = response.body.getReader();
                        const decoder = new TextDecoder();
                        
                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;
                            
                            const chunk = decoder.decode(value);
                            const lines = chunk.split('\\n');
                            
                            for (const line of lines) {
                                if (line.startsWith('data: ')) {
                                    try {
                                        const data = JSON.parse(line.substring(6));
                                        addEvent(`事件: ${data.event_type}<br>数据: ${JSON.stringify(data.data, null, 2)}`, 'success');
                                    } catch (e) {
                                        addEvent(`原始数据: ${line}`, 'info');
                                    }
                                } else if (line.startsWith('event: ')) {
                                    addEvent(`事件类型: ${line.substring(8)}`, 'info');
                                }
                            }
                        }
                        
                        addEvent('请求完成', 'success');
                        
                    } catch (error) {
                        addEvent(`错误: ${error.message}`, 'error');
                    }
                }
                
                // 回车发送
                document.getElementById('userInput').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendRequest();
                    }
                });
            </script>
        </body>
        </html>
        """
        return web_response.Response(text=html_content, content_type='text/html')
    
    async def health_handler(self, request: web_request.Request) -> web_response.Response:
        """健康检查处理器"""
        status = self.api.get_api_status()
        return web_response.json_response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "api_status": status
        })
    
    async def cors_handler(self, request: web_request.Request) -> web_response.Response:
        """CORS 预检请求处理器"""
        return web_response.Response(
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        )
    
    async def chat_handler(self, request: web_request.Request) -> web_response.Response:
        """普通聊天API处理器（非流式）"""
        try:
            data = await request.json()
            user_input = data.get('user_input', '').strip()
            
            if not user_input:
                return web_response.json_response(
                    {"error": "user_input is required"}, 
                    status=400
                )
            
            # 收集SSE数据
            sse_events = []
            
            async def collect_sse_data(data: str):
                sse_events.append(data)
            
            # 处理请求
            result = await self.api.process_simple_request(
                user_input=user_input,
                response_writer=collect_sse_data
            )
            
            # 返回结果和SSE事件
            return web_response.json_response({
                "result": result,
                "sse_events": sse_events
            }, headers={'Access-Control-Allow-Origin': '*'})
            
        except Exception as e:
            return web_response.json_response(
                {"error": str(e)}, 
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )
    
    async def chat_stream_handler(self, request: web_request.Request) -> web_response.StreamResponse:
        """SSE流式聊天处理器"""
        user_input = request.query.get('user_input', '').strip()
        include_metadata = request.query.get('include_metadata', 'false').lower() == 'true'
        
        if not user_input:
            return web_response.json_response(
                {"error": "user_input parameter is required"}, 
                status=400
            )
        
        # 创建SSE响应
        response = web_response.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
            }
        )
        
        await response.prepare(request)
        
        try:
            # SSE写入函数
            async def write_sse_data(data: str):
                await response.write(data.encode('utf-8'))
                await response.drain()
            
            # 发送初始连接事件
            await write_sse_data(f"event: connection\ndata: {{\"status\": \"connected\", \"timestamp\": \"{datetime.now().isoformat()}\"}}\n\n")
            
            # 处理请求
            result = await self.api.process_request_stream(
                user_input=user_input,
                response_writer=write_sse_data,
                include_metadata=include_metadata
            )
            
            # 发送完成事件
            await write_sse_data(f"event: complete\ndata: {json.dumps(result, ensure_ascii=False)}\n\n")
            
        except Exception as e:
            # 发送错误事件
            error_data = {
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
            await write_sse_data(f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n")
        
        finally:
            await response.write_eof()
        
        return response
    
    async def start_server(self):
        """启动服务器"""
        if not AIOHTTP_AVAILABLE:
            print("❌ aiohttp 未安装，无法启动HTTP服务器")
            print("请运行: pip install aiohttp")
            return
        
        print(f"🚀 启动GTPlanner SSE服务器...")
        print(f"📍 地址: http://{self.host}:{self.port}")
        print(f"🔗 API文档: http://{self.host}:{self.port}/health")
        print(f"🎯 演示页面: http://{self.host}:{self.port}/")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        print("✅ 服务器启动成功！按 Ctrl+C 停止服务器")
        
        try:
            # 保持服务器运行
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 正在停止服务器...")
        finally:
            await runner.cleanup()


async def main():
    """主函数"""
    server = GTPlannerSSEServer()
    await server.start_server()


if __name__ == "__main__":
    asyncio.run(main())
