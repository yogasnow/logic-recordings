/** Editable educational MIDI arrangement. Node.js 24+; no packages required. */
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

type Note = { start: number; duration: number; pitch: number; velocity: number; voice: string };
type Score = {
  title: string;
  timeUnit: 'seconds' | 'beats';
  tempoBpm?: number;
  notes?: Note[];
  eventsFile?: string;
};
type SourceEvent = [number, number, number, number, number, string, number];

const [, , input, output = 'arrangement.mid', preset = 'piano'] = process.argv;
if (!input || !['piano', 'strings'].includes(preset)) {
  console.error('Usage: node music-code/arrange.ts <score.json> <output.mid> [piano|strings]');
  process.exit(1);
}
const inputPath = resolve(input);
const score = JSON.parse(readFileSync(inputPath, 'utf8')) as Score;
let notes: Note[];
if (score.eventsFile) {
  const events = JSON.parse(readFileSync(resolve(dirname(inputPath), score.eventsFile), 'utf8')) as SourceEvent[];
  notes = events.map(([, start, pitch, duration, amplitude, voice]) => ({
    start, duration, pitch, voice,
    velocity: Math.max(1, Math.min(127, Math.round(22 + amplitude * 300))),
  })).filter(note => note.duration > 0 && note.velocity > 22);
} else {
  notes = score.notes ?? [];
}
if (!notes.length) {
  console.error(`No verified note events in ${inputPath}. Add notes from MIDI or a score; an MP3 alone is not a note transcription.`);
  process.exit(2);
}
const bpm = score.timeUnit === 'seconds' ? 120 : score.tempoBpm;
if (!bpm || bpm <= 0) throw new Error('A positive tempoBpm is required for beat-based scores.');
const ppq = 480;
const toTicks = (value: number) => Math.round(value * (score.timeUnit === 'seconds' ? bpm / 60 : 1) * ppq);
const bytes = (...values: number[]) => Buffer.from(values);
const variable = (n: number): number[] => {
  if (n < 0 || !Number.isFinite(n)) throw new Error('Invalid MIDI delta time');
  const parts = [n & 0x7f];
  while ((n >>= 7)) parts.unshift((n & 0x7f) | 0x80);
  return parts;
};
const chunk = (tag: string, data: Buffer) => {
  const length = Buffer.alloc(4); length.writeUInt32BE(data.length);
  return Buffer.concat([Buffer.from(tag), length, data]);
};
const names = [...new Set(notes.map(note => note.voice))].sort();
if (names.length > 16) throw new Error('Too many voices for a simple MIDI arrangement.');
const programs: Record<string, number> = preset === 'strings'
  ? { bell: 48, pad: 48, harp: 48, flute: 73, finger: 42, sub: 38 }
  : { bell: 8, pad: 89, harp: 46, flute: 73, finger: 32, sub: 38 };
const drums = new Set(['kick', 'snare', 'hat', 'udu', 'click']);
const channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15];
let melodicIndex = 0;
const tracks: Buffer[] = [];
const tempo = Math.round(60_000_000 / bpm);
tracks.push(chunk('MTrk', bytes(0, 0xff, 0x51, 3, (tempo >> 16) & 255, (tempo >> 8) & 255, tempo & 255, 0, 0xff, 0x2f, 0)));
for (const name of names) {
  const drum = drums.has(name);
  const channel = drum ? 9 : channels[melodicIndex++];
  if (channel === undefined) throw new Error('No free MIDI channel');
  const messages: { tick: number; order: number; data: Buffer }[] = [];
  if (!drum) messages.push({ tick: 0, order: 0, data: bytes(0xc0 | channel, programs[name] ?? 0) });
  for (const note of notes.filter(note => note.voice === name)) {
    if (![note.start, note.duration, note.pitch, note.velocity].every(Number.isFinite) || note.pitch < 0 || note.pitch > 127 || note.duration <= 0) throw new Error(`Invalid note in ${name}`);
    const start = toTicks(note.start);
    const end = Math.max(start + 1, toTicks(note.start + note.duration));
    const pitch = Math.round(note.pitch);
    const velocity = Math.max(1, Math.min(127, Math.round(note.velocity)));
    messages.push({ tick: start, order: 2, data: bytes(0x90 | channel, pitch, velocity) });
    messages.push({ tick: end, order: 1, data: bytes(0x80 | channel, pitch, 0) });
  }
  messages.sort((a, b) => a.tick - b.tick || a.order - b.order);
  const parts: Buffer[] = [];
  let previous = 0;
  for (const message of messages) {
    parts.push(bytes(...variable(message.tick - previous)), message.data);
    previous = message.tick;
  }
  parts.push(bytes(0, 0xff, 0x2f, 0));
  tracks.push(chunk('MTrk', Buffer.concat(parts)));
}
const header = bytes(0, 1, (tracks.length >> 8) & 255, tracks.length & 255, (ppq >> 8) & 255, ppq & 255);
writeFileSync(resolve(output), Buffer.concat([chunk('MThd', header), ...tracks]));
console.log(`${score.title}: ${notes.length} notes, ${names.length} voices → ${output} (${preset})`);
