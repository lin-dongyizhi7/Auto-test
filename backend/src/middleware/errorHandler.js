/**
 * 错误处理中间件
 */

const logger = require('../utils/logger');

// 404错误处理
const notFound = (req, res, next) => {
  const error = new Error(`未找到路径: ${req.originalUrl}`);
  error.status = 404;
  next(error);
};

// 全局错误处理
const errorHandler = (err, req, res, next) => {
  const status = err.status || 500;
  const message = err.message || '服务器内部错误';
  
  // 记录错误日志
  logger.error('请求错误', {
    method: req.method,
    url: req.originalUrl,
    status,
    message,
    stack: err.stack,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });

  // 开发环境返回详细错误信息
  const errorResponse = {
    success: false,
    error: message,
    timestamp: new Date().toISOString()
  };

  if (process.env.NODE_ENV === 'development') {
    errorResponse.stack = err.stack;
    errorResponse.details = err;
  }

  res.status(status).json(errorResponse);
};

module.exports = {
  notFound,
  errorHandler
};
