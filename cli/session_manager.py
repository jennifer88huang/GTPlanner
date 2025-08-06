"""
会话管理器 (SessionManager)

管理GTPlanner CLI的多轮对话会话：
1. 会话创建和恢复
2. 上下文状态持久化
3. 对话历史管理
4. 会话元数据管理
5. 自动保存和清理机制

支持ReAct主控制器的上下文对话功能。
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from agent.shared import SharedState


class SessionManager:
    """CLI会话管理器"""

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
        self.current_shared_state: Optional[SharedState] = None
        
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
        
        # 创建新的共享状态
        shared_state = SharedState()
        
        # 设置会话元数据
        session_metadata = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "user_name": user_name,
            "message_count": 0,
            "react_cycles": 0,
            "current_stage": "initialization",
            "title": "新会话"  # 将根据第一条消息自动生成
        }
        
        # 保存会话
        self._save_session(session_id, shared_state.data, session_metadata)
        
        # 设置为当前会话
        self.current_session_id = session_id
        self.current_shared_state = shared_state
        
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
                session_data = json.load(f)
            
            # 恢复共享状态
            shared_state = SharedState()
            shared_state.data = session_data.get("shared_state", {})
            
            # 设置为当前会话
            self.current_session_id = session_id
            self.current_shared_state = shared_state
            
            # 更新最后访问时间
            metadata = session_data.get("metadata", {})
            metadata["last_updated"] = datetime.now().isoformat()
            self._save_session(session_id, shared_state.data, metadata)
            
            return True
            
        except Exception as e:
            print(f"加载会话失败: {e}")
            return False

    def save_current_session(self):
        """保存当前会话"""
        if self.current_session_id and self.current_shared_state:
            # 获取现有元数据
            metadata = self._get_session_metadata(self.current_session_id)
            if metadata:
                # 更新统计信息
                metadata["last_updated"] = datetime.now().isoformat()
                metadata["message_count"] = len(self.current_shared_state.data.get("dialogue_history", {}).get("messages", []))
                metadata["react_cycles"] = self.current_shared_state.data.get("react_cycle_count", 0)
                metadata["current_stage"] = self.current_shared_state.data.get("current_stage", "unknown")
                
                # 自动生成会话标题（基于第一条用户消息）
                if metadata.get("title") == "新会话":
                    messages = self.current_shared_state.data.get("dialogue_history", {}).get("messages", [])
                    if messages:
                        first_message = messages[0].get("content", "")
                        if first_message:
                            # 取前30个字符作为标题
                            metadata["title"] = first_message[:30] + ("..." if len(first_message) > 30 else "")
                
                self._save_session(self.current_session_id, self.current_shared_state.data, metadata)

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
                    session_data = json.load(f)
                
                metadata = session_data.get("metadata", {})
                sessions.append({
                    "session_id": metadata.get("session_id", session_file.stem),
                    "title": metadata.get("title", "未命名会话"),
                    "created_at": metadata.get("created_at", ""),
                    "last_updated": metadata.get("last_updated", ""),
                    "message_count": metadata.get("message_count", 0),
                    "react_cycles": metadata.get("react_cycles", 0),
                    "current_stage": metadata.get("current_stage", "unknown"),
                    "user_name": metadata.get("user_name")
                })
                
            except Exception as e:
                print(f"读取会话文件 {session_file} 失败: {e}")
                continue
        
        # 按最后更新时间排序
        sessions.sort(key=lambda x: x["last_updated"], reverse=True)
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
                    self.current_shared_state = None
                
                return True
            
            return False
            
        except Exception as e:
            print(f"删除会话失败: {e}")
            return False

    def get_current_session_info(self) -> Optional[Dict[str, Any]]:
        """获取当前会话信息"""
        if not self.current_session_id:
            return None
        
        metadata = self._get_session_metadata(self.current_session_id)
        if metadata:
            return {
                "session_id": self.current_session_id,
                "title": metadata.get("title", "未命名会话"),
                "created_at": metadata.get("created_at", ""),
                "message_count": len(self.current_shared_state.data.get("dialogue_history", {}).get("messages", [])),
                "react_cycles": self.current_shared_state.data.get("react_cycle_count", 0),
                "current_stage": self.current_shared_state.data.get("current_stage", "unknown")
            }
        
        return None

    def add_user_message(self, message: str):
        """添加用户消息到当前会话"""
        if self.current_shared_state:
            self.current_shared_state.add_user_message(message)
            self.save_current_session()

    def add_assistant_message(self, message: str):
        """添加助手消息到当前会话"""
        if self.current_shared_state:
            self.current_shared_state.add_assistant_message(message)
            self.save_current_session()

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取当前会话的对话历史"""
        if self.current_shared_state:
            return self.current_shared_state.data.get("dialogue_history", {}).get("messages", [])
        return []

    def _save_session(self, session_id: str, shared_state_data: Dict[str, Any], metadata: Dict[str, Any]):
        """保存会话到文件"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            session_data = {
                "metadata": metadata,
                "shared_state": shared_state_data
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            print(f"保存会话失败: {e}")

    def _get_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话元数据"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            return session_data.get("metadata", {})
            
        except Exception as e:
            print(f"读取会话元数据失败: {e}")
            return None

    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.session_ttl_days)
            
            for session_file in self.sessions_dir.glob("*.json"):
                try:
                    # 检查文件修改时间
                    file_mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        session_file.unlink()
                        
                except Exception as e:
                    print(f"清理会话文件 {session_file} 失败: {e}")
                    continue
            
            # 如果会话数量超过限制，删除最旧的会话
            session_files = list(self.sessions_dir.glob("*.json"))
            if len(session_files) > self.max_sessions:
                # 按修改时间排序，删除最旧的
                session_files.sort(key=lambda f: f.stat().st_mtime)
                for old_file in session_files[:-self.max_sessions]:
                    try:
                        old_file.unlink()
                    except Exception as e:
                        print(f"删除旧会话文件 {old_file} 失败: {e}")
                        
        except Exception as e:
            print(f"清理过期会话失败: {e}")

    def export_session(self, session_id: str, export_path: str) -> bool:
        """
        导出会话到指定路径
        
        Args:
            session_id: 会话ID
            export_path: 导出路径
            
        Returns:
            是否导出成功
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            if not session_file.exists():
                return False
            
            # 复制会话文件
            import shutil
            shutil.copy2(session_file, export_path)
            
            return True
            
        except Exception as e:
            print(f"导出会话失败: {e}")
            return False

    def import_session(self, import_path: str) -> Optional[str]:
        """
        从指定路径导入会话
        
        Args:
            import_path: 导入路径
            
        Returns:
            导入的会话ID，失败返回None
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # 生成新的会话ID
            new_session_id = str(uuid.uuid4())[:8]
            
            # 更新元数据
            metadata = session_data.get("metadata", {})
            metadata["session_id"] = new_session_id
            metadata["last_updated"] = datetime.now().isoformat()
            
            # 保存会话
            shared_state_data = session_data.get("shared_state", {})
            self._save_session(new_session_id, shared_state_data, metadata)
            
            return new_session_id
            
        except Exception as e:
            print(f"导入会话失败: {e}")
            return None
