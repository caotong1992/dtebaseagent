# Checklist

## start.bat 重启参数验证
- [x] start.bat 支持 --restart 参数
- [x] start.bat 支持 -r 参数（简写）
- [x] 正常启动时检测同一进程并跳过
- [x] 强制重启时停止现有进程
- [x] 支持端口参数组合（如 9090 --restart）

## start.sh 重启参数验证
- [x] start.sh 支持 --restart 参数
- [x] start.sh 支持 -r 参数（简写）
- [x] 强制重启时正确停止进程
- [x] 支持端口参数组合