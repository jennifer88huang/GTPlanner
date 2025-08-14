"""
SQLite数据库架构设计

为GTPlanner对话历史持久化系统设计的完整数据库架构。
支持完整历史记录、增量存储、智能压缩和高效检索。
"""

import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime


class DatabaseSchema:
    """数据库架构管理器"""
    
    # 数据库版本，用于迁移管理
    CURRENT_VERSION = 1
    
    @staticmethod
    def get_create_tables_sql() -> dict:
        """获取所有表的创建SQL语句"""
        return {
            "sessions": """
                -- 会话表：存储对话会话的基本信息和元数据（简化版，压缩管理由compressed_context表负责）
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,                           -- 会话唯一标识符（UUID）
                    title TEXT NOT NULL,                                   -- 会话标题，用户可自定义
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 会话创建时间
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 最后更新时间（触发器自动更新）
                    project_stage TEXT NOT NULL DEFAULT 'requirements',    -- 项目阶段（保留用于兼容性）
                    total_messages INTEGER NOT NULL DEFAULT 0,             -- 消息总数（触发器自动维护）
                    total_tokens INTEGER NOT NULL DEFAULT 0,               -- token总数（用于成本统计）
                    metadata TEXT NULL,                                     -- JSON格式的扩展元数据（用户偏好、配置等）
                    status TEXT NOT NULL DEFAULT 'active'                  -- 会话状态：active, archived, deleted
                );
            """,
            
            "messages": """
                -- 消息表：存储完整的对话历史记录，永不删除，仅作为备份存储
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,                           -- 消息唯一标识符（UUID）
                    session_id TEXT NOT NULL,                              -- 所属会话ID
                    role TEXT NOT NULL,                                     -- 消息角色：user, assistant, system
                    content TEXT NOT NULL,                                  -- 消息内容（完整保存）
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 消息时间戳
                    token_count INTEGER NULL,                               -- 消息的token数量（用于统计）
                    metadata TEXT NULL,                                     -- JSON格式的消息元数据（模型参数、温度等）
                    tool_calls TEXT NULL,                                   -- JSON格式的工具调用信息（Function Calling）
                    parent_message_id TEXT NULL,                           -- 父消息ID（用于消息链追踪和对话树）
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_message_id) REFERENCES messages (message_id)
                );
            """,
            
            "compressed_context": """
                -- 压缩上下文表：存储智能压缩后的对话上下文，用于传递给Agent层
                CREATE TABLE IF NOT EXISTS compressed_context (
                    context_id TEXT PRIMARY KEY,                           -- 压缩上下文唯一标识符（UUID）
                    session_id TEXT NOT NULL,                              -- 所属会话ID
                    compression_version INTEGER NOT NULL,                  -- 压缩版本号（递增，支持压缩历史追踪）
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 压缩创建时间
                    original_message_count INTEGER NOT NULL,               -- 原始消息数量
                    compressed_message_count INTEGER NOT NULL,             -- 压缩后消息数量
                    original_token_count INTEGER NOT NULL,                 -- 原始token数量
                    compressed_token_count INTEGER NOT NULL,               -- 压缩后token数量
                    compression_ratio REAL NOT NULL,                       -- 压缩比率（compressed/original）
                    compressed_messages TEXT NOT NULL,                     -- JSON格式的压缩后消息列表
                    summary TEXT NOT NULL,                                  -- LLM生成的对话摘要
                    key_decisions TEXT NULL,                                -- JSON格式的关键决策和里程碑
                    tool_execution_results TEXT NULL,                       -- JSON格式的工具执行结果集合
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,               -- 是否为当前活跃的压缩版本
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
                );
            """,
            
            "tool_executions": """
                -- 工具执行表：记录Function Calling的详细执行信息
                CREATE TABLE IF NOT EXISTS tool_executions (
                    execution_id TEXT PRIMARY KEY,                         -- 执行唯一标识符（UUID）
                    session_id TEXT NOT NULL,                              -- 所属会话ID
                    message_id TEXT NULL,                                   -- 关联的消息ID（触发工具调用的消息）
                    tool_name TEXT NOT NULL,                                -- 工具名称（如search_web, analyze_requirements）
                    arguments TEXT NOT NULL,                                -- JSON格式的工具参数
                    result TEXT NULL,                                       -- JSON格式的工具执行结果
                    success BOOLEAN NOT NULL,                               -- 执行是否成功
                    execution_time REAL NOT NULL,                          -- 执行耗时（秒，用于性能分析）
                    started_at TIMESTAMP NOT NULL,                         -- 开始执行时间
                    completed_at TIMESTAMP NULL,                           -- 完成执行时间
                    error_message TEXT NULL,                                -- 错误信息（如果执行失败）
                    metadata TEXT NULL,                                     -- JSON格式的执行元数据（重试次数、缓存命中等）
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
                    FOREIGN KEY (message_id) REFERENCES messages (message_id) ON DELETE SET NULL
                );
            """,
            
            "search_index": """
                -- 搜索索引表：为全文搜索优化的内容索引
                CREATE TABLE IF NOT EXISTS search_index (
                    index_id TEXT PRIMARY KEY,                             -- 索引唯一标识符（UUID）
                    session_id TEXT NOT NULL,                              -- 所属会话ID
                    message_id TEXT NOT NULL,                              -- 关联的消息ID
                    content_type TEXT NOT NULL,                            -- 内容类型：message, summary, decision, requirement
                    searchable_content TEXT NOT NULL,                      -- 经过处理的可搜索内容（去除格式、提取关键信息）
                    keywords TEXT NULL,                                     -- JSON格式的提取关键词（用于快速匹配）
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 索引创建时间
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
                    FOREIGN KEY (message_id) REFERENCES messages (message_id) ON DELETE CASCADE
                );
            """,
            
            "database_metadata": """
                -- 数据库元数据表：存储数据库版本、配置等系统信息
                CREATE TABLE IF NOT EXISTS database_metadata (
                    key TEXT PRIMARY KEY,                                   -- 元数据键名（如schema_version, last_cleanup_at）
                    value TEXT NOT NULL,                                    -- 元数据值（JSON或字符串）
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP -- 最后更新时间
                );
            """
        }
    
    @staticmethod
    def get_create_indexes_sql() -> dict:
        """获取所有索引的创建SQL语句"""
        return {
            # sessions表索引 - 优化会话列表查询和过滤
            "idx_sessions_created_at": "CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions (created_at DESC);",  # 按创建时间排序
            "idx_sessions_updated_at": "CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions (updated_at DESC);",  # 按更新时间排序（最常用）
            "idx_sessions_stage": "CREATE INDEX IF NOT EXISTS idx_sessions_stage ON sessions (project_stage);",              # 按项目阶段过滤
            "idx_sessions_status": "CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions (status);",                   # 按状态过滤（active/archived）

            # messages表索引 - 优化消息查询和对话历史加载
            "idx_messages_session_id": "CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id);",                        # 按会话查询消息
            "idx_messages_timestamp": "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp DESC);",                      # 全局时间排序
            "idx_messages_role": "CREATE INDEX IF NOT EXISTS idx_messages_role ON messages (role);",                                          # 按角色过滤（user/assistant）
            "idx_messages_session_timestamp": "CREATE INDEX IF NOT EXISTS idx_messages_session_timestamp ON messages (session_id, timestamp DESC);", # 会话内时间排序（最重要）
            "idx_messages_parent": "CREATE INDEX IF NOT EXISTS idx_messages_parent ON messages (parent_message_id);",                         # 消息链追踪
            
            # compressed_context表索引
            "idx_compressed_context_session": "CREATE INDEX IF NOT EXISTS idx_compressed_context_session ON compressed_context (session_id);",
            "idx_compressed_context_version": "CREATE INDEX IF NOT EXISTS idx_compressed_context_version ON compressed_context (session_id, compression_version DESC);",
            "idx_compressed_context_active": "CREATE INDEX IF NOT EXISTS idx_compressed_context_active ON compressed_context (session_id, is_active);",
            
            # tool_executions表索引
            "idx_tool_executions_session": "CREATE INDEX IF NOT EXISTS idx_tool_executions_session ON tool_executions (session_id);",
            "idx_tool_executions_message": "CREATE INDEX IF NOT EXISTS idx_tool_executions_message ON tool_executions (message_id);",
            "idx_tool_executions_tool": "CREATE INDEX IF NOT EXISTS idx_tool_executions_tool ON tool_executions (tool_name);",
            "idx_tool_executions_time": "CREATE INDEX IF NOT EXISTS idx_tool_executions_time ON tool_executions (started_at DESC);",
            "idx_tool_executions_success": "CREATE INDEX IF NOT EXISTS idx_tool_executions_success ON tool_executions (success);",
            
            # search_index表索引
            "idx_search_index_session": "CREATE INDEX IF NOT EXISTS idx_search_index_session ON search_index (session_id);",
            "idx_search_index_message": "CREATE INDEX IF NOT EXISTS idx_search_index_message ON search_index (message_id);",
            "idx_search_index_type": "CREATE INDEX IF NOT EXISTS idx_search_index_type ON search_index (content_type);",
            
            # 全文搜索索引（SQLite FTS5）
            "fts_search_content": """
                CREATE VIRTUAL TABLE IF NOT EXISTS fts_search_content USING fts5(
                    session_id,
                    message_id,
                    content_type,
                    searchable_content,
                    keywords,
                    content='search_index',
                    content_rowid='rowid'
                );
            """,
            
            # FTS5触发器
            "fts_insert_trigger": """
                CREATE TRIGGER IF NOT EXISTS fts_search_content_insert AFTER INSERT ON search_index BEGIN
                    INSERT INTO fts_search_content(rowid, session_id, message_id, content_type, searchable_content, keywords)
                    VALUES (new.rowid, new.session_id, new.message_id, new.content_type, new.searchable_content, new.keywords);
                END;
            """,
            
            "fts_delete_trigger": """
                CREATE TRIGGER IF NOT EXISTS fts_search_content_delete AFTER DELETE ON search_index BEGIN
                    INSERT INTO fts_search_content(fts_search_content, rowid, session_id, message_id, content_type, searchable_content, keywords)
                    VALUES ('delete', old.rowid, old.session_id, old.message_id, old.content_type, old.searchable_content, old.keywords);
                END;
            """,
            
            "fts_update_trigger": """
                CREATE TRIGGER IF NOT EXISTS fts_search_content_update AFTER UPDATE ON search_index BEGIN
                    INSERT INTO fts_search_content(fts_search_content, rowid, session_id, message_id, content_type, searchable_content, keywords)
                    VALUES ('delete', old.rowid, old.session_id, old.message_id, old.content_type, old.searchable_content, old.keywords);
                    INSERT INTO fts_search_content(rowid, session_id, message_id, content_type, searchable_content, keywords)
                    VALUES (new.rowid, new.session_id, new.message_id, new.content_type, new.searchable_content, new.keywords);
                END;
            """
        }
    
    @staticmethod
    def get_update_triggers_sql() -> dict:
        """获取自动更新触发器的SQL语句"""
        return {
            # 自动更新sessions表的updated_at字段
            "sessions_update_trigger": """
                CREATE TRIGGER IF NOT EXISTS sessions_update_timestamp 
                AFTER UPDATE ON sessions
                FOR EACH ROW
                BEGIN
                    UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
                END;
            """,
            
            # 自动更新sessions表的消息计数
            "sessions_message_count_insert": """
                CREATE TRIGGER IF NOT EXISTS sessions_message_count_insert
                AFTER INSERT ON messages
                FOR EACH ROW
                BEGIN
                    UPDATE sessions 
                    SET total_messages = total_messages + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = NEW.session_id;
                END;
            """,
            
            "sessions_message_count_delete": """
                CREATE TRIGGER IF NOT EXISTS sessions_message_count_delete
                AFTER DELETE ON messages
                FOR EACH ROW
                BEGIN
                    UPDATE sessions 
                    SET total_messages = total_messages - 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = OLD.session_id;
                END;
            """
        }


def initialize_database(db_path: str) -> bool:
    """
    初始化数据库，创建所有表、索引和触发器
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        是否初始化成功
    """
    try:
        # 确保数据库目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(db_path) as conn:
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON;")
            
            # 设置WAL模式以提高并发性能
            conn.execute("PRAGMA journal_mode = WAL;")
            
            # 创建所有表
            tables_sql = DatabaseSchema.get_create_tables_sql()
            for table_name, sql in tables_sql.items():
                conn.execute(sql)
                print(f"✅ 创建表: {table_name}")
            
            # 创建所有索引
            indexes_sql = DatabaseSchema.get_create_indexes_sql()
            for index_name, sql in indexes_sql.items():
                conn.execute(sql)
                print(f"✅ 创建索引: {index_name}")
            
            # 创建触发器
            triggers_sql = DatabaseSchema.get_update_triggers_sql()
            for trigger_name, sql in triggers_sql.items():
                conn.execute(sql)
                print(f"✅ 创建触发器: {trigger_name}")
            
            # 插入数据库版本信息
            conn.execute(
                "INSERT OR REPLACE INTO database_metadata (key, value) VALUES (?, ?)",
                ("schema_version", str(DatabaseSchema.CURRENT_VERSION))
            )
            
            conn.commit()
            print(f"🎉 数据库初始化完成: {db_path}")
            return True
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False


def get_database_info(db_path: str) -> dict:
    """
    获取数据库信息
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        数据库信息字典
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 获取版本信息
            cursor.execute("SELECT value FROM database_metadata WHERE key = 'schema_version'")
            version_result = cursor.fetchone()
            version = version_result[0] if version_result else "unknown"
            
            # 获取表统计信息
            tables_info = {}
            tables = ["sessions", "messages", "compressed_context", "tool_executions", "search_index"]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                tables_info[table] = count
            
            return {
                "database_path": db_path,
                "schema_version": version,
                "tables": tables_info,
                "total_records": sum(tables_info.values())
            }
            
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # 测试数据库初始化
    test_db_path = "test_gtplanner.db"
    
    print("🧪 测试数据库架构初始化")
    print("=" * 50)
    
    if initialize_database(test_db_path):
        info = get_database_info(test_db_path)
        print("\n📊 数据库信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    # 清理测试文件
    import os
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"\n🧹 清理测试文件: {test_db_path}")
