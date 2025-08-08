"""
会话管理器

为GTPlanner CLI提供对话历史持久化功能：
1. 会话创建和恢复
2. 对话历史保存和加载
3. 会话列表管理
4. 自动清理过期会话

基于Function Calling架构优化设计。
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path


class SessionManager:
    """GTPlanner CLI会话管理器"""

    def __init__(self, sessions_dir: str = ".gtplanner_sessions"):
        """
        初始化会话管理器
        
        Args:
            sessions_dir: 会话存储目录
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        
        # 当前活跃会话
        self.current_session_id: Optional[str] = None
        self.current_session_data: Dict[str, Any] = {}
        
        # 会话配置
        self.max_sessions = 50  # 最大保存会话数
        self.session_ttl_days = 30  # 会话保存天数
        
        # 自动清理过期会话
        self._cleanup_expired_sessions()

    def create_new_session(self, user_name: Optional[str] = None) -> str:
        """
        创建新会话
        
        Args:
            user_name: 用户名（可选）
            
        Returns:
            新会话ID
        """
        session_id = str(uuid.uuid4())[:8]  # 使用短UUID
        
        # 创建新的会话数据
        session_data = {
            "dialogue_history": {"messages": []},
            "current_stage": "initialization",
            # 添加工具结果状态键
            "structured_requirements": None,
            "confirmation_document": None,
            "research_findings": None,
            "agent_design_document": None,
            # 添加工具执行历史
            "tool_execution_history": []
        }
        
        # 设置会话元数据
        session_metadata = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "user_name": user_name,
            "message_count": 0,
            "title": "新会话"  # 将根据第一条消息自动生成
        }
        
        # 保存会话
        self._save_session(session_id, session_data, session_metadata)
        
        # 设置为当前会话
        self.current_session_id = session_id
        self.current_session_data = session_data
        
        return session_id

    def load_session(self, session_id: str) -> bool:
        """
        加载指定会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否加载成功
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            if not session_file.exists():
                return False
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_file_data = json.load(f)
            
            # 恢复会话数据
            self.current_session_id = session_id
            self.current_session_data = session_file_data.get("session_data", {})
            
            # 更新最后访问时间
            metadata = session_file_data.get("metadata", {})
            metadata["last_updated"] = datetime.now().isoformat()
            self._save_session(session_id, self.current_session_data, metadata)
            
            return True
            
        except Exception as e:
            print(f"加载会话失败: {e}")
            return False

    def save_current_session(self):
        """保存当前会话"""
        if self.current_session_id and self.current_session_data:
            # 更新消息计数
            message_count = len(self.current_session_data.get("dialogue_history", {}).get("messages", []))
            
            # 生成会话标题（基于第一条用户消息）
            title = self._generate_session_title()
            
            metadata = {
                "session_id": self.current_session_id,
                "created_at": self._get_session_created_time(),
                "last_updated": datetime.now().isoformat(),
                "message_count": message_count,
                "title": title
            }
            
            self._save_session(self.current_session_id, self.current_session_data, metadata)

    def add_user_message(self, content: str):
        """
        添加用户消息
        
        Args:
            content: 用户消息内容
        """
        if not self.current_session_data:
            return
        
        message = {
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.current_session_data["dialogue_history"]["messages"].append(message)

    def add_assistant_message(self, content: str, tool_calls: List[Dict] = None):
        """
        添加AI助手消息
        
        Args:
            content: AI回复内容
            tool_calls: 工具调用列表（可选）
        """
        if not self.current_session_data:
            return
        
        message = {
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        if tool_calls:
            message["tool_calls"] = tool_calls
        
        self.current_session_data["dialogue_history"]["messages"].append(message)

    def get_session_data(self) -> Dict[str, Any]:
        """获取当前会话数据"""
        return self.current_session_data.copy() if self.current_session_data else {}

    def sync_tool_execution_history(self, tool_history: List[Dict[str, Any]]) -> None:
        """
        同步工具执行历史到会话数据

        Args:
            tool_history: 工具执行历史列表
        """
        if not self.current_session_data:
            return

        # 更新工具执行历史
        self.current_session_data['tool_execution_history'] = tool_history
        print(f"🔍 [DEBUG] SessionManager已同步工具执行历史，记录数: {len(tool_history)}")

    def sync_tool_result_data(self, shared_state: Dict[str, Any]) -> None:
        """
        同步工具结果数据到会话数据

        Args:
            shared_state: 共享状态字典
        """
        if not self.current_session_data:
            return

        # 同步所有工具结果状态键
        tool_result_keys = [
            'structured_requirements',
            'confirmation_document',
            'research_findings',
            'agent_design_document'
        ]

        for key in tool_result_keys:
            if key in shared_state:
                self.current_session_data[key] = shared_state[key]
                print(f"🔍 [DEBUG] SessionManager已同步工具结果: {key}")

        print(f"🔍 [DEBUG] SessionManager工具结果同步完成")

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        列出所有会话
        
        Returns:
            会话列表，按最后更新时间排序
        """
        sessions = []
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_file_data = json.load(f)
                
                metadata = session_file_data.get("metadata", {})
                sessions.append({
                    "session_id": metadata.get("session_id", session_file.stem),
                    "title": metadata.get("title", "未命名会话"),
                    "created_at": metadata.get("created_at", ""),
                    "last_updated": metadata.get("last_updated", ""),
                    "message_count": metadata.get("message_count", 0)
                })
                
            except Exception as e:
                print(f"读取会话文件失败 {session_file}: {e}")
                continue
        
        # 按最后更新时间排序
        sessions.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        删除指定会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                
                # 如果删除的是当前会话，清空当前会话
                if self.current_session_id == session_id:
                    self.current_session_id = None
                    self.current_session_data = {}
                
                return True
            return False
            
        except Exception as e:
            print(f"删除会话失败: {e}")
            return False

    def _save_session(self, session_id: str, session_data: Dict[str, Any], metadata: Dict[str, Any]):
        """保存会话到文件"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            file_data = {
                "session_data": session_data,
                "metadata": metadata
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存会话失败: {e}")

    def _generate_session_title(self) -> str:
        """生成会话标题"""
        messages = self.current_session_data.get("dialogue_history", {}).get("messages", [])
        
        # 找到第一条用户消息
        for message in messages:
            if message.get("role") == "user":
                content = message.get("content", "")
                # 截取前30个字符作为标题
                title = content[:30]
                if len(content) > 30:
                    title += "..."
                return title
        
        return "新会话"

    def _get_session_created_time(self) -> str:
        """获取会话创建时间"""
        if not self.current_session_id:
            return datetime.now().isoformat()
        
        try:
            session_file = self.sessions_dir / f"{self.current_session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_file_data = json.load(f)
                return session_file_data.get("metadata", {}).get("created_at", datetime.now().isoformat())
        except:
            pass
        
        return datetime.now().isoformat()

    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.session_ttl_days)
            
            for session_file in self.sessions_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_file_data = json.load(f)
                    
                    created_at_str = session_file_data.get("metadata", {}).get("created_at", "")
                    if created_at_str:
                        created_at = datetime.fromisoformat(created_at_str)
                        if created_at < cutoff_date:
                            session_file.unlink()
                            
                except Exception:
                    continue
            
            # 如果会话数量超过限制，删除最旧的会话
            sessions = self.list_sessions()
            if len(sessions) > self.max_sessions:
                sessions_to_delete = sessions[self.max_sessions:]
                for session in sessions_to_delete:
                    self.delete_session(session["session_id"])
                    
        except Exception as e:
            print(f"清理过期会话失败: {e}")

    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        sessions = self.list_sessions()
        
        return {
            "total_sessions": len(sessions),
            "current_session_id": self.current_session_id,
            "current_message_count": len(self.current_session_data.get("dialogue_history", {}).get("messages", [])),
            "sessions_dir": str(self.sessions_dir)
        }
