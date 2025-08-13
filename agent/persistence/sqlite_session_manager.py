"""
基于SQLite的会话和消息管理系统

完全替换现有的文件存储方式，使用SQLite数据库进行高效的会话和消息管理。
支持与StatelessGTPlanner的AgentContext转换，兼容流式响应系统。
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .database_dao import DatabaseDAO
from ..context_types import AgentContext, Message, MessageRole, ProjectStage, ToolExecution


class SQLiteSessionManager:
    """基于SQLite的会话管理器"""
    
    def __init__(self, db_path: str = "gtplanner_conversations.db"):
        """
        初始化SQLite会话管理器

        Args:
            db_path: 数据库文件路径
        """
        self.dao = DatabaseDAO(db_path)
        self.current_session_id: Optional[str] = None
        self._compressor = None  # 延迟初始化压缩器
        self._session_cache = {}  # 会话缓存

    @property
    def compressor(self):
        """获取压缩器实例（延迟初始化）"""
        if self._compressor is None:
            from .smart_compressor import SmartCompressor
            self._compressor = SmartCompressor(self)
        return self._compressor
    
    # ==================== 会话管理 ====================
    
    def create_new_session(self, title: Optional[str] = None, 
                          project_stage: str = "requirements") -> str:
        """
        创建新会话
        
        Args:
            title: 会话标题，如果为None则自动生成
            project_stage: 项目阶段
            
        Returns:
            新会话的ID
        """
        if not title:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            title = f"新会话 - {timestamp}"
        
        # 创建会话
        session_id = self.dao.create_session(
            title=title,
            project_stage=project_stage,
            metadata={
                "created_by": "sqlite_session_manager",
                "version": "1.0"
            }
        )
        
        # 设置为当前会话
        self.current_session_id = session_id
        
        # 清除缓存
        self._session_cache.clear()
        
        return session_id
    
    def load_session(self, session_id: str) -> bool:
        """
        加载指定会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否加载成功
        """
        session = self.dao.get_session(session_id)
        if session and session["status"] == "active":
            self.current_session_id = session_id
            # 清除缓存以强制重新加载
            self._session_cache.clear()
            return True
        return False
    
    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """
        获取当前会话信息
        
        Returns:
            当前会话信息或None
        """
        if not self.current_session_id:
            return None
        
        # 使用缓存
        if self.current_session_id in self._session_cache:
            return self._session_cache[self.current_session_id]
        
        session = self.dao.get_session(self.current_session_id)
        if session:
            self._session_cache[self.current_session_id] = session
        
        return session
    
    def list_sessions(self, limit: int = 50, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        列出会话
        
        Args:
            limit: 限制数量
            include_archived: 是否包含已归档的会话
            
        Returns:
            会话列表
        """
        if include_archived:
            # 获取活跃和已归档的会话
            active_sessions = self.dao.list_sessions(limit=limit//2, status="active")
            archived_sessions = self.dao.list_sessions(limit=limit//2, status="archived")
            return active_sessions + archived_sessions
        else:
            return self.dao.list_sessions(limit=limit, status="active")
    
    def update_session_title(self, title: str, session_id: Optional[str] = None) -> bool:
        """
        更新会话标题
        
        Args:
            title: 新标题
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            是否更新成功
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False
        
        success = self.dao.update_session(target_session_id, title=title)
        if success and target_session_id in self._session_cache:
            # 更新缓存
            self._session_cache[target_session_id]["title"] = title
        
        return success
    
    def update_project_stage(self, stage: str, session_id: Optional[str] = None) -> bool:
        """
        更新项目阶段
        
        Args:
            stage: 新的项目阶段
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            是否更新成功
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False
        
        success = self.dao.update_session(target_session_id, project_stage=stage)
        if success and target_session_id in self._session_cache:
            # 更新缓存
            self._session_cache[target_session_id]["project_stage"] = stage
        
        return success
    
    def archive_session(self, session_id: Optional[str] = None) -> bool:
        """
        归档会话
        
        Args:
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            是否归档成功
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False
        
        success = self.dao.update_session(target_session_id, status="archived")
        if success:
            # 如果归档的是当前会话，清除当前会话
            if target_session_id == self.current_session_id:
                self.current_session_id = None
            
            # 清除缓存
            if target_session_id in self._session_cache:
                del self._session_cache[target_session_id]
        
        return success
    
    def delete_session(self, session_id: Optional[str] = None) -> bool:
        """
        删除会话（软删除）
        
        Args:
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            是否删除成功
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False
        
        success = self.dao.delete_session(target_session_id)
        if success:
            # 如果删除的是当前会话，清除当前会话
            if target_session_id == self.current_session_id:
                self.current_session_id = None
            
            # 清除缓存
            if target_session_id in self._session_cache:
                del self._session_cache[target_session_id]
        
        return success
    
    # ==================== 消息管理 ====================
    
    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None,
                        session_id: Optional[str] = None) -> Optional[str]:
        """
        添加用户消息
        
        Args:
            content: 消息内容
            metadata: 消息元数据
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            消息ID或None（如果失败）
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return None
        
        # 估算token数量（简单估算）
        token_count = len(content.split()) * 1.3  # 粗略估算
        
        message_id = self.dao.add_message(
            session_id=target_session_id,
            role="user",
            content=content,
            metadata=metadata,
            token_count=int(token_count)
        )
        
        # 清除会话缓存以更新统计信息
        if target_session_id in self._session_cache:
            del self._session_cache[target_session_id]
        
        return message_id
    
    def add_assistant_message(self, content: str, 
                            metadata: Optional[Dict[str, Any]] = None,
                            tool_calls: Optional[List[Dict[str, Any]]] = None,
                            parent_message_id: Optional[str] = None,
                            session_id: Optional[str] = None) -> Optional[str]:
        """
        添加助手消息
        
        Args:
            content: 消息内容
            metadata: 消息元数据
            tool_calls: 工具调用信息
            parent_message_id: 父消息ID
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            消息ID或None（如果失败）
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return None
        
        # 估算token数量
        token_count = len(content.split()) * 1.3
        
        message_id = self.dao.add_message(
            session_id=target_session_id,
            role="assistant",
            content=content,
            metadata=metadata,
            tool_calls=tool_calls,
            parent_message_id=parent_message_id,
            token_count=int(token_count)
        )
        
        # 清除会话缓存以更新统计信息
        if target_session_id in self._session_cache:
            del self._session_cache[target_session_id]
        
        return message_id
    
    def get_messages(self, limit: Optional[int] = None, 
                    session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取会话消息
        
        Args:
            limit: 限制数量
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            消息列表
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return []
        
        return self.dao.get_messages(target_session_id, limit=limit)
    
    def get_recent_messages(self, count: int = 10, 
                          session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取最近的消息
        
        Args:
            count: 消息数量
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            最近的消息列表
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return []
        
        return self.dao.get_recent_messages(target_session_id, count=count)

    # ==================== 工具执行管理 ====================

    def add_tool_execution(self, tool_execution: ToolExecution,
                          message_id: Optional[str] = None,
                          session_id: Optional[str] = None) -> Optional[str]:
        """
        添加工具执行记录

        Args:
            tool_execution: 工具执行对象
            message_id: 关联的消息ID
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            执行ID或None（如果失败）
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return None

        return self.dao.add_tool_execution(
            session_id=target_session_id,
            tool_name=tool_execution.tool_name,
            arguments=tool_execution.arguments,
            result=tool_execution.result,
            success=tool_execution.success,
            execution_time=tool_execution.execution_time,
            message_id=message_id,
            error_message=tool_execution.error_message,
            metadata={
                "timestamp": tool_execution.timestamp,
                "execution_id": tool_execution.id
            }
        )

    def get_tool_executions(self, limit: Optional[int] = None,
                           session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取工具执行记录

        Args:
            limit: 限制数量
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            工具执行记录列表
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return []

        return self.dao.get_tool_executions(target_session_id, limit=limit)

    # ==================== AgentContext转换 ====================

    def build_agent_context(self, session_id: Optional[str] = None,
                           include_recent_only: bool = False,
                           recent_count: int = 20) -> Optional[AgentContext]:
        """
        构建AgentContext对象

        Args:
            session_id: 会话ID，如果为None则使用当前会话
            include_recent_only: 是否只包含最近的消息
            recent_count: 最近消息的数量

        Returns:
            AgentContext对象或None
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return None

        # 获取会话信息
        session = self.dao.get_session(target_session_id)
        if not session:
            return None

        # 获取消息
        if include_recent_only:
            message_data = self.dao.get_recent_messages(target_session_id, count=recent_count)
        else:
            message_data = self.dao.get_messages(target_session_id)

        # 转换消息格式
        dialogue_history = []
        for msg_data in message_data:
            message = Message(
                role=MessageRole(msg_data["role"]),
                content=msg_data["content"],
                timestamp=msg_data["timestamp"],
                metadata=msg_data["metadata"],
                tool_calls=msg_data["tool_calls"]
            )
            dialogue_history.append(message)

        # 获取工具执行历史
        tool_execution_data = self.dao.get_tool_executions(target_session_id)
        tool_execution_history = []

        for exec_data in tool_execution_data:
            tool_execution = ToolExecution(
                id=exec_data["execution_id"],
                tool_name=exec_data["tool_name"],
                arguments=exec_data["arguments"],
                result=exec_data["result"],
                success=exec_data["success"],
                execution_time=exec_data["execution_time"],
                timestamp=exec_data["started_at"],
                error_message=exec_data["error_message"]
            )
            tool_execution_history.append(tool_execution)

        # 构建项目状态（从会话元数据中获取）
        project_state = session["metadata"].get("project_state", {})

        # 构建AgentContext
        context = AgentContext(
            session_id=target_session_id,
            dialogue_history=dialogue_history,
            current_stage=ProjectStage(session["project_stage"]),
            project_state=project_state,
            tool_execution_history=tool_execution_history,
            session_metadata=session["metadata"]
        )

        return context

    def update_from_agent_result(self, agent_result, session_id: Optional[str] = None) -> bool:
        """
        从AgentResult更新会话数据

        Args:
            agent_result: StatelessGTPlanner的处理结果
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            是否更新成功
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False

        try:
            # 保存新的助手消息
            for message in agent_result.new_assistant_messages:
                self.add_assistant_message(
                    content=message.content,
                    metadata=message.metadata,
                    tool_calls=message.tool_calls,
                    session_id=target_session_id
                )

            # 保存新的工具执行记录
            for tool_execution in agent_result.new_tool_executions:
                self.add_tool_execution(
                    tool_execution=tool_execution,
                    session_id=target_session_id
                )

            # 更新项目状态（如果有变化）
            if hasattr(agent_result, 'updated_project_state') and agent_result.updated_project_state:
                session = self.get_current_session()
                if session:
                    updated_metadata = session["metadata"].copy()
                    updated_metadata["project_state"] = agent_result.updated_project_state
                    self.dao.update_session(target_session_id, metadata=updated_metadata)

            # 更新项目阶段（如果有变化）
            if hasattr(agent_result, 'updated_stage') and agent_result.updated_stage:
                self.update_project_stage(agent_result.updated_stage.value, target_session_id)

            return True

        except Exception as e:
            print(f"更新会话数据失败: {e}")
            return False

    # ==================== 搜索和统计 ====================

    def search_sessions(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索会话

        Args:
            keyword: 搜索关键词
            limit: 结果限制

        Returns:
            匹配的会话列表
        """
        return self.dao.search_sessions_by_keyword(keyword, limit=limit)

    def get_session_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取会话统计信息

        Args:
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            统计信息字典
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return {}

        return self.dao.get_session_statistics(target_session_id)

    def get_global_statistics(self) -> Dict[str, Any]:
        """
        获取全局统计信息

        Returns:
            全局统计信息字典
        """
        return self.dao.get_global_statistics()

    # ==================== 工具执行管理 ====================

    def add_tool_execution(self, tool_execution: ToolExecution,
                          message_id: Optional[str] = None,
                          session_id: Optional[str] = None) -> Optional[str]:
        """
        添加工具执行记录

        Args:
            tool_execution: 工具执行对象
            message_id: 关联的消息ID
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            执行ID或None（如果失败）
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return None

        return self.dao.add_tool_execution(
            session_id=target_session_id,
            tool_name=tool_execution.tool_name,
            arguments=tool_execution.arguments,
            result=tool_execution.result,
            success=tool_execution.success,
            execution_time=tool_execution.execution_time,
            message_id=message_id,
            error_message=tool_execution.error_message,
            metadata={
                "timestamp": tool_execution.timestamp,
                "execution_id": tool_execution.id
            }
        )

    def get_tool_executions(self, limit: Optional[int] = None,
                           session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取工具执行记录

        Args:
            limit: 限制数量
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            工具执行记录列表
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return []

        return self.dao.get_tool_executions(target_session_id, limit=limit)

    # ==================== AgentContext转换 ====================

    def build_agent_context(self, session_id: Optional[str] = None,
                           include_recent_only: bool = False,
                           recent_count: int = 20) -> Optional[AgentContext]:
        """
        构建AgentContext对象

        Args:
            session_id: 会话ID，如果为None则使用当前会话
            include_recent_only: 是否只包含最近的消息
            recent_count: 最近消息的数量

        Returns:
            AgentContext对象或None
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return None

        # 获取会话信息
        session = self.dao.get_session(target_session_id)
        if not session:
            return None

        # 获取消息
        if include_recent_only:
            message_data = self.dao.get_recent_messages(target_session_id, count=recent_count)
        else:
            message_data = self.dao.get_messages(target_session_id)

        # 转换消息格式
        dialogue_history = []
        for msg_data in message_data:
            message = Message(
                role=MessageRole(msg_data["role"]),
                content=msg_data["content"],
                timestamp=msg_data["timestamp"],
                metadata=msg_data["metadata"],
                tool_calls=msg_data["tool_calls"]
            )
            dialogue_history.append(message)

        # 获取工具执行历史
        tool_execution_data = self.dao.get_tool_executions(target_session_id)
        tool_execution_history = []

        for exec_data in tool_execution_data:
            tool_execution = ToolExecution(
                id=exec_data["execution_id"],
                tool_name=exec_data["tool_name"],
                arguments=exec_data["arguments"],
                result=exec_data["result"],
                success=exec_data["success"],
                execution_time=exec_data["execution_time"],
                timestamp=exec_data["started_at"],
                error_message=exec_data["error_message"]
            )
            tool_execution_history.append(tool_execution)

        # 构建项目状态（从会话元数据中获取）
        project_state = session["metadata"].get("project_state", {})

        # 构建AgentContext
        context = AgentContext(
            session_id=target_session_id,
            dialogue_history=dialogue_history,
            current_stage=ProjectStage(session["project_stage"]),
            project_state=project_state,
            tool_execution_history=tool_execution_history,
            session_metadata=session["metadata"]
        )

        return context

    def update_from_agent_result(self, agent_result, session_id: Optional[str] = None) -> bool:
        """
        从AgentResult更新会话数据

        Args:
            agent_result: StatelessGTPlanner的处理结果
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            是否更新成功
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False

        try:
            # 保存新的助手消息
            for message in agent_result.new_assistant_messages:
                self.add_assistant_message(
                    content=message.content,
                    metadata=message.metadata,
                    tool_calls=message.tool_calls,
                    session_id=target_session_id
                )

            # 保存新的工具执行记录
            for tool_execution in agent_result.new_tool_executions:
                self.add_tool_execution(
                    tool_execution=tool_execution,
                    session_id=target_session_id
                )

            # 更新项目状态（如果有变化）
            if hasattr(agent_result, 'updated_project_state') and agent_result.updated_project_state:
                session = self.get_current_session()
                if session:
                    updated_metadata = session["metadata"].copy()
                    updated_metadata["project_state"] = agent_result.updated_project_state
                    self.dao.update_session(target_session_id, metadata=updated_metadata)

            # 更新项目阶段（如果有变化）
            if hasattr(agent_result, 'updated_stage') and agent_result.updated_stage:
                self.update_project_stage(agent_result.updated_stage.value, target_session_id)

            return True

        except Exception as e:
            print(f"更新会话数据失败: {e}")
            return False

    # ==================== 搜索和统计 ====================

    def search_sessions(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索会话

        Args:
            keyword: 搜索关键词
            limit: 结果限制

        Returns:
            匹配的会话列表
        """
        return self.dao.search_sessions_by_keyword(keyword, limit=limit)

    def get_session_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取会话统计信息

        Args:
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            统计信息字典
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return {}

        return self.dao.get_session_statistics(target_session_id)

    def get_global_statistics(self) -> Dict[str, Any]:
        """
        获取全局统计信息

        Returns:
            全局统计信息字典
        """
        return self.dao.get_global_statistics()


