const DAY_MS = 24 * 60 * 60 * 1000;

/** Buckets events into "This weekend" / "Next week" / "Later", for the list view. */
export function groupEventsByBucket(events) {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const dayOfWeek = now.getDay(); // 0 = Sunday ... 6 = Saturday
  const daysUntilSaturday = (6 - dayOfWeek) % 7;
  const weekendStart = new Date(startOfToday.getTime() + daysUntilSaturday * DAY_MS);
  const weekendEnd = new Date(weekendStart.getTime() + 2 * DAY_MS); // Sat + Sun
  const nextWeekEnd = new Date(startOfToday.getTime() + 7 * DAY_MS);

  const buckets = { "This weekend": [], "Next week": [], Later: [] };
  for (const event of events) {
    const start = new Date(event.start);
    if (start >= weekendStart && start < weekendEnd) {
      buckets["This weekend"].push(event);
    } else if (start < nextWeekEnd) {
      buckets["Next week"].push(event);
    } else {
      buckets.Later.push(event);
    }
  }
  return buckets;
}

export function formatEventDateTime(isoString) {
  const date = new Date(isoString);
  return date.toLocaleString("en-ZA", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}
