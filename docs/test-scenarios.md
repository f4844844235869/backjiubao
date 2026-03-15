# 测试场景清单

本文档整理当前项目的测试场景名称清单，并标记当前覆盖状态，方便持续补测试。

状态说明：

- `已覆盖`：当前已有自动化测试覆盖
- `占位待实现`：接口已预留或已有测试占位，但业务尚未实现
- `待补充`：当前尚未落地自动化测试

## 一、用户注册与登录

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 1 | 小程序首次登录 | 已覆盖 | `test_miniapp_code_login_first_time_creates_user` |
| 2 | 小程序重复登录 | 已覆盖 | `test_miniapp_code_login_repeat_reuses_same_user` |
| 3 | 小程序登录用户不存在 | 已覆盖 | 首次登录会自动创建 `MINI_APP_MEMBER` 用户，见 `test_miniapp_code_login_first_time_creates_user` |
| 4 | 小程序登录用户已存在 | 已覆盖 | 重复登录会命中同一小程序账号，见 `test_miniapp_code_login_repeat_reuses_same_user` |
| 5 | 小程序登录后未绑定手机号 | 已覆盖 | `test_miniapp_me_before_bind_phone_has_empty_mobile` |
| 6 | 小程序登录后已绑定手机号 | 已覆盖 | `test_miniapp_me_after_bind_phone_returns_mobile` |
| 7 | 用户绑定手机号 | 已覆盖 | `test_miniapp_bind_phone_success` |
| 8 | 用户重复绑定手机号 | 已覆盖 | `test_miniapp_bind_phone_repeat_is_idempotent` |
| 9 | 用户绑定已存在手机号 | 已覆盖 | `test_miniapp_bind_phone_conflict_with_other_user` |
| 10 | 用户解绑手机号 | 待补充 | 功能未实现 |
| 11 | 手机号登录 | 已覆盖 | `test_backend_mobile_code_login_success`，当前为本地模拟验证码链路 |
| 12 | 手机号登录错误密码 | 已覆盖 | `test_backend_mobile_code_login_invalid_code` |
| 13 | 手机号未注册登录 | 已覆盖 | `test_backend_mobile_code_login_unregistered_mobile` |
| 14 | token登录访问接口 | 已覆盖 | `test_get_current_user_profile` |
| 15 | token过期访问接口 | 已覆盖 | `test_get_current_user_profile_with_expired_token` |
| 16 | token伪造访问接口 | 已覆盖 | `test_get_current_user_profile_with_invalid_token` |

## 二、用户账号合并

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 17 | 小程序账号绑定已有手机号 | 已覆盖 | `test_miniapp_phone_related_employees_returns_employee_history`，当前按手机号建立关联，不做账号合并；`test_miniapp_phone_related_employees_respects_current_store_context` 与 `test_miniapp_store_context_flow` 额外覆盖当前门店过滤 |
| 18 | 小程序账号合并用户 | 待补充 | 功能未实现 |
| 19 | 多小程序账号合并同一用户 | 待补充 | 功能未实现 |
| 20 | 用户解绑openid | 待补充 | 功能未实现 |
| 21 | 用户重新绑定openid | 待补充 | 功能未实现 |

## 三、员工入职

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 22 | 创建员工账号 | 已覆盖 | `test_create_employee_user_auto_builds_profile`、`test_employee_onboarding_flow` |
| 23 | 用户转员工 | 已覆盖 | `test_user_to_employee_transfer_flow` |
| 24 | 员工绑定门店 | 已覆盖 | `test_employee_onboarding_flow`、`test_store_employee_permission_flow` 通过主门店/主组织链路覆盖 |
| 25 | 员工绑定组织 | 已覆盖 | `test_employee_onboarding_flow` |
| 26 | 员工绑定角色 | 已覆盖 | `test_employee_onboarding_flow` |
| 27 | 员工绑定多个角色 | 已覆盖 | `test_multi_role_scope_union_flow` |
| 28 | 员工绑定多个门店 | 已覆盖 | `test_current_store_context_flow` |

## 四、员工权限

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 29 | 员工访问员工接口 | 已覆盖 | `test_read_employee_profile`、`test_store_employee_permission_flow` |
| 30 | 员工访问非权限接口 | 已覆盖 | `test_read_employee_profile_requires_permission` |
| 31 | 员工访问后台接口 | 已覆盖 | `test_employee_onboarding_flow` 登录后访问 `/auth/me`、`/stores/` |
| 32 | 员工访问小程序员工接口 | 已覆盖 | `test_employee_user_cannot_read_miniapp_phone_related_employees`，当前员工账号访问小程序手机号关联接口会被拒绝 |
| 33 | 员工访问普通用户接口 | 已覆盖 | `test_employee_onboarding_flow` 访问 `/users/` 被拒绝 |
| 34 | 员工跨门店访问数据 | 已覆盖 | `test_store_employee_permission_flow`、`test_employee_cross_store_access_flow` |
| 35 | 员工访问本门店数据 | 已覆盖 | `test_store_employee_permission_flow` |

## 五、员工调岗

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 36 | 员工角色变更 | 已覆盖 | `test_employee_role_change_flow` |
| 37 | 员工岗位变更 | 已覆盖 | `test_employee_position_change_flow` |
| 38 | 员工门店变更 | 已覆盖 | `test_user_to_employee_transfer_flow` 通过主组织切换带出主门店切换 |
| 39 | 员工组织变更 | 已覆盖 | `test_user_to_employee_transfer_flow` |

## 六、员工多门店

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 40 | 员工同时属于多个门店 | 已覆盖 | `test_employee_multi_store_membership_flow` |
| 41 | 员工访问多个门店数据 | 已覆盖 | `test_current_store_context_flow` |
| 42 | 员工只访问部分门店数据 | 已覆盖 | `test_current_store_context_flow` |

## 七、员工离职

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 43 | 员工离职 | 已覆盖 | `test_employee_rehire_flow` |
| 44 | 离职员工访问系统 | 已覆盖 | `test_employee_rehire_flow` 中旧账号登录被拒绝 |
| 45 | 离职员工重新入职 | 已覆盖 | `test_employee_rehire_flow` 中按新员工重新入职 |
| 46 | 离职员工权限恢复 | 已覆盖 | `test_employee_rehire_flow`，再次入职默认不恢复历史权限，需重新授权 |

## 八、角色权限

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 47 | 创建角色 | 已覆盖 | `test_create_role` 隐含于 `test_org_iam.py`、场景测试 |
| 48 | 修改角色 | 已覆盖 | `test_update_role` |
| 49 | 删除角色 | 已覆盖 | `test_delete_role` |
| 50 | 角色绑定权限 | 已覆盖 | `test_employee_onboarding_flow`、`test_store_employee_permission_flow` |
| 51 | 角色解绑权限 | 已覆盖 | `test_unbind_role_permissions_takes_effect_immediately` |
| 52 | 角色权限变更生效 | 已覆盖 | `test_read_user_authorization_summary`、授权摘要接口 |

## 九、权限控制

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 53 | 用户无权限访问接口 | 已覆盖 | `test_list_users_requires_permission` |
| 54 | 用户拥有权限访问接口 | 已覆盖 | `test_employee_onboarding_flow`、`test_store_employee_permission_flow` |
| 55 | 用户越权访问接口 | 已覆盖 | `test_store_employee_permission_flow` 中授权越权与跨店越权 |
| 56 | 用户访问跨门店数据 | 已覆盖 | `test_store_employee_permission_flow` |
| 57 | 用户访问跨组织数据 | 已覆盖 | `test_store_employee_permission_flow` 中组织绑定与员工档案读取 |

## 十、组织结构

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 58 | 创建组织节点 | 已覆盖 | `test_create_org_node` |
| 59 | 修改组织节点 | 已覆盖 | `test_update_org_node`、`test_store_org_maintenance_flow` |
| 60 | 删除组织节点 | 已覆盖 | `test_delete_org_node_success_when_unreferenced`、`test_delete_org_node_soft_disables_when_only_historical_refs`、`test_store_org_deletion_boundary_flow` |
| 61 | 组织权限继承 | 已覆盖 | `test_org_inheritance_flow` |
| 62 | 组织权限隔离 | 已覆盖 | `test_store_employee_permission_flow` |

## 十一、门店权限

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 63 | 创建门店 | 已覆盖 | `test_create_store` |
| 64 | 修改门店 | 已覆盖 | `test_update_store`、`test_store_org_maintenance_flow` |
| 65 | 删除门店 | 已覆盖 | `test_delete_store_success_when_unreferenced`、`test_delete_store_soft_disables_when_only_historical_refs`、`test_store_org_deletion_boundary_flow` |
| 66 | 门店数据权限控制 | 已覆盖 | `test_store_employee_permission_flow` |
| 67 | 门店数据隔离 | 已覆盖 | `test_store_employee_permission_flow`、`test_employee_cross_store_access_flow` |

## 十二、小程序员工场景

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 68 | 小程序员工登录 | 已覆盖 | 当前为模拟小程序登录链路，已覆盖首次登录、重复登录、手机号绑定 |
| 69 | 小程序员工访问员工接口 | 已覆盖 | `test_miniapp_user_can_read_employee_profile_after_assign_permission_and_scope`、`test_miniapp_store_context_flow`、`test_backend_miniapp_end_to_end_flow` |
| 70 | 小程序员工访问普通用户接口 | 已覆盖 | `test_miniapp_user_with_employee_permission_still_cannot_list_users` |
| 71 | 小程序普通用户访问员工接口 | 已覆盖 | `test_miniapp_user_cannot_read_employee_profile_without_permission` |

## 十三、安全场景

| 编号 | 场景名称 | 当前状态 | 对应测试或说明 |
| --- | --- | --- | --- |
| 72 | 无token访问接口 | 已覆盖 | `test_get_current_user_profile_without_token` |
| 73 | 非法token访问接口 | 已覆盖 | `test_get_current_user_profile_with_invalid_token` |
| 74 | token过期访问接口 | 已覆盖 | `test_get_current_user_profile_with_expired_token` |
| 75 | 用户权限缓存失效 | 待补充 | 当前按数据库实时查询，不依赖缓存 |
| 76 | 用户权限更新即时生效 | 已覆盖 | 当前授权摘要与角色权限分配后实时生效 |

## 当前重点自动化用例

- [test_login.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/api/routes/test_login.py)
- [test_employee.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/api/routes/test_employee.py)
- [test_org_iam.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/api/routes/test_org_iam.py)
- [test_employee_onboarding_flow.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/scenarios/test_employee_onboarding_flow.py)
- [test_current_store_context_flow.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/scenarios/test_current_store_context_flow.py)
- [test_employee_rehire_flow.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/scenarios/test_employee_rehire_flow.py)
- [test_multi_role_scope_union_flow.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/scenarios/test_multi_role_scope_union_flow.py)
- [test_org_inheritance_flow.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/scenarios/test_org_inheritance_flow.py)
- [test_store_employee_permission_flow.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/scenarios/test_store_employee_permission_flow.py)
- [test_user_to_employee_transfer_flow.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/scenarios/test_user_to_employee_transfer_flow.py)
- [test_employee_position_change_flow.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/scenarios/test_employee_position_change_flow.py)
- [test_store_org_maintenance_flow.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/scenarios/test_store_org_maintenance_flow.py)
- [test_store_org_deletion_boundary_flow.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/tests/scenarios/test_store_org_deletion_boundary_flow.py)

## 建议的下一批优先补测

1. 手机号解绑
2. 小程序账号解绑与重绑
3. 用户权限缓存失效
4. 更复杂的组织树调整
5. 更复杂的门店归档/恢复
