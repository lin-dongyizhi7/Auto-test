/**
 * 配置文件
 */

require('dotenv').config();

const config = {
  // 服务器配置
  server: {
    port: process.env.PORT || 8080,
    host: process.env.HOST || '0.0.0.0',
    env: process.env.NODE_ENV || 'development'
  },

  // 测试服务器配置
  testServer: {
    defaultHost: process.env.TEST_SERVER_HOST || '0.0.0.0',
    defaultPort: parseInt(process.env.TEST_SERVER_PORT) || 8888,
    retryInterval: parseInt(process.env.TEST_SERVER_RETRY_INTERVAL) || 3000,
    timeout: parseInt(process.env.TEST_SERVER_TIMEOUT) || 10000
  },

  // 数据库配置
  database: {
    scriptStorageFile: process.env.SCRIPT_STORAGE_FILE || './data/scripts_storage.json',
    scriptCounterFile: process.env.SCRIPT_COUNTER_FILE || './data/script_counter.json',
    backupDir: process.env.BACKUP_DIR || './data/backup'
  },

  // 脚本配置
  script: {
    maxSize: parseInt(process.env.SCRIPT_MAX_SIZE) || 1024 * 1024, // 1MB
    timeout: parseInt(process.env.SCRIPT_TIMEOUT) || 30000, // 30秒
    allowedExtensions: process.env.SCRIPT_ALLOWED_EXTENSIONS?.split(',') || ['.py', '.js', '.ts']
  },

  // 安全配置
  security: {
    allowedOrigins: process.env.ALLOWED_ORIGINS?.split(',') || [
      'http://localhost:3000',
      'http://localhost:8080',
      'http://127.0.0.1:3000',
      'http://127.0.0.1:8080'
    ],
    corsCredentials: process.env.CORS_CREDENTIALS === 'true',
    rateLimit: {
      windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15分钟
      max: parseInt(process.env.RATE_LIMIT_MAX) || 100 // 限制每个IP 15分钟内最多100个请求
    }
  },

  // 日志配置
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: process.env.LOG_FORMAT || 'combined',
    file: process.env.LOG_FILE || './logs/app.log',
    maxSize: process.env.LOG_MAX_SIZE || '10m',
    maxFiles: process.env.LOG_MAX_FILES || '5'
  },

  // 文件上传配置
  upload: {
    maxFileSize: parseInt(process.env.MAX_FILE_SIZE) || 10 * 1024 * 1024, // 10MB
    allowedMimeTypes: process.env.ALLOWED_MIME_TYPES?.split(',') || [
      'text/plain',
      'text/x-python',
      'application/javascript',
      'application/typescript'
    ]
  }
};

module.exports = config;
