function updateClock() {
  const clock = document.getElementById('clock');
  if (!clock) return;
  const now = new Date().toLocaleString('en-US', { timeZone: 'America/Argentina/Buenos_Aires', hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  clock.textContent = now;
}
setInterval(updateClock, 1000);
updateClock();
