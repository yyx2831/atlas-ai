"""应用配置：集中管理 FastAPI 实例的元数据。

原本这些 title/description/version 直接写死在 main.py 里，现抽离到此处，
便于按环境统一管理，main.py 只负责装配。
"""
TITLE = "Atlas AI API"
DESCRIPTION = "模块化架构接口文档"
VERSION = "1.0.0"
