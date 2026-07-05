# 测试8001端口是否正常工作
curl -X POST "http://localhost:8001/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"你好"}]}' \
  -N

# 测试完整的8000端口流程（需要先获取token）
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"你好"}' \
  -N