import asyncio
import logging
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.call_llm import _request_llm_stream_async, settings

canvas_router = APIRouter(prefix="/canvas", tags=["canvas"])

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextSelection(BaseModel):
    text: str
    startLine: int
    endLine: int
    startOffset: int
    endOffset: int


class CanvasModifyRequest(BaseModel):
    instruction: str
    selectedText: str
    selection: TextSelection
    documentContent: str
    sessionId: Optional[str] = None
    language: Optional[str] = "zh"


async def encode_stream_generator(generator):
    """确保流式输出正确编码为UTF-8"""
    async for chunk in generator:
        if isinstance(chunk, str):
            yield chunk.encode('utf-8')
        else:
            yield chunk


def create_canvas_prompt(instruction: str, selected_text: str, document_content: str, language: str = "zh") -> str:
    """创建Canvas修改的提示词"""

    if language == "zh":
        prompt = f"""你是一个专业的文档编辑助手。用户选中了文档中的一段文本，并给出了修改指令。请根据指令对选中的文本进行修改。

**用户指令**: {instruction}

**选中的文本**:
```
{selected_text}
```

**完整文档内容**:
```
{document_content}
```

**要求**:
1. 仔细理解用户的修改指令
2. 只修改选中的文本部分，保持其他内容不变
3. 修改后的文本应该与整个文档的风格和语调保持一致
4. 如果指令不明确，请做出合理的解释和修改
5. 直接输出修改后的文本，不需要额外的解释

**修改后的文本**:"""
    else:
        prompt = f"""You are a professional document editing assistant. The user has selected a piece of text in the document and provided modification instructions. Please modify the selected text according to the instructions.

**User Instruction**: {instruction}

**Selected Text**:
```
{selected_text}
```

**Full Document Content**:
```
{document_content}
```

**Requirements**:
1. Carefully understand the user's modification instructions
2. Only modify the selected text portion, keep other content unchanged
3. The modified text should maintain consistency with the style and tone of the entire document
4. If the instruction is unclear, make reasonable interpretations and modifications
5. Output the modified text directly without additional explanations

**Modified Text**:"""

    return prompt





async def canvas_modify_stream(body: CanvasModifyRequest):
    """流式Canvas文档修改"""
    instruction = body.instruction
    selected_text = body.selectedText
    document_content = body.documentContent
    language = body.language or "zh"

    if not instruction or not selected_text:
        yield "data: [ERROR_START]\n"
        if language == "zh":
            yield "data: ❌ 缺少修改指令或选中文本\n"
        else:
            yield "data: ❌ Missing modification instruction or selected text\n"
        yield "data: [ERROR_END]\n\n"
        return

    try:
        # 创建提示词
        prompt = create_canvas_prompt(instruction, selected_text, document_content, language)

        # 发送开始信号
        yield "data: [MODIFICATION_START]\n"

        # 流式调用LLM
        model = settings.llm.model
        full_response = ""

        async for chunk in _request_llm_stream_async(prompt, model):
            if chunk:
                full_response += chunk
                # 使用占位符保护换行符，避免与SSE协议冲突
                protected_chunk = chunk.replace('\n', '<|newline|>')
                yield f"data: {protected_chunk}\n"

        # 发送结束信号
        yield "data: [MODIFICATION_END]\n\n"

        logger.info(f"Canvas modification completed. Instruction: {instruction[:50]}...")

    except Exception as e:
        logger.error(f"Error in canvas_modify_stream: {str(e)}", exc_info=True)

        yield "data: [ERROR_START]\n"
        if language == "zh":
            yield "data: ❌ 文档修改过程中发生错误，请稍后重试\n"
        else:
            yield "data: ❌ An error occurred during document modification. Please try again later\n"
        yield "data: [ERROR_END]\n\n"





@canvas_router.post("/modify")
async def canvas_modify_endpoint(body: CanvasModifyRequest):
    """Canvas文档修改流式接口"""
    return StreamingResponse(
        encode_stream_generator(canvas_modify_stream(body)),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )





# 测试函数
async def test_canvas_modify():
    """测试Canvas修改功能"""
    print("开始测试Canvas修改功能...")

    # 测试用例1: 基本修改测试
    print("\n测试用例1: 基本文本修改")
    test_selection = TextSelection(
        text="这是一段需要修改的文本",
        startLine=0,
        endLine=0,
        startOffset=0,
        endOffset=10
    )

    test_request = CanvasModifyRequest(
        instruction="让这段文字更加生动有趣",
        selectedText="这是一段需要修改的文本",
        selection=test_selection,
        documentContent="这是一段需要修改的文本。这是文档的其他内容。",
        language="zh"
    )

    try:
        print("开始流式修改...")
        async for chunk in canvas_modify_stream(test_request):
            print(chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk, end='')
    except Exception as e:
        print(f"测试出错: {e}")

    print("\n\n测试完成!")


# 如果直接运行此文件，执行测试
if __name__ == "__main__":
    asyncio.run(test_canvas_modify())