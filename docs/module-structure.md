# 模块化目录约定

后端按业务模块组织代码，不再继续把新增能力堆到全局 `models.py`、`routes.py`、`crud.py`。

## 1. 当前约定

每个模块单独建目录，目录内至少包含：

- `models.py`：本模块数据模型
- `service.py`：本模块业务逻辑
- `router.py`：本模块接口入口

当前已经落地的模块：

- [auth](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/app/modules/auth)
- [employee](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/app/modules/employee)
- [miniapp](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/app/modules/miniapp)
- [store](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/app/modules/store)
- [org](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/app/modules/org)
- [iam](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/app/modules/iam)

## 2. 导入约定

- 对外统一通过 [app.models](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/app/models/__init__.py) 暴露模型聚合导出，兼容现有代码
- 模块内部逻辑优先放到各自 `service.py`
- API 路由统一在 [api/main.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/app/api/main.py) 注册

## 3. 后续新增模块要求

后续新增 `member`、`wallet`、`inventory`、`finance` 等模块时，继续沿用：

```text
app/modules/<module_name>/
  models.py
  service.py
  router.py
```

如果模块继续变大，再在模块目录内细分：

- `schemas.py`
- `repository.py`
- `service/`
- `router/`

例如当前 `auth` 模块已经采用：

```text
app/modules/auth/
  router.py
  service.py
```

## 4. 当前不再推荐的方式

不再继续新增：

- 全局业务模型堆在单个文件
- 全局业务路由堆在单个目录平铺文件
- 跨模块逻辑都塞进统一 `crud.py`
