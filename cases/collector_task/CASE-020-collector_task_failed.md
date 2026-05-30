---

case_id: CASE-020
title: 采集任务失败定位指南
category: collector_task
severity: medium
created_at: 2024-02-10T09:00:00
updated_at: 2024-02-10T10:30:00
tags:

- collector task
- scene guide

---

## 问题现象

采集任务失败

## 症状列表

- 采集任务失败
- 数据不一致

## 分析过程

步骤1. 查询数据库: rmtaskmgmtdb，sql语句：select last_result,last_error_code,last_fail_reason from tbl_task_info where task_id={task_id}，其中last_result为最近一次的执行结果、last_error_code为最近一次的执行错误码，last_fail_reason为最近一次的执行错误原因。
last_error_code枚举类型：

| last_error_code            | 错误原因描述          | 可能原因   |
| :--------------------------- | :-------------- | :----- |
| csm.task.timeout             | 采集任务超时          | <br /> |
| csm.task.load.timeout        | 采集任务预加载超时       | <br /> |
| csm.loading.error            | 采集任务预加载失败       | <br /> |
| csm.running.error            | 采集任务失败          | <br /> |
| data.cleaning.error          | 后处理过程中，删除冗余数据失败 | <br /> |
| csm.template.not.exist.error | 采集模板不存在         | <br /> |
| send.ap.error                | 调用采集器失败         | <br /> |
| task.stopped.manual          | 任务被手动中止         | <br /> |
| collector_failed            | 采集失败            | <br /> |

步骤2. 解析last_fail_reason,last_fail_reason为json结构的数组，每个数组元素对应一个JOB的失败信息，每个JOB信息中包含jobId、type、errorMsg三个信息，从中提取jobId和errorMsg。errorMsg消息示例如下：
```
[
  {
    "jobId": "mockjobid-123456",
    "type": "iManagerU2000",
    "errorMsg": [
      "invcollectfram.executors.CALL_REFLECT_EXECUTE_FAIL"
    ]
  },
  {
    "jobId": "mockjobid1-123456",
    "type": "iManagerU2000",
    "errorMsg": [
      "invcollectfram.executors.CALL_REFLECT_EXECUTE_FAIL1"
    ]
  }
]
```
步骤3. 如果errorMsg不为空，执行步骤4；如果errorMsg为空，则执行步骤7。
步骤4. 在知识库检索errorMsg相关案例。
步骤5. 如果检索到相关案例，则执行步骤6；否则执行步骤7。
步骤6. 根据检索到的案例进行分析。
步骤7. 在知识库检索last_error_code相关错误处理流程，并按照处理流程处理。

## 解决方案

根据错误码执行相应的处理流程。
