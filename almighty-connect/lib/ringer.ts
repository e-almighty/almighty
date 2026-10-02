// A short two-note ringtone. stop() also cancels a tone already playing.
export class Ringer {
  private timer: ReturnType<typeof setInterval> | null = null;
  private nodes = new Set<OscillatorNode>();
  private context: AudioContext;
  constructor(context: AudioContext) { this.context = context; }
  pulse() {
    if (this.context.state !== 'running') return;
    const oscillator = this.context.createOscillator();
    const gain = this.context.createGain();
    const start = this.context.currentTime;
    oscillator.frequency.setValueAtTime(660, start);
    oscillator.frequency.setValueAtTime(880, start + 0.22);
    gain.gain.setValueAtTime(0.1, start);
    gain.gain.exponentialRampToValueAtTime(0.001, start + 0.8);
    oscillator.connect(gain);
    gain.connect(this.context.destination);
    this.nodes.add(oscillator);
    oscillator.onended = () => {
      this.nodes.delete(oscillator);
      oscillator.disconnect();
      gain.disconnect();
    };
    oscillator.start();
    oscillator.stop(start + 0.8);
  }
  start() {
    if (this.timer !== null) return;
    this.pulse();
    this.timer = setInterval(() => this.pulse(), 4000);
  }
  stop() {
    if (this.timer !== null) clearInterval(this.timer);
    this.timer = null;
    for (const node of this.nodes) {
      try { node.stop(); } catch { /* A completed tone is already silent. */ }
    }
    this.nodes.clear();
  }
}
