## feshttp Changelog

###[1.0.1b2] - 2020-9-18

#### Changed
- 更改同步http初始化的时机,改为调用后即初始化

###[1.0.1b1] - 2020-3-2

#### Added
- 整体重构
- 增加jrpc客户端单个方法请求的功能,调用形式和普通的函数调用形式一致
- 增加jrpc客户端批量方法请求的功能,调用形式类似链式调用
- 增加jrpc服务端jsonrpc子类, http和websocket的URL固定和client中的一致
- 拆分aclients库和eclients中的请求和RPC功能到此库中
- 增加默认使用simplejson的功能
- 同步和异步均增加对时间的序列化功能,和flask中的时间序列化一致

#### Changed 
- 优化所有代码中没有类型标注的地方,都改为typing中的类型标注
- SanicJsonRPC类中增加init_app方法保证和其他sanic扩展的初始化和调用方式一致
- jrpc client 和 jrpc server增加jrpc router的修改入口
- 更改jsonrpc三方包中queue没有使用同一个loop而造成的错误
