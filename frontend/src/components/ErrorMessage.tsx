import { APIError } from '@/lib/api-error';

export function ErrorMessage({ error }: { error: APIError | Error | string }) {
  const getMessage = () => {
    if (typeof error === 'string') return error;
    if (error instanceof APIError) {
      if (error.isNetworkError()) {
        return '网络连接失败，请检查后端服务是否启动';
      }
      return error.detail || error.message;
    }
    return error.message;
  };

  const getAction = () => {
    if (error instanceof APIError && error.isNetworkError()) {
      return (
        <a
          href="http://127.0.0.1:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-[var(--accent-primary)] hover:underline"
        >
          打开 API 文档检查
        </a>
      );
    }
    return null;
  };

  return (
    <div className="rounded-xl border border-[color:var(--error-light)] bg-[var(--error-light)] p-4">
      <div className="flex items-start gap-3">
        <div className="text-xl">⚠️</div>
        <div className="flex-1">
          <div className="text-sm font-medium text-[var(--error)]">
            {getMessage()}
          </div>
          {getAction() && (
            <div className="mt-2">{getAction()}</div>
          )}
        </div>
      </div>
    </div>
  );
}
