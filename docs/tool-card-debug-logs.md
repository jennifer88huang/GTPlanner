# 工具卡片调试日志

## 🔍 问题描述

用户反馈：**工具调用完成后工具卡片直接不展示了**

从SSE日志来看，后端正确发送了工具调用事件：
- `tool_call_start` (starting)
- `tool_call_progress` (running)  
- `tool_call_end` (completed)

但是前端没有显示工具卡片。

## 🛠️ 添加的调试日志

为了诊断问题，我在以下关键位置添加了详细的调试日志：

### 1. 工具调用开始 (`chat-client.tsx`)

```typescript
onToolCallStart: (toolName: string, args?: Record<string, any>, callId?: string) => {
  console.log('🔧 [DEBUG] 工具调用开始:', {
    toolName,
    callId,
    latestTimestamp,
    baseTimestamp,
    toolCallTimestamp,
    newToolCall
  });

  actions.setToolCalls(prevToolCalls => {
    const updatedToolCalls = [...prevToolCalls, newToolCall];
    console.log('🔧 [DEBUG] 更新工具调用状态:', {
      previousCount: prevToolCalls.length,
      newCount: updatedToolCalls.length,
      allToolCalls: updatedToolCalls.map(tc => ({ id: tc.id, toolName: tc.toolName, status: tc.status }))
    });
    return updatedToolCalls;
  });
}
```

### 2. 工具调用进度 (`chat-client.tsx`)

```typescript
onToolCallProgress: (toolName: string, progress: string, callId?: string) => {
  console.log('🔧 [DEBUG] 工具调用进度:', {
    toolName,
    progress,
    callId,
    currentToolCallsCount: conversationState.toolCalls.length
  });

  console.log('🔧 [DEBUG] 工具调用进度更新:', {
    matchedCalls: updatedToolCalls.filter(call => call.status === 'running').length,
    allCalls: updatedToolCalls.map(tc => ({ id: tc.id, toolName: tc.toolName, status: tc.status }))
  });
}
```

### 3. 工具调用结束 (`chat-client.tsx`)

```typescript
onToolCallEnd: (toolName: string, result?: Record<string, any>, error?: string, callId?: string, executionTime?: number) => {
  console.log('🔧 [DEBUG] 工具调用结束:', {
    toolName,
    callId,
    hasResult: !!result,
    hasError: !!error,
    executionTime
  });

  actions.setToolCalls(prevToolCalls => {
    console.log('🔧 [DEBUG] 工具调用结束前状态:', {
      totalCalls: prevToolCalls.length,
      calls: prevToolCalls.map(tc => ({ id: tc.id, toolName: tc.toolName, status: tc.status }))
    });

    console.log('🔧 [DEBUG] 工具调用结束后状态:', {
      totalCalls: updatedToolCalls.length,
      completedCalls: updatedToolCalls.filter(tc => tc.status === 'completed').length,
      calls: updatedToolCalls.map(tc => ({ id: tc.id, toolName: tc.toolName, status: tc.status }))
    });

    return updatedToolCalls;
  });
}
```

### 4. 消息列表渲染 (`message-list.tsx`)

```typescript
const mixedItems = useMemo(() => {
  // ... 处理逻辑

  console.log('🔧 [DEBUG] MessageList 渲染项目:', {
    totalMessages: messages.length,
    totalToolCalls: toolCalls.length,
    totalItems: sortedItems.length,
    items: sortedItems.map(item => ({
      type: item.type,
      id: item.data.id,
      timestamp: item.timestamp,
      ...(item.type === 'toolCall' ? { 
        toolName: item.data.toolName, 
        status: item.data.status 
      } : {})
    }))
  });

  return sortedItems;
}, [messages, toolCalls]);
```

### 5. 单个项目渲染 (`message-list.tsx`)

```typescript
{mixedItems.map((item, index) => {
  console.log('🔧 [DEBUG] 渲染项目:', {
    index,
    type: item.type,
    id: item.data.id,
    ...(item.type === 'toolCall' ? { 
      toolName: item.data.toolName, 
      status: item.data.status 
    } : {})
  });

  return (
    // ... 渲染逻辑
  );
})}
```

## 🔍 调试步骤

现在可以通过以下步骤来诊断问题：

1. **发送一个需要工具调用的消息**
2. **打开浏览器开发者工具的控制台**
3. **观察调试日志的输出**

### 预期的日志流程

```
🔧 [DEBUG] 工具调用开始: { toolName: "short_planning", callId: "...", ... }
🔧 [DEBUG] 更新工具调用状态: { previousCount: 0, newCount: 1, ... }
🔧 [DEBUG] MessageList 渲染项目: { totalToolCalls: 1, totalItems: 2, ... }
🔧 [DEBUG] 渲染项目: { type: "toolCall", toolName: "short_planning", status: "starting" }

🔧 [DEBUG] 工具调用进度: { toolName: "short_planning", progress: "正在执行...", ... }
🔧 [DEBUG] 工具调用进度更新: { matchedCalls: 1, ... }
🔧 [DEBUG] MessageList 渲染项目: { totalToolCalls: 1, totalItems: 2, ... }
🔧 [DEBUG] 渲染项目: { type: "toolCall", toolName: "short_planning", status: "running" }

🔧 [DEBUG] 工具调用结束: { toolName: "short_planning", hasResult: true, ... }
🔧 [DEBUG] 工具调用结束前状态: { totalCalls: 1, ... }
🔧 [DEBUG] 工具调用结束后状态: { totalCalls: 1, completedCalls: 1, ... }
🔧 [DEBUG] MessageList 渲染项目: { totalToolCalls: 1, totalItems: 2, ... }
🔧 [DEBUG] 渲染项目: { type: "toolCall", toolName: "short_planning", status: "completed" }
```

## 🎯 可能的问题点

根据调试日志，可以确定问题出现在哪个环节：

### 1. 工具调用状态未添加
如果看不到 "工具调用开始" 日志：
- SSE事件处理器没有被正确调用
- `onToolCallStart` 回调没有被触发

### 2. 工具调用状态添加但未渲染
如果看到状态更新日志但看不到渲染日志：
- `conversationState.toolCalls` 状态管理有问题
- `MessageList` 组件没有接收到正确的 `toolCalls` 数据

### 3. 工具调用状态渲染但不显示
如果看到渲染日志但界面上没有工具卡片：
- `ToolSelector` 组件渲染逻辑有问题
- CSS样式问题导致工具卡片不可见

### 4. 时间戳问题
如果工具调用被添加但排序有问题：
- `latestAssistantTimestampRef.current` 为空
- 时间戳计算逻辑有误

## 🔧 下一步行动

1. **运行测试** - 发送消息并观察控制台日志
2. **定位问题** - 根据日志输出确定问题环节
3. **针对性修复** - 根据具体问题进行修复
4. **清理调试代码** - 问题解决后移除调试日志

## 📊 预期结果

修复后应该能看到：
- ✅ 工具调用状态正确添加到 `conversationState.toolCalls`
- ✅ 工具卡片正确显示在消息列表中
- ✅ 工具调用状态正确更新（starting → running → completed）
- ✅ 工具调用结果正确显示为格式化的Markdown内容

现在请测试一下，看看控制台输出什么调试信息！🔍
