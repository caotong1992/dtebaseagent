---
case_id: CASE-020
title: 采集任务失败
category: collector_task
severity: medium
created_at: 2024-02-10T09:00:00
updated_at: 2024-02-10T10:30:00
tags:
  - database
  - performance
  - slow-query
---

## 问题现象

数据库查询响应时间过长，部分查询耗时超过5秒，影响服务整体性能。

## 症状列表

- 查询响应缓慢
- 数据库CPU使用率高
- 慢查询日志记录频繁

## 分析过程

1. 使用pg_stat_statements查看慢查询
2. 分析执行计划发现全表扫描
3. 检查索引发现缺失关键索引
4. 分析查询语句发现未使用索引提示

## 解决方案

1. 为高频查询字段创建索引
2. 优化查询语句使用索引提示
3. 增加查询超时限制
4. 定期分析慢查询日志

## 验证结果

查询平均响应时间从5秒降低到200ms，数据库CPU使用率下降30%。

## 参考资料

- PostgreSQL索引优化指南
- SQL查询优化最佳实践