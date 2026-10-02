export async function resumeAudio(context: AudioContext, timeout = 2000) {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    await Promise.race([
      context.resume(),
      new Promise<never>((_, reject) => { timer = setTimeout(() => reject(new Error('着信音の準備が完了しませんでした。')), timeout); }),
    ]);
    if (context.state !== 'running') throw new Error('着信音を有効にできませんでした。');
  } finally { clearTimeout(timer); }
}
