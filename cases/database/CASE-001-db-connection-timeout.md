---
case_id: CASE-001
title: 数据库连接超时问题解决
category: database
severity: high
created_at: 2024-01-15T10:30:00
updated_at: 2024-01-15T11:00:00
tags:
  - database
  - connection
  - timeout
cluster: prod-01
service: DTEBaseService
related_cases:
  - CASE-002
  - CASE-005
---

## 问题现象

数据库连接频繁超时，用户登录失败，服务响应缓慢。

## 症状列表

- 连接超时
- 服务响应缓慢
- 用户登录失败
- 错误日志显示connection timeout

## 分析过程

1. 检查数据库连接状态：`SELECT count(*) FROM pg_stat_activity`
2. 检查连接池配置：发现max_connections=50
3. 分析连接持有时间：发现长事务存在
4. 查看应用日志：发现连接池耗尽告警

## 解决方案

1. 增加连接池大小，从50调整为150
2. 设置连接超时时间为30秒
3. 启用连接健康检查
4. 定期清理空闲连接
5. 配置连接数超过80%时告警

## 验证结果

修改后连接超时问题消失，高峰期连接数维持在100左右，用户登录正常。

## 参考资料

- PostgreSQL连接池最佳实践
- DTEBaseService配置手册