"""Запуск HTTP API: uvicorn run_web_api:app или python -m uvicorn run_web_api:app --host 0.0.0.0 --port 8090"""

import uvicorn

from web_api.app import app

__all__ = ['app']

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8090)
