# Trae MQTT Web 应用

这是一个基于 Flask 和 MQTT 的 Web 应用程序，用于实现消息的实时传输和管理。

## 主要功能

### MQTT 连接管理
- 自动连接到 MQTT 服务器
- 实时监控连接状态
- 自动重连机制

### Web 接口
- RESTful API 设计
- 实时状态查询
- 消息发送接口

### 消息处理
- 支持消息的发布
- 消息格式验证
- 错误处理机制

## API 接口说明

### 1. 获取 MQTT 连接状态
- 端点：`/api/mqtt_status`
- 方法：GET
- 返回：MQTT 客户端的连接状态

### 2. 发送消息
- 端点：`/api/send_message`
- 方法：POST
- 数据格式：JSON
- 参数：
  ```json
  {
    "message": "要发送的消息内容"
  }