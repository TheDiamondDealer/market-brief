'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..', '..');
const slices = new Map();
const evidence = {
  updated: '14 July 2026',
  eventReactions: [
    {
      id: 'exact', event: 'Exact event', scheduled: '14 July 2026 · 10:30 pm Melbourne', stage: 'Pre-event', source: 'Official agency',
      previous: 'Research verification required', consensus: 'Not sourced from an official free feed', actual: 'Pending',
      scenarios: [['Upside', 'Gold and USD are named in the supplied scenario.']],
      reactions: { immediate: 'Pending', close: 'Pending', day1: 'Pending', day5: 'Pending' }, verdict: 'Too early'
    },
    {
      id: 'approximate', event: 'Approximate event', scheduled: 'Mid-July 2026 · Melbourne time to verify', stage: 'Pre-event', source: 'Official agency',
      previous: '1.0', consensus: 'Not sourced', actual: '2.0', scenarios: [],
      reactions: { immediate: 'Observed move', close: 'Observed close', day1: 'Observed day one', day5: 'Observed day five' }, verdict: 'Complete'
    }
  ]
};
const windowObject = {
  marketResearchData: evidence,
  MarketBriefCore: {
    adapters: { evidence: () => evidence },
    store: { getSlice: (name) => slices.get(name), setSlice: (name, value) => slices.set(name, value) }
  }
};
windowObject.window = windowObject;
const context = vm.createContext({ console, window: windowObject });
vm.runInContext(fs.readFileSync(path.join(root, 'site/features/calendar/calendar-data.js'), 'utf8'), context, { filename: 'calendar-data.js' });

const data = windowObject.marketCalendarData;
assert.equal(data.schemaVersion, 1);
assert.equal(data.timezone, 'Australia/Melbourne');
assert.equal(data.events[0].scheduledAt, '2026-07-14T22:30:00+10:00');
assert.equal(data.events[0].timeStatus, 'verified-melbourne');
assert.equal(data.events[0].consensus.status, 'not-sourced');
assert.equal(data.events[0].actual.status, 'pending');
assert.equal(data.events[0].state, 'upcoming');
assert.equal(data.events[1].scheduledAt, null);
assert.equal(data.events[1].timeStatus, 'needs-verification');
assert.equal(data.events[1].state, 'reaction-complete');
assert.equal(data.events[1].consensus.status, 'not-sourced');
assert.equal(slices.get('calendar'), data);
console.log('BR-15 calendar adapter tests passed');
