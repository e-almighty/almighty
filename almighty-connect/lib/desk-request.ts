// Use AbortController rather than AbortSignal.timeout, including on older iPads.
export async function deskRequest<T>(url: string, options: RequestInit = {}, timeout = 10000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, {...options, cache: 'no-store', signal: controller.signal});
    if (response.status === 401 || response.status === 403) throw new Error('受付への接続が切れました。この画面を再読み込みし、同じChatGPTアカウントでログインしてください。');
    if (!response.headers.get('content-type')?.includes('application/json')) throw new Error('受付に接続できません。この画面を再読み込みしてください。');
    const data = await response.json() as {error?: string};
    if (!response.ok) throw new Error(data.error || '送信できませんでした。もう一度お試しください。');
    return data as T;
  } catch (error) {
    if (controller.signal.aborted) throw new Error('通信が遅れています。接続を自動で確認しています。');
    throw error;
  } finally { clearTimeout(timer); }
}
