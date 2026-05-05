module.exports = {
  apps: [
    {
      name: 'japan-dict-tool',
      script: './venv/bin/python',
      args: '-m uvicorn app:app --host 127.0.0.1 --port 8000',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production'
      },
      error_file: 'logs/error.log',
      out_file: 'logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      watch: false,
      ignore_watch: ['node_modules', 'venv', 'db', 'logs'],
      max_memory_restart: '500M',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s'
    }
  ],
  deploy: {
    production: {
      user: process.env.DEPLOY_USER || 'ubuntu',
      host: process.env.DEPLOY_HOST || 'your-server.com',
      key: process.env.DEPLOY_KEY || '~/.ssh/id_rsa',
      ref: 'origin/main',
      repo: 'https://github.com/thomas-chu123/Kanji_trans_tool.git',
      path: '/var/www/japan_dict_tool',
      'post-deploy': 'bash setup.sh && pm2 startOrRestart ecosystem.config.js --env production'
    }
  }
};
