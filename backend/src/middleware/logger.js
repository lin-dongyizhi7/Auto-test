/**
 * 日志中间件
 */

const logger = require('../utils/logger');

// 请求日志记录
const requestLogger = (req, res, next) => {
  const start = Date.now();
  
  // 响应完成后记录日志
  res.on('finish', () => {
    const duration = Date.now() - start;
    const logData = {
      method: req.method,
      url: req.originalUrl,
      status: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      contentLength: res.get('Content-Length') || 0
    };

    if (res.statusCode >= 400) {
      logger.warn('请求处理', logData);
    } else {
      logger.info('请求处理', logData);
    }
  });

  next();
};

module.exports = {
  requestLogger
};
