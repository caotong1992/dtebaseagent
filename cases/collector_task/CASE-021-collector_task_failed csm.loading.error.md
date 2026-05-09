---
case_id: CASE-021
title: 采集任务失败,last_error_code为:csm.loading.error
category: collector_task
severity: medium
created_at: 2024-02-10T09:00:00
updated_at: 2024-02-10T10:30:00
tags:
  - collector task
  - csm.loading.error
---

## 问题现象

采集任务失败,last_error_code为:csm.loading.error

## 症状列表

- 采集任务失败
- 数据不一致
- 采集任务管理表，last_error_code为:csm.loading.error

## 分析过程

1. 查询DTEBaseService服务部署节点。查询方式：ssh登录在om节点并切换至root用户，执行命令：
   ```
   su - ossadm -c `cd /opt/oss/manager/agent/bin;./ipmc_adm -cmd statusapp DTEBaseService -nodeip global -tenant NCE`
   ```
2. 根据查询每个节点InvFederatedService日志，查询方式：ssh登录DTEBaseService服务所在节点，并执行如下命令：
   ```
   cd /opt/oss/log/*/DTEBaseService/dtebaseservice-*/invfederatedservice/;zgrep {taskid} invfederatedservice*.log 
   ```

3.查看失败原因

## 解决方案

1. 根据错误原因整改