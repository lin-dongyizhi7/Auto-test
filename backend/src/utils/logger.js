/**
 * 日志工具类
 * 基于 winston 的日志记录器
 */

const winston = require('winston');
const path = require('path');
const config = require('../config');

// 创建日志目录
const logDir = path.join(__dirname, '../../logs');

// 定义日志格式
const logFormat = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss'
  }),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

// 控制台格式
const consoleFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({
    format: 'HH:mm:ss'
  }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    let msg = `${timestamp} [${level}]: ${message}`;
    if (Object.keys(meta).length > 0) {
      msg += ` ${JSON.stringify(meta)}`;
    }
    return msg;
  })
);

// 创建 logger 实例
const logger = winston.createLogger({
  level: config.logging.level || 'info',
  format: logFormat,
  defaultMeta: { service: 'auto-test-backend' },
  transports: [
    // 错误日志文件
    new winston.transports.File({
      filename: path.join(logDir, 'error.log'),
      level: 'error',
      maxsize: config.logging.maxFileSize || 5242880, // 5MB
      maxFiles: config.logging.maxFiles || 5
    }),
    
    // 所有日志文件
    new winston.transports.File({
      filename: path.join(logDir, 'combined.log'),
      maxsize: config.logging.maxFileSize || 5242880, // 5MB
      maxFiles: config.logging.maxFiles || 5
    })
  ]
});

// 在开发环境下添加控制台输出
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: consoleFormat
  }));
}

// 添加日志级别方法
const logLevels = ['error', 'warn', 'info', 'verbose', 'debug', 'silly'];

logLevels.forEach(level => {
  if (!logger[level]) {
    logger[level] = (message, meta = {}) => {
      logger.log(level, message, meta);
    };
  }
});

// 添加便捷方法
logger.startup = (message, meta = {}) => {
  logger.info(`🚀 ${message}`, meta);
};

logger.shutdown = (message, meta = {}) => {
  logger.info(`🛑 ${message}`, meta);
};

logger.request = (message, meta = {}) => {
  logger.info(`📡 ${message}`, meta);
};

logger.response = (message, meta = {}) => {
  logger.info(`📤 ${message}`, meta);
};

logger.database = (message, meta = {}) => {
  logger.info(`💾 ${message}`, meta);
};

logger.security = (message, meta = {}) => {
  logger.warn(`🔒 ${message}`, meta);
};

logger.performance = (message, meta = {}) => {
  logger.info(`⚡ ${message}`, meta);
};

// 处理未捕获的异常
logger.exceptions.handle(
  new winston.transports.File({
    filename: path.join(logDir, 'exceptions.log')
  })
);

// 处理未处理的 Promise 拒绝
logger.rejections.handle(
  new winston.transports.File({
    filename: path.join(logDir, 'rejections.log')
  })
);

module.exports = logger;
