"""
Agent Function Calling工具包装器测试

测试现有子Agent节点的Function Calling包装功能。
"""

import pytest
import asyncio
from agent.function_calling import (
    get_agent_function_definitions,
    execute_agent_tool,
    get_tool_by_name,
    validate_tool_arguments
)


class TestAgentFunctionDefinitions:
    """Agent Function定义测试"""
    
    def test_get_agent_function_definitions(self):
        """测试获取Function定义"""
        definitions = get_agent_function_definitions()
        
        # 验证返回的是列表
        assert isinstance(definitions, list)
        assert len(definitions) == 3

        # 验证每个定义的基本结构
        expected_tools = ["short_planning", "research", "architecture_design"]
        actual_tools = [tool["function"]["name"] for tool in definitions]

        for expected_tool in expected_tools:
            assert expected_tool in actual_tools

        # 验证第一个工具的详细结构
        short_planning_tool = next(
            tool for tool in definitions
            if tool["function"]["name"] == "short_planning"
        )

        assert short_planning_tool["type"] == "function"
        assert "description" in short_planning_tool["function"]
        assert "parameters" in short_planning_tool["function"]
        assert short_planning_tool["function"]["parameters"]["type"] == "object"
        assert "structured_requirements" in short_planning_tool["function"]["parameters"]["properties"]
        assert "structured_requirements" in short_planning_tool["function"]["parameters"]["required"]
    
    def test_get_tool_by_name(self):
        """测试根据名称获取工具"""
        # 获取存在的工具
        tool = get_tool_by_name("short_planning")
        assert tool is not None
        assert tool["function"]["name"] == "short_planning"

        # 获取不存在的工具
        tool = get_tool_by_name("nonexistent_tool")
        assert tool is None
    
    def test_validate_tool_arguments(self):
        """测试工具参数验证"""
        # 有效参数
        result = validate_tool_arguments("short_planning", {"structured_requirements": {}})
        assert result["valid"] is True
        assert len(result["errors"]) == 0

        # 缺少必需参数
        result = validate_tool_arguments("short_planning", {})
        assert result["valid"] is False
        assert "Missing required parameter: structured_requirements" in result["errors"]

        # 不存在的工具
        result = validate_tool_arguments("nonexistent_tool", {})
        assert result["valid"] is False
        assert "Unknown tool: nonexistent_tool" in result["errors"]


class TestAgentToolExecution:
    """Agent工具执行测试"""
    
    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        """测试执行不存在的工具"""
        result = await execute_agent_tool("unknown_tool", {})
        
        assert result["success"] is False
        assert "Unknown tool" in result["error"]
    

    
    @pytest.mark.asyncio
    async def test_execute_short_planning_missing_param(self):
        """测试短期规划缺少参数"""
        result = await execute_agent_tool("short_planning", {})
        
        assert result["success"] is False
        assert "structured_requirements is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_research_missing_param(self):
        """测试技术调研缺少参数"""
        result = await execute_agent_tool("research", {})
        
        assert result["success"] is False
        assert "research_requirements is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_architecture_design_missing_param(self):
        """测试架构设计缺少参数"""
        result = await execute_agent_tool("architecture_design", {})
        
        assert result["success"] is False
        assert "structured_requirements is required" in result["error"]
    


class TestFunctionCallingIntegration:
    """Function Calling集成测试"""
    
    def test_function_definitions_openai_format(self):
        """测试Function定义符合OpenAI格式"""
        definitions = get_agent_function_definitions()
        
        for definition in definitions:
            # 验证顶层结构
            assert "type" in definition
            assert definition["type"] == "function"
            assert "function" in definition
            
            function_def = definition["function"]
            
            # 验证function结构
            assert "name" in function_def
            assert "description" in function_def
            assert "parameters" in function_def
            
            # 验证parameters结构
            parameters = function_def["parameters"]
            assert "type" in parameters
            assert parameters["type"] == "object"
            assert "properties" in parameters
            assert "required" in parameters
            
            # 验证required参数都在properties中定义
            for required_param in parameters["required"]:
                assert required_param in parameters["properties"]
            
            # 验证每个property的结构
            for prop_name, prop_def in parameters["properties"].items():
                assert "type" in prop_def
                assert "description" in prop_def
    
    def test_tool_names_consistency(self):
        """测试工具名称一致性"""
        definitions = get_agent_function_definitions()
        
        expected_names = ["short_planning", "research", "architecture_design"]
        actual_names = [tool["function"]["name"] for tool in definitions]
        
        assert set(expected_names) == set(actual_names)
    
    def test_parameter_validation_comprehensive(self):
        """测试全面的参数验证"""
        test_cases = [
            # short_planning
            ("short_planning", {"structured_requirements": {}}, True),
            ("short_planning", {}, False),
            
            # research
            ("research", {"research_requirements": "test"}, True),
            ("research", {}, False),
            
            # architecture_design
            ("architecture_design", {"structured_requirements": {}}, True),
            ("architecture_design", {}, False),
            ("architecture_design", {
                "structured_requirements": {},
                "confirmation_document": {},
                "research_findings": {}
            }, True),
        ]
        
        for tool_name, arguments, should_be_valid in test_cases:
            result = validate_tool_arguments(tool_name, arguments)
            assert result["valid"] == should_be_valid, f"Failed for {tool_name} with {arguments}"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
