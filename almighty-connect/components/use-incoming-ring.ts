'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Ringer } from '@/lib/ringer';
import { resumeAudio } from '@/lib/audio-unlock';

export function useIncomingRing(incoming: boolean, initialAudio: AudioContext | null = null) {
  const audio = useRef<AudioContext | null>(initialAudio);
  const ringer = useRef<Ringer | null>(initialAudio ? new Ringer(initialAudio) : null);
  const [audioReady, setAudioReady] = useState(false);
  const [visible, setVisible] = useState(true);
  const arm = useCallback(async () => {
    if (!audio.current || audio.current.state === 'closed') {
      const Audio = window.AudioContext || (window as any).webkitAudioContext;
      if (!Audio) throw new Error('このブラウザでは着信音を利用できません。');
      const context: AudioContext = new Audio();
      audio.current = context;
      ringer.current = new Ringer(context);
      context.onstatechange = () => setAudioReady(context.state === 'running');
    }
    await resumeAudio(audio.current);
    setAudioReady(audio.current.state === 'running');
    if (audio.current.state !== 'running') throw new Error('音を有効にできませんでした');
  }, []);
  useEffect(() => {
    const changed = () => setVisible(document.visibilityState === 'visible');
    changed();
    document.addEventListener('visibilitychange', changed);
    return () => document.removeEventListener('visibilitychange', changed);
  }, []);
  useEffect(() => {
    if (incoming && audioReady && visible) ringer.current?.start();
    else ringer.current?.stop();
    return () => ringer.current?.stop();
  }, [incoming, audioReady, visible]);
  useEffect(() => () => {
    ringer.current?.stop();
    if (audio.current) { audio.current.onstatechange = null; void audio.current.close(); }
  }, []);
  return { audioReady, visible, arm, test: async () => { await arm(); ringer.current?.pulse(); } };
}
