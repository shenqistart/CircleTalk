# Knowledge 知识库

> 版本: v1.0

`packages/knowledge` 提供知识库领域模型、数据访问和检索 DTO，供业务服务组合使用。

## 模块总览

| 模块 | 职责 | 关键导出 |
|------|------|----------|
| `model` | 领域模型（5 个聚合根） | `Knowledge`, `KnowledgeBase`, `KnowledgeChunk`, `KnowledgeSection`, `KnowledgeFolder` |
| `repository` | 数据访问层 | 5 个 Repository（每个聚合根对应一个） |
| `schema` | 检索 DTO | `RetrievedChunk`, `KnowledgeCitation` |
| `exceptions` | 细粒度业务异常 | `KnowledgeError` 层次结构（8 个子类） |
| `knowledge_config` | 模块配置 | `KnowledgeConfig`, `ChunkingConfig` |

## 目录结构

```
packages/knowledge/src/knowledge/
├── model/
│   ├── knowledge_base.py   # 知识库容器
│   ├── knowledge.py        # 文档（支持版本追踪）
│   ├── chunk.py            # 可检索的知识片段
│   ├── section.py          # 文档逻辑结构/目录树
│   ├── folder.py           # 文件夹树形组织
│   └── batch_operation.py  # 批量操作
├── repository/
│   ├── knowledge_base_repository.py
│   ├── knowledge_repository.py
│   ├── chunk_repository.py
│   ├── section_repository.py
│   └── folder_repository.py
├── schema/
│   ├── retrieval.py        # RetrievedChunk, KnowledgeCitation
│   └── speech.py           # 语音相关 Schema
├── exceptions.py           # KnowledgeError 层次结构
└── knowledge_config.py     # ChunkingConfig, StorageConfig
```

## 领域模型

```
KnowledgeBase (知识库)
├── KnowledgeFolder (文件夹，树形结构)
└── Knowledge (文档)
    ├── KnowledgeSection (章节/目录，树形结构)
    └── KnowledgeChunk (知识片段，关联 Section 获取上下文)
```

- **Knowledge** 支持版本追踪（`version` + `parent_id` 实现更新历史）
- **KnowledgeSection** 通过 `parent_section_id` 形成目录树
- **KnowledgeChunk** 关联 Section，检索时可回溯上下文

## 异常体系

| 异常 | HTTP 状态码 | 场景 |
|------|------------|------|
| `KnowledgeNotFoundError` | 404 | 文档/知识库不存在 |
| `KnowledgeAccessDeniedError` | 403 | 无访问权限 |
| `FileParsingError` | 400 | 文件解析失败 |
| `ChunkingError` | 500 | 分片处理异常 |
| `StorageError` | 500 | 对象存储异常 |
| `VectorSearchError` | 500 | 向量检索异常 |
| `KnowledgeMetadataError` | 400 | 元数据校验失败 |
| `VersionManagementError` | 400 | 版本管理异常 |
