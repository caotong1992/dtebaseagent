---
case_id: CASE-020
title: 采集任务失败
category: collector_task
severity: medium
created_at: 2024-02-10T09:00:00
updated_at: 2024-02-10T10:30:00
tags:
  - collector task
---

## 问题现象

采集任务失败

## 症状列表

- 采集任务失败
- 数据不一致

## 分析过程

1. 查询数据库: rmtaskmgmtdb，sql语句：select last\_result,last\_error\_code,last\_fail\_reason from tbl\_task\_info where task\_id={task\_id}，其中last\_result为最近一次的执行结果、last\_error\_code为最近一次的执行错误码，last\_fail\_reason为最近一次的执行错误原因。
   last\_error\_code枚举类型：
   | last\_error\_code            | 错误原因描述          | 可能原因   |
   | :--------------------------- | :-------------- | :----- |
   | csm.\_task.\_timeout         | 采集任务超时          | <br /> |
   | csm.task.load.timeout        | 采集任务预加载超时       | <br /> |
   | csm.loading.error            | 采集任务预加载失败       | <br /> |
   | csm.running.error            | 采集任务失败          | <br /> |
   | data.cleaning.error          | 后处理过程中，删除冗余数据失败 | <br /> |
   | csm.template.not.exist.error | 采集模板不存在         | <br /> |
   | send.ap.error                | 调用采集器失败         | <br /> |
   | task.stopped.manual          | 任务被手动中止         | <br /> |
2. 在知识库检索相关错误码处理流程，并按照处理流程处理。
3. 如果未检索到，请按照如下默认流程处理。

<br />