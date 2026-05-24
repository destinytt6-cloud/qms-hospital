"""入口文件：启动 QMS 服务"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",   # 监听所有网卡，局域网可访问
        port=8000,
        reload=True,       # 开发模式，代码修改自动重启
        reload_dirs=["./app"],  # 只监控 app 目录
    )
