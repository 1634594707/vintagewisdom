export class APIError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public detail: string,
    public url: string
  ) {
    super(`API ${status} ${statusText}: ${detail}`);
    this.name = 'APIError';
  }

  static async fromResponse(response: Response): Promise<APIError> {
    let detail = '';
    try {
      const data = await response.json();
      detail = data.detail || data.message || '';
    } catch {
      detail = await response.text().catch(() => '');
    }
    
    return new APIError(
      response.status,
      response.statusText,
      detail,
      response.url
    );
  }

  isNetworkError(): boolean {
    return this.status === 0 || this.status >= 500;
  }

  isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  isNotFound(): boolean {
    return this.status === 404;
  }

  isUnauthorized(): boolean {
    return this.status === 401;
  }
}
