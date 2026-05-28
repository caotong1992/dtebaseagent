---

case_id: CASE-021
title: last_error_code:csm.loading.error
category: collector_task
severity: medium
created_at: 2024-02-10T09:00:00
updated_at: 2024-02-10T10:30:00
tags:

- collector task
- csm.loading.error

---

## 问题现象

rmtaskmgmtdb数据库中tbl_task_info表last_error_code字段为:csm.loading.error

## 症状列表

- last_error_code:csm.loading.error

## 分析过程

步骤1. 查询InvFederatedService日志，使用日志分析工具通过如下命令分析：

```
zgrep {taskid} invfederatedservice*.log 
```


步骤2.查看失败原因

## 解决方案

1. 根据错误原因整改

